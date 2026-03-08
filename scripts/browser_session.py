#!/usr/bin/env python3
"""Low-level browser session helper for NotebookLM page interactions."""

import time
import sys
from typing import Any, Dict, Optional
from pathlib import Path

from patchright.sync_api import BrowserContext, Page

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import StealthUtils, get_latest_text_from_selectors, wait_for_first_selector
from config import QUERY_INPUT_SELECTORS, RESPONSE_SELECTORS
from runtime_logging import debug_kv


class BrowserSession:
    """
    Represents a single browser tab within a shared NotebookLM context.
    """

    def __init__(self, session_id: str, context: BrowserContext, notebook_url: str):
        """
        Initialize a new browser session

        Args:
            session_id: Unique identifier for this session
            context: Browser context (shared or dedicated)
            notebook_url: Target NotebookLM URL for this session
        """
        self.id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.message_count = 0
        self.notebook_url = notebook_url
        self.context = context
        self.page = None
        self.stealth = StealthUtils()

        # Initialize the session
        self._initialize()

    def _initialize(self):
        """Initialize the browser session and navigate to NotebookLM"""
        print(f"Creating session {self.id}...")

        # Create new page (tab) in context
        self.page = self.context.new_page()
        print(f"  Navigating to NotebookLM...")

        try:
            # Navigate to notebook
            self.page.goto(self.notebook_url, wait_until="domcontentloaded", timeout=30000)

            # Check if login is needed
            if "accounts.google.com" in self.page.url:
                raise RuntimeError("Authentication required. Please run auth_manager.py setup first.")

            # Wait for page to be ready
            self._wait_for_ready()

            # Simulate human inspection
            self.stealth.random_mouse_movement(self.page)
            self.stealth.random_delay(300, 600)

            print(f"Session {self.id} ready!")

        except Exception as e:
            print(f"Failed to initialize session: {e}")
            if self.page:
                self.page.close()
            raise

    def _wait_for_ready(self):
        """Wait for NotebookLM page to be ready"""
        element, selector = wait_for_first_selector(
            self.page,
            QUERY_INPUT_SELECTORS,
            context=f"browser_session.ready.{self.id}",
            timeout=10000,
            state="visible",
        )
        if not element or not selector:
            raise TimeoutError("NotebookLM query input did not become ready")

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question in this session

        Args:
            question: The question to ask

        Returns:
            Dict with status, question, answer, session_id
        """
        try:
            self.last_activity = time.time()
            self.message_count += 1

            print(f"[{self.id}] Asking: {question}")

            # Snapshot current answer to detect new response
            previous_answer = self._snapshot_latest_response()

            # Find chat input
            _, chat_input_selector = wait_for_first_selector(
                self.page,
                QUERY_INPUT_SELECTORS,
                context=f"browser_session.ask_input.{self.id}",
                timeout=5000,
                state="visible",
            )
            if not chat_input_selector:
                raise TimeoutError("NotebookLM query input not found for session ask")

            # Click and type with human-like behavior
            clicked_selector = self.stealth.realistic_click(
                self.page,
                chat_input_selector,
                context=f"browser_session.click_input.{self.id}",
            )
            typed_selector = self.stealth.human_type(
                self.page,
                chat_input_selector,
                question,
                context=f"browser_session.type_input.{self.id}",
            )
            if not clicked_selector:
                debug_kv(
                    "browser_session.input_click",
                    session_id=self.id,
                    selector=chat_input_selector,
                    success=False,
                )
            if not typed_selector:
                raise TimeoutError("Could not type into NotebookLM query input")

            # Small pause before submit
            self.stealth.random_delay(300, 800)

            # Submit
            self.page.keyboard.press("Enter")

            # Wait for response
            print("  Waiting for response...")
            self.stealth.random_delay(1500, 3000)

            # Get new answer
            answer = self._wait_for_latest_answer(previous_answer)

            if not answer:
                raise Exception("Empty response from NotebookLM")

            print(f"  Got response ({len(answer)} chars)")

            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "session_id": self.id,
                "notebook_url": self.notebook_url
            }

        except Exception as e:
            print(f"  Error: {e}")
            return {
                "status": "error",
                "question": question,
                "error": str(e),
                "session_id": self.id
            }

    def _snapshot_latest_response(self) -> Optional[str]:
        """Get the current latest response text"""
        text, _ = get_latest_text_from_selectors(
            self.page,
            RESPONSE_SELECTORS,
            context=f"browser_session.snapshot.{self.id}",
        )
        return text

    def _wait_for_latest_answer(self, previous_answer: Optional[str], timeout: int = 120) -> str:
        """Wait for and extract the new answer"""
        start_time = time.time()
        last_candidate = None
        stable_count = 0
        poll_count = 0

        while time.time() - start_time < timeout:
            poll_count += 1
            debug_kv(
                "browser_session.response.poll",
                session_id=self.id,
                poll=poll_count,
                remaining_seconds=max(0, int(timeout - (time.time() - start_time))),
            )

            # Check if NotebookLM is still thinking (most reliable indicator)
            try:
                thinking_element = self.page.query_selector('div.thinking-message')
                if thinking_element and thinking_element.is_visible():
                    time.sleep(0.5)
                    continue
            except Exception:
                pass

            latest_text, response_selector = get_latest_text_from_selectors(
                self.page,
                RESPONSE_SELECTORS,
                context=f"browser_session.response.{self.id}.{poll_count}",
            )

            if latest_text and latest_text != previous_answer:
                if latest_text == last_candidate:
                    stable_count += 1
                    debug_kv(
                        "browser_session.response.stability",
                        session_id=self.id,
                        poll=poll_count,
                        selector=response_selector,
                        stable_count=stable_count,
                        text_length=len(latest_text),
                    )
                    if stable_count >= 3:
                        return latest_text
                else:
                    stable_count = 1
                    last_candidate = latest_text
                    debug_kv(
                        "browser_session.response.new_text",
                        session_id=self.id,
                        poll=poll_count,
                        selector=response_selector,
                        text_length=len(latest_text),
                    )

            time.sleep(0.5)

        raise TimeoutError(f"No response received within {timeout} seconds")

    def reset(self):
        """Reset the chat by reloading the page"""
        print(f"Resetting session {self.id}...")

        self.page.reload(wait_until="domcontentloaded")
        self._wait_for_ready()

        previous_count = self.message_count
        self.message_count = 0
        self.last_activity = time.time()

        print(f"Session reset (cleared {previous_count} messages)")
        return previous_count

    def close(self):
        """Close this session and clean up resources"""
        print(f"Closing session {self.id}...")

        if self.page:
            try:
                self.page.close()
            except Exception as e:
                print(f"  Warning: Error closing page: {e}")

        print(f"Session {self.id} closed")

    def get_info(self) -> Dict[str, Any]:
        """Get information about this session"""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "age_seconds": time.time() - self.created_at,
            "inactive_seconds": time.time() - self.last_activity,
            "message_count": self.message_count,
            "notebook_url": self.notebook_url
        }

    def is_expired(self, timeout_seconds: int = 900) -> bool:
        """Check if session has expired (default: 15 minutes)"""
        return (time.time() - self.last_activity) > timeout_seconds


if __name__ == "__main__":
    # Example usage
    print("Browser Session Module - Use ask_question.py for main interface")
    print("This module provides low-level browser session management.")
