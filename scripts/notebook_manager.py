#!/usr/bin/env python3
"""
Notebook Library Management for NotebookLM
Manages a library of NotebookLM notebooks with metadata
Based on the MCP server implementation
"""

import json
import argparse
import uuid
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


def _extract_id_from_url(url: str) -> Optional[str]:
    """Extract notebook UUID from NotebookLM URL"""
    match = re.search(r'/notebook/([a-f0-9-]+)', url)
    if match:
        return match.group(1)
    return None


def fetch_notebook_metadata(url: str, profile_id=None, headless: bool = True) -> Dict[str, Any]:
    """
    Navigate to a NotebookLM notebook and extract real metadata.

    Returns:
        Dict with 'title' (str or None) and 'sources' (list of source name strings)
    """
    from patchright.sync_api import sync_playwright
    from browser_utils import BrowserFactory
    from auth_manager import AuthManager
    from config import QUERY_INPUT_SELECTORS

    auth = AuthManager(profile_id=profile_id)

    if not auth.is_authenticated():
        print("Warning: Not authenticated. Cannot fetch metadata.")
        return {'title': None, 'sources': []}

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(
            playwright,
            headless=headless,
            user_data_dir=str(auth.browser_profile_dir),
            state_file=auth.state_file,
        )
        page = context.new_page()

        print("  Fetching notebook metadata...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Check accessibility
        is_ready = False
        for sel in QUERY_INPUT_SELECTORS:
            try:
                if page.is_visible(sel):
                    is_ready = True
                    break
            except Exception:
                continue

        if not is_ready:
            print("  Warning: Notebook may not be accessible")

        # Extract title from page title
        raw_title = page.title()
        title = None
        if raw_title:
            if " - NotebookLM" in raw_title:
                title = raw_title.rsplit(" - NotebookLM", 1)[0].strip()
            elif raw_title not in ("NotebookLM", ""):
                title = raw_title.strip()

        # Extract source names from the sources panel
        sources = []
        source_selectors = [
            '.source-item .source-title',
            '.source-item-title',
            '.source-list-item .title',
            'source-item .title-text',
            '[data-source-title]',
            '.notebook-source .title',
        ]

        for sel in source_selectors:
            try:
                elements = page.query_selector_all(sel)
                if elements:
                    for el in elements:
                        text = el.inner_text().strip()
                        if text and text not in sources:
                            sources.append(text)
                    if sources:
                        break
            except Exception:
                continue

        print(f"  Title: {title or '(not found)'}")
        if sources:
            print(f"  Sources ({len(sources)}): {', '.join(sources[:5])}")
        else:
            print("  Sources: (none extracted)")

        return {'title': title, 'sources': sources}

    except Exception as e:
        print(f"  Error fetching metadata: {e}")
        return {'title': None, 'sources': []}

    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


class NotebookLibrary:
    """Manages a collection of NotebookLM notebooks with metadata"""

    def __init__(self, profile_id: Optional[str] = None):
        """Initialize the notebook library.

        Args:
            profile_id: Profile to load library for. None = active profile.
        """
        from profile_manager import ProfileManager
        pm = ProfileManager()
        if profile_id:
            paths = pm.get_paths(profile_id)
        else:
            paths = pm.get_active_paths()
        self.data_dir = paths["profile_dir"]
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.library_file = paths["library_file"]
        self.notebooks: Dict[str, Dict[str, Any]] = {}
        self.active_notebook_id: Optional[str] = None

        # Load existing library
        self._load_library()

    def _load_library(self):
        """Load library from disk"""
        if self.library_file.exists():
            try:
                with open(self.library_file, 'r') as f:
                    data = json.load(f)
                    self.notebooks = data.get('notebooks', {})
                    self.active_notebook_id = data.get('active_notebook_id')
                    print(f"Loaded library with {len(self.notebooks)} notebooks")
            except Exception as e:
                print(f"Warning: Error loading library: {e}")
                self.notebooks = {}
                self.active_notebook_id = None
        else:
            self._save_library()

    def _save_library(self):
        """Save library to disk"""
        try:
            data = {
                'notebooks': self.notebooks,
                'active_notebook_id': self.active_notebook_id,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.library_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library: {e}")

    def add_notebook(
        self,
        url: str,
        name: str,
        description: str,
        topics: List[str],
        content_types: Optional[List[str]] = None,
        use_cases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add a new notebook to the library

        Args:
            url: NotebookLM notebook URL
            name: Display name for the notebook
            description: What's in this notebook
            topics: Topics covered
            content_types: Types of content (optional)
            use_cases: When to use this notebook (optional)
            tags: Additional tags for organization (optional)

        Returns:
            The created notebook object
        """
        # Use UUID from URL as ID, fallback to slugified name
        notebook_id = _extract_id_from_url(url) or name.lower().replace(' ', '-').replace('_', '-')

        # Check for duplicates
        if notebook_id in self.notebooks:
            raise ValueError(f"Notebook with ID '{notebook_id}' already exists")

        # Create notebook object
        notebook = {
            'id': notebook_id,
            'url': url,
            'name': name,
            'description': description,
            'topics': topics,
            'content_types': content_types or [],
            'use_cases': use_cases or [],
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'use_count': 0,
            'last_used': None
        }

        # Add to library
        self.notebooks[notebook_id] = notebook

        # Set as active if it's the first notebook
        if len(self.notebooks) == 1:
            self.active_notebook_id = notebook_id

        self._save_library()

        print(f"Added notebook: {name} ({notebook_id})")
        return notebook

    def remove_notebook(self, notebook_id: str) -> bool:
        """
        Remove a notebook from the library

        Args:
            notebook_id: ID of notebook to remove

        Returns:
            True if removed, False if not found
        """
        if notebook_id in self.notebooks:
            del self.notebooks[notebook_id]

            # Clear active if it was removed
            if self.active_notebook_id == notebook_id:
                self.active_notebook_id = None
                # Set new active if there are other notebooks
                if self.notebooks:
                    self.active_notebook_id = list(self.notebooks.keys())[0]

            self._save_library()
            print(f"Removed notebook: {notebook_id}")
            return True

        print(f"Warning: Notebook not found: {notebook_id}")
        return False

    def update_notebook(
        self,
        notebook_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        use_cases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update notebook metadata

        Args:
            notebook_id: ID of notebook to update
            Other args: Fields to update (None = keep existing)

        Returns:
            Updated notebook object
        """
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        notebook = self.notebooks[notebook_id]

        # Update fields if provided
        if name is not None:
            notebook['name'] = name
        if description is not None:
            notebook['description'] = description
        if topics is not None:
            notebook['topics'] = topics
        if content_types is not None:
            notebook['content_types'] = content_types
        if use_cases is not None:
            notebook['use_cases'] = use_cases
        if tags is not None:
            notebook['tags'] = tags
        if url is not None:
            notebook['url'] = url

        notebook['updated_at'] = datetime.now().isoformat()

        self._save_library()
        print(f"Updated notebook: {notebook['name']}")
        return notebook

    def get_notebook(self, notebook_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific notebook by ID"""
        return self.notebooks.get(notebook_id)

    def list_notebooks(self) -> List[Dict[str, Any]]:
        """List all notebooks in the library"""
        return list(self.notebooks.values())

    def search_notebooks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search notebooks by query

        Args:
            query: Search query (searches name, description, topics, tags)

        Returns:
            List of matching notebooks
        """
        query_lower = query.lower()
        results = []

        for notebook in self.notebooks.values():
            # Search in various fields
            searchable = [
                notebook['name'].lower(),
                notebook['description'].lower(),
                ' '.join(notebook['topics']).lower(),
                ' '.join(notebook['tags']).lower(),
                ' '.join(notebook.get('use_cases', [])).lower()
            ]

            if any(query_lower in field for field in searchable):
                results.append(notebook)

        return results

    def select_notebook(self, notebook_id: str) -> Dict[str, Any]:
        """
        Set a notebook as active

        Args:
            notebook_id: ID of notebook to activate

        Returns:
            The activated notebook
        """
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        self.active_notebook_id = notebook_id
        self._save_library()

        notebook = self.notebooks[notebook_id]
        print(f"Activated notebook: {notebook['name']}")
        return notebook

    def get_active_notebook(self) -> Optional[Dict[str, Any]]:
        """Get the currently active notebook"""
        if self.active_notebook_id:
            return self.notebooks.get(self.active_notebook_id)
        return None

    def increment_use_count(self, notebook_id: str) -> Dict[str, Any]:
        """
        Increment usage counter for a notebook

        Args:
            notebook_id: ID of notebook that was used

        Returns:
            Updated notebook
        """
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        notebook = self.notebooks[notebook_id]
        notebook['use_count'] += 1
        notebook['last_used'] = datetime.now().isoformat()

        self._save_library()
        return notebook

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        total_notebooks = len(self.notebooks)
        total_topics = set()
        total_use_count = 0

        for notebook in self.notebooks.values():
            total_topics.update(notebook['topics'])
            total_use_count += notebook['use_count']

        # Find most used
        most_used = None
        if self.notebooks:
            most_used = max(
                self.notebooks.values(),
                key=lambda n: n['use_count']
            )

        return {
            'total_notebooks': total_notebooks,
            'total_topics': len(total_topics),
            'total_use_count': total_use_count,
            'active_notebook': self.get_active_notebook(),
            'most_used_notebook': most_used,
            'library_path': str(self.library_file)
        }


def main():
    """Command-line interface for notebook management"""
    parser = argparse.ArgumentParser(description='Manage NotebookLM library')
    parser.add_argument('--profile', help='Profile to use (default: active profile)')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a notebook')
    add_parser.add_argument('--url', required=True, help='NotebookLM URL')
    add_parser.add_argument('--name', help='Display name (auto-detected if omitted)')
    add_parser.add_argument('--description', help='Description (auto-generated if omitted)')
    add_parser.add_argument('--topics', help='Comma-separated topics (auto-detected from sources if omitted)')
    add_parser.add_argument('--use-cases', help='Comma-separated use cases')
    add_parser.add_argument('--tags', help='Comma-separated tags')
    add_parser.add_argument('--no-fetch', action='store_true', help='Skip auto-fetching metadata from browser')

    # List command
    subparsers.add_parser('list', help='List all notebooks')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search notebooks')
    search_parser.add_argument('--query', required=True, help='Search query')

    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Set active notebook')
    activate_parser.add_argument('--id', required=True, help='Notebook ID')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a notebook')
    remove_parser.add_argument('--id', required=True, help='Notebook ID')

    # Stats command
    subparsers.add_parser('stats', help='Show library statistics')

    args = parser.parse_args()

    # Initialize library
    library = NotebookLibrary(profile_id=getattr(args, 'profile', None))

    # Execute command
    if args.command == 'add':
        name = args.name
        description = args.description
        topics_str = args.topics

        # Auto-fetch metadata from notebook page when fields are missing
        if not args.no_fetch and (not name or not description or not topics_str):
            print("Auto-detecting metadata from notebook page...")
            meta = fetch_notebook_metadata(
                args.url,
                profile_id=getattr(args, 'profile', None),
            )

            if not name and meta.get('title'):
                name = meta['title']
                print(f"  Using detected name: {name}")

            if not topics_str and meta.get('sources'):
                topics_str = ','.join(meta['sources'])
                print(f"  Using detected topics from sources: {topics_str}")

            if not description:
                if meta.get('sources'):
                    description = f"Notebook with {len(meta['sources'])} sources: {', '.join(meta['sources'][:5])}"
                elif name:
                    description = name
                print(f"  Using generated description: {description}")

        # Final fallback: extract ID from URL as name if still missing
        if not name:
            name = _extract_id_from_url(args.url) or 'unnamed-notebook'
            print(f"  Warning: Could not detect name, using: {name}")
        if not description:
            description = name
        if not topics_str:
            topics_str = 'general'
            print("  Warning: No topics detected, using: general")

        topics = [t.strip() for t in topics_str.split(',')]
        use_cases = [u.strip() for u in args.use_cases.split(',')] if args.use_cases else None
        tags = [t.strip() for t in args.tags.split(',')] if args.tags else None

        notebook = library.add_notebook(
            url=args.url,
            name=name,
            description=description,
            topics=topics,
            use_cases=use_cases,
            tags=tags
        )
        print(json.dumps(notebook, indent=2))

    elif args.command == 'list':
        notebooks = library.list_notebooks()
        if notebooks:
            print("\nNotebook Library:")
            for notebook in notebooks:
                active = " [ACTIVE]" if notebook['id'] == library.active_notebook_id else ""
                print(f"\n  {notebook['name']}{active}")
                print(f"     ID: {notebook['id']}")
                print(f"     Topics: {', '.join(notebook['topics'])}")
                print(f"     Uses: {notebook['use_count']}")
        else:
            print("Library is empty. Add notebooks with: notebook_manager.py add")

    elif args.command == 'search':
        results = library.search_notebooks(args.query)
        if results:
            print(f"\nFound {len(results)} notebooks:")
            for notebook in results:
                print(f"\n  {notebook['name']} ({notebook['id']})")
                print(f"     {notebook['description']}")
        else:
            print(f"No notebooks found for: {args.query}")

    elif args.command == 'activate':
        notebook = library.select_notebook(args.id)
        print(f"Now using: {notebook['name']}")

    elif args.command == 'remove':
        if library.remove_notebook(args.id):
            print("Notebook removed from library")

    elif args.command == 'stats':
        stats = library.get_stats()
        print("\nLibrary Statistics:")
        print(f"  Total notebooks: {stats['total_notebooks']}")
        print(f"  Total topics: {stats['total_topics']}")
        print(f"  Total uses: {stats['total_use_count']}")
        if stats['active_notebook']:
            print(f"  Active: {stats['active_notebook']['name']}")
        if stats['most_used_notebook']:
            print(f"  Most used: {stats['most_used_notebook']['name']} ({stats['most_used_notebook']['use_count']} uses)")
        print(f"  Library path: {stats['library_path']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
