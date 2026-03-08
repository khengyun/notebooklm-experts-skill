"""Browser helpers for NotebookLM skill workflows."""

import json
import time
import random
from pathlib import Path
from typing import Optional, List, Sequence, Tuple, Union

from patchright.sync_api import Playwright, BrowserContext, Page
from config import BROWSER_ARGS, QUERY_INPUT_SELECTORS, USER_AGENT
from runtime_logging import debug, debug_kv, expect, log_exception, step


SelectorTarget = Union[str, Sequence[str]]


def _selector_reason(exc: Optional[BaseException]) -> str:
    """Return a short reason string for selector failures."""
    if exc is None:
        return "unknown"

    message = str(exc).strip()
    return message or type(exc).__name__


def log_selector_attempt(
    context: str,
    selector: str,
    *,
    action: str,
    success: Optional[bool] = None,
    reason: Optional[str] = None,
    **extra,
) -> None:
    """Emit a structured selector attempt or result line through debug logging."""
    payload = {
        "context": context,
        "selector": selector,
        "action": action,
    }
    payload.update(extra)

    if success is None:
        debug_kv("selector.attempt", **payload)
        return

    payload["success"] = success
    if reason is not None:
        payload["reason"] = reason
    debug_kv("selector.result", **payload)


def wait_for_first_selector(
    page: Page,
    selectors: Sequence[str],
    *,
    context: str,
    timeout: int = 10000,
    state: str = "visible",
) -> Tuple[Optional[object], Optional[str]]:
    """Wait for the first selector that resolves successfully."""
    debug_kv(
        "selector.scan",
        context=context,
        action="wait_for_selector",
        selector_count=len(selectors),
        timeout=timeout,
        state=state,
    )

    for selector in selectors:
        log_selector_attempt(
            context,
            selector,
            action="wait_for_selector",
            timeout=timeout,
            state=state,
        )
        try:
            element = page.wait_for_selector(selector, timeout=timeout, state=state)
        except Exception as exc:
            log_selector_attempt(
                context,
                selector,
                action="wait_for_selector",
                success=False,
                reason=_selector_reason(exc),
                timeout=timeout,
                state=state,
            )
            continue

        if not element:
            log_selector_attempt(
                context,
                selector,
                action="wait_for_selector",
                success=False,
                reason="missing",
                timeout=timeout,
                state=state,
            )
            continue

        log_selector_attempt(
            context,
            selector,
            action="wait_for_selector",
            success=True,
            reason="matched",
            timeout=timeout,
            state=state,
        )
        return element, selector

    return None, None


def find_first_visible_selector(
    page: Page,
    selectors: Sequence[str],
    *,
    context: str,
) -> Tuple[Optional[str], Optional[object]]:
    """Return the first visible selector and element from a selector list."""
    debug_kv(
        "selector.scan",
        context=context,
        action="is_visible",
        selector_count=len(selectors),
    )

    for selector in selectors:
        log_selector_attempt(context, selector, action="is_visible")
        try:
            visible = page.is_visible(selector)
        except Exception as exc:
            log_selector_attempt(
                context,
                selector,
                action="is_visible",
                success=False,
                reason=_selector_reason(exc),
            )
            continue

        if not visible:
            log_selector_attempt(
                context,
                selector,
                action="is_visible",
                success=False,
                reason="not_visible",
            )
            continue

        element = page.query_selector(selector)
        if not element:
            log_selector_attempt(
                context,
                selector,
                action="query_selector",
                success=False,
                reason="missing_after_visible",
            )
            continue

        log_selector_attempt(
            context,
            selector,
            action="is_visible",
            success=True,
            reason="visible",
        )
        return selector, element

    return None, None


def get_latest_text_from_selectors(
    page: Page,
    selectors: Sequence[str],
    *,
    context: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Read the latest non-empty text from the first selector that yields content."""
    debug_kv(
        "selector.scan",
        context=context,
        action="query_selector_all",
        selector_count=len(selectors),
    )

    for selector in selectors:
        log_selector_attempt(context, selector, action="query_selector_all")
        try:
            elements = page.query_selector_all(selector)
        except Exception as exc:
            log_selector_attempt(
                context,
                selector,
                action="query_selector_all",
                success=False,
                reason=_selector_reason(exc),
            )
            continue

        if not elements:
            log_selector_attempt(
                context,
                selector,
                action="query_selector_all",
                success=False,
                reason="no_elements",
            )
            continue

        try:
            text = elements[-1].inner_text().strip()
        except Exception as exc:
            log_selector_attempt(
                context,
                selector,
                action="inner_text",
                success=False,
                reason=_selector_reason(exc),
                element_count=len(elements),
            )
            continue

        if not text:
            log_selector_attempt(
                context,
                selector,
                action="inner_text",
                success=False,
                reason="empty_text",
                element_count=len(elements),
            )
            continue

        log_selector_attempt(
            context,
            selector,
            action="inner_text",
            success=True,
            reason="matched_text",
            element_count=len(elements),
            text_length=len(text),
        )
        return text, selector

    return None, None


class BrowserFactory:
    """Factory for creating configured browser contexts"""

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        state_file: Optional[Path] = None,
    ) -> BrowserContext:
        """
        Launch a persistent browser context with anti-detection features
        and cookie workaround.

        Args:
            playwright: Playwright instance
            headless: Run headless
            user_data_dir: Chrome profile directory. If None, resolves from active profile.
            state_file: Path to state.json for cookie injection. If None, resolves from active profile.
        """
        if user_data_dir is None or state_file is None:
            from profile_manager import ProfileManager
            pm = ProfileManager()
            paths = pm.get_active_paths()
            if user_data_dir is None:
                user_data_dir = str(paths["browser_profile_dir"])
            if state_file is None:
                state_file = paths["state_file"]

        # Launch persistent context
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",  # Use real Chrome
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            user_agent=USER_AGENT,
            args=BROWSER_ARGS
        )

        # Cookie workaround for Playwright bug #36139.
        # Session cookies (expires=-1) don't persist in user_data_dir automatically
        BrowserFactory._inject_cookies(context, state_file)

        return context

    @staticmethod
    def _inject_cookies(context: BrowserContext, state_file: Path):
        """Inject cookies from state.json if available"""
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    if 'cookies' in state and len(state['cookies']) > 0:
                        context.add_cookies(state['cookies'])
            except Exception as e:
                log_exception("  Warning: Could not load state.json", e)


class StealthUtils:
    """Human-like interaction utilities"""

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500):
        """Add random delay"""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    @staticmethod
    def random_mouse_movement(page: Page):
        """Perform a small amount of movement to avoid robotic interactions."""
        width = 1280
        height = 720
        try:
            viewport = page.viewport_size or {}
            width = viewport.get("width", width)
            height = viewport.get("height", height)
        except Exception:
            pass

        x = random.randint(max(1, width // 5), max(2, (width * 4) // 5))
        y = random.randint(max(1, height // 5), max(2, (height * 4) // 5))
        page.mouse.move(x, y, steps=random.randint(3, 7))

    @staticmethod
    def human_type(
        page: Page,
        selector: SelectorTarget,
        text: str,
        wpm_min: int = 320,
        wpm_max: int = 480,
        *,
        context: str = "human_type",
    ) -> Optional[str]:
        """Type with human-like speed and return the selector that succeeded."""
        element, resolved_selector = StealthUtils._resolve_target(
            page,
            selector,
            context=context,
            timeout=2000,
        )

        if not element or not resolved_selector:
            print(f"Warning: Element not found for typing: {selector}")
            return None

        # Click to focus
        try:
            log_selector_attempt(context, resolved_selector, action="click")
            element.click(timeout=2000)
            log_selector_attempt(
                context,
                resolved_selector,
                action="click",
                success=True,
                reason="focused",
            )
        except Exception as exc:
            log_selector_attempt(
                context,
                resolved_selector,
                action="click",
                success=False,
                reason=_selector_reason(exc),
            )
            try:
                log_selector_attempt(context, resolved_selector, action="focus")
                element.focus()
                log_selector_attempt(
                    context,
                    resolved_selector,
                    action="focus",
                    success=True,
                    reason="fallback_focus",
                )
            except Exception as focus_exc:
                log_selector_attempt(
                    context,
                    resolved_selector,
                    action="focus",
                    success=False,
                    reason=_selector_reason(focus_exc),
                )
                print(f"Warning: Element focus failed for typing: {resolved_selector}")
                return None

        cps_min = max(1.0, (wpm_min * 5) / 60.0)
        cps_max = max(cps_min, (wpm_max * 5) / 60.0)

        # Type
        for char in text:
            delay_ms = random.uniform(1000 / cps_max, 1000 / cps_min)
            element.type(char, delay=delay_ms)
            if random.random() < 0.05:
                time.sleep(random.uniform(0.15, 0.4))

        return resolved_selector

    @staticmethod
    def realistic_click(
        page: Page,
        selector: SelectorTarget,
        *,
        context: str = "realistic_click",
    ) -> Optional[str]:
        """Click with realistic movement and return the selector that succeeded."""
        element, resolved_selector = StealthUtils._resolve_target(
            page,
            selector,
            context=context,
            timeout=2000,
        )
        if not element or not resolved_selector:
            return None

        # Optional: Move mouse to element (simplified)
        box = element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            page.mouse.move(x, y, steps=5)

        StealthUtils.random_delay(100, 300)
        try:
            log_selector_attempt(context, resolved_selector, action="click")
            element.click(timeout=2000)
            log_selector_attempt(
                context,
                resolved_selector,
                action="click",
                success=True,
                reason="clicked",
            )
        except Exception as exc:
            log_selector_attempt(
                context,
                resolved_selector,
                action="click",
                success=False,
                reason=_selector_reason(exc),
            )
            try:
                log_selector_attempt(context, resolved_selector, action="click_force")
                element.click(force=True, timeout=2000)
                log_selector_attempt(
                    context,
                    resolved_selector,
                    action="click_force",
                    success=True,
                    reason="force_clicked",
                )
            except Exception as force_exc:
                log_selector_attempt(
                    context,
                    resolved_selector,
                    action="click_force",
                    success=False,
                    reason=_selector_reason(force_exc),
                )
                return None
        StealthUtils.random_delay(100, 300)
        return resolved_selector

    @staticmethod
    def _resolve_target(
        page: Page,
        selector: SelectorTarget,
        *,
        context: str,
        timeout: int,
    ) -> Tuple[Optional[object], Optional[str]]:
        """Resolve a single selector or selector list to an element and winner."""
        if isinstance(selector, str):
            log_selector_attempt(context, selector, action="query_selector")
            element = page.query_selector(selector)
            if element:
                log_selector_attempt(
                    context,
                    selector,
                    action="query_selector",
                    success=True,
                    reason="matched",
                )
                return element, selector

            try:
                element = page.wait_for_selector(selector, timeout=timeout, state="visible")
            except Exception as exc:
                log_selector_attempt(
                    context,
                    selector,
                    action="wait_for_selector",
                    success=False,
                    reason=_selector_reason(exc),
                    timeout=timeout,
                    state="visible",
                )
                return None, None

            log_selector_attempt(
                context,
                selector,
                action="wait_for_selector",
                success=bool(element),
                reason="matched" if element else "missing",
                timeout=timeout,
                state="visible",
            )
            if element:
                return element, selector
            return None, None

        return wait_for_first_selector(
            page,
            list(selector),
            context=context,
            timeout=timeout,
            state="visible",
        )


# ------------------------------------------------------------------ #
# M3 — Add Web Source                                                  #
# ------------------------------------------------------------------ #

def add_source_web(
    notebook_url: str,
    source_url: str,
    profile_id: Optional[str] = None,
    headless: bool = True,
) -> bool:
    """Add a web URL (or YouTube URL) as a source to a NotebookLM notebook.

    Args:
        notebook_url: Full URL of the target notebook
        source_url: Web URL or YouTube URL to add as a source
        profile_id: Profile to use; None = active profile
        headless: Run browser headlessly

    Returns:
        True on success, False on failure
    """
    from patchright.sync_api import sync_playwright
    from auth_manager import AuthManager

    step("Add web source through NotebookLM browser flow")
    auth = AuthManager(profile_id=profile_id)
    if not auth.is_authenticated():
        print("Error: Not authenticated. Run auth_manager.py setup first.")
        return False

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
        page.set_viewport_size({"width": 1440, "height": 900})

        print("  Navigating to notebook...")
        expect("Notebook page should load and show the add-source action")
        page.goto(notebook_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Open the add-sources dialog
        add_btn_sel = 'button[aria-label="Thêm nguồn"]'
        page.wait_for_selector(add_btn_sel, timeout=15000)
        page.click(add_btn_sel)
        page.wait_for_timeout(1500)
        print("  Opened add-source dialog")

        # Click the "Trang web" (Website) option inside the dialog
        web_btn = page.query_selector('button:has-text("Trang web")')
        if not web_btn:
            print("  Error: 'Trang web' button not found in dialog")
            return False
        web_btn.click()
        page.wait_for_timeout(1500)
        print("  Clicked 'Trang web'")

        # Fill URL into the query box textarea
        url_input_selectors = [
            'textarea[aria-label="Hộp truy vấn"]',
            *QUERY_INPUT_SELECTORS,
        ]
        url_selector, _ = find_first_visible_selector(
            page,
            url_input_selectors,
            context="add_source.url_input",
        )

        if not url_selector:
            print("  Error: URL input textarea not found")
            return False

        page.fill(url_selector, source_url)
        debug(f"Filled source URL with selector: {url_selector}")
        print(f"  Filled URL via: {url_selector}")

        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        print(f"  Source submitted: {source_url}")
        return True

    except Exception as e:
        log_exception("  Error adding source", e)
        return False

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
