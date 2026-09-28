"""Shared UIA helpers for screen-independent Studio automation.

Design rules:
- Locate controls by AutomationId / accessible name / control type.
- Interact via invoke/click_input on the resolved wrapper.
- Never click absolute screen coordinates.
- Prefer condition waits over fixed sleeps.
"""

from __future__ import annotations

import re
import time
from typing import Callable, Optional


# COM/UIA stale-element and discovery failures are common while Studio
# rebuilds Chromium-backed pages. Catch these narrowly instead of bare Exception.
try:
    from pywinauto.findwindows import ElementNotFoundError
except ImportError:  # pragma: no cover
    ElementNotFoundError = Exception  # type: ignore[misc, assignment]

try:
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError
except ImportError:  # pragma: no cover
    PywinautoTimeoutError = TimeoutError  # type: ignore[misc, assignment]

try:
    from comtypes import COMError
except ImportError:  # pragma: no cover
    COMError = Exception  # type: ignore[misc, assignment]

UIA_TRANSIENT_ERRORS = (
    ElementNotFoundError,
    PywinautoTimeoutError,
    COMError,
    RuntimeError,
    AttributeError,
    ValueError,
)


def element_name(element) -> str:
    try:
        return (element.element_info.name or "").strip()
    except UIA_TRANSIENT_ERRORS:
        return ""


def element_type(element) -> str:
    try:
        return element.element_info.control_type or ""
    except UIA_TRANSIENT_ERRORS:
        return ""


def element_auto_id(element) -> str:
    try:
        return (element.element_info.automation_id or "").strip()
    except UIA_TRANSIENT_ERRORS:
        return ""


def is_usable(element) -> bool:
    """True when an element is visible with a non-empty bounding box."""
    try:
        if not element.is_visible():
            return False
        rect = element.rectangle()
        return rect.width() > 0 and rect.height() > 0
    except UIA_TRANSIENT_ERRORS:
        return False


def wait_until(
    predicate: Callable[[], bool],
    timeout: float,
    interval: float = 0.5,
    description: str = "condition",
) -> bool:
    """Poll until predicate returns True or timeout expires."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            if predicate():
                return True
        except UIA_TRANSIENT_ERRORS:
            pass
        time.sleep(interval)
    return False


def wait_until_result(
    factory: Callable,
    timeout: float,
    interval: float = 0.5,
    description: str = "result",
):
    """Poll until factory returns a non-None value or raise TimeoutError."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = factory()
            if result is not None:
                return result
        except UIA_TRANSIENT_ERRORS:
            pass
        time.sleep(interval)
    raise TimeoutError(
        f"Timed out waiting for {description} "
        f"after {timeout} seconds."
    )


def board_match_score(control_name: str, board_name: str) -> Optional[int]:
    """Lower score is better. None means no match.

    Prefers exact and whole-token matches over loose substring matches
    so kits like '2601B' are not confused with longer related names.
    """
    name = (control_name or "").strip().lower()
    board = str(board_name or "").strip().lower()
    if not name or not board:
        return None

    if name == board:
        return 0

    # Whole-token / kit-id style match (e.g. "... BRD2601B ..." / "xG24 2601B")
    pattern = rf"(^|[^a-z0-9]){re.escape(board)}([^a-z0-9]|$)"
    if re.search(pattern, name):
        return 1

    if board in name:
        return 2

    return None
