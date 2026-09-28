import re
import sys
import time
from pathlib import Path

from pywinauto import Desktop


# ============================================================
# Make src/studio_automation importable
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from studio_automation.configuration import (
    STUDIO_TITLE_REGEX,
)


# ============================================================
# Start
# ============================================================

print("")
print("=" * 70)
print("MACHINE LEARNING APPLICATION COUNT TEST")
print("=" * 70)


desktop = Desktop(
    backend="uia"
)


# ============================================================
# STEP 1
# Find Simplicity Studio
# ============================================================

print(
    "Searching for Simplicity Studio..."
)

studio_windows = desktop.windows(
    title_re=STUDIO_TITLE_REGEX
)

usable_windows = []

for window in studio_windows:

    try:

        if not window.is_visible():
            continue

        rect = window.rectangle()

        if (
            rect.width() <= 0
            or rect.height() <= 0
        ):
            continue

        usable_windows.append(
            window
        )

    except Exception:
        pass


if not usable_windows:

    raise RuntimeError(
        "Simplicity Studio is not open."
    )


# Prefer largest Studio window

usable_windows.sort(
    key=lambda window: (
        window.rectangle().width()
        * window.rectangle().height()
    ),
    reverse=True
)

studio_wrapper = usable_windows[0]

studio = desktop.window(
    handle=studio_wrapper.handle
)

studio_window = (
    studio.wrapper_object()
)

print(
    "Studio found:",
    repr(
        studio_wrapper.window_text()
    )
)

print(
    "Handle:",
    studio_wrapper.handle
)


# ============================================================
# Focus Studio
# ============================================================

studio_window.set_focus()

try:
    studio_window.maximize()
except Exception:
    pass

time.sleep(1)


# ============================================================
# STEP 2
# Find Filter on keywords
# ============================================================

print("")
print(
    "Searching for 'Filter on keywords'..."
)

filter_box = studio.child_window(
    title="Filter on keywords",
    control_type="ComboBox"
)

filter_box.wait(
    "exists visible enabled",
    timeout=15,
    retry_interval=0.5
)

box = filter_box.wrapper_object()

print(
    "Filter box found."
)

print(
    "AutomationID:",
    repr(
        box.element_info.automation_id
        or ""
    )
)

print(
    "Rect:",
    box.rectangle()
)


# ============================================================
# STEP 3
# Clear current search
# ============================================================

print("")
print(
    "Clearing previous filter..."
)

studio_window.set_focus()

box.click_input()

time.sleep(0.3)

box.type_keys(
    "^a{BACKSPACE}",
    set_foreground=True
)

time.sleep(0.5)


# ============================================================
# STEP 4
# Search for machine learning
# ============================================================

SEARCH_TEXT = "machine learning"

print(
    f"Searching for: {SEARCH_TEXT}"
)

box.type_keys(
    SEARCH_TEXT,
    with_spaces=True,
    set_foreground=True
)

time.sleep(0.5)

box.type_keys(
    "{ENTER}",
    set_foreground=True
)


# ============================================================
# STEP 5
# Find "X Items Found"
# ============================================================

print("")
print(
    "Waiting for item count..."
)

count = None
count_text = None

start_time = time.time()
timeout = 30

pattern = re.compile(
    r"^\s*(\d+)\s+items?\s+found\s*$",
    re.IGNORECASE
)


while (
    time.time() - start_time
    < timeout
):

    window = studio.wrapper_object()

    candidates = []

    for element in window.descendants():

        try:

            name = (
                element.element_info.name
                or ""
            ).strip()

            if not name:
                continue

            match = pattern.match(
                name
            )

            if not match:
                continue

            if not element.is_visible():
                continue

            rect = element.rectangle()

            if (
                rect.width() <= 0
                or rect.height() <= 0
            ):
                continue

            value = int(
                match.group(1)
            )

            candidates.append(
                (
                    value,
                    name,
                    element
                )
            )

            print(
                "FOUND COUNT CANDIDATE:",
                repr(name),
                "| Type:",
                element.element_info.control_type,
                "| AutomationID:",
                repr(
                    element.element_info.automation_id
                    or ""
                ),
                "| Rect:",
                rect
            )

        except Exception:
            pass


    if candidates:

        # Normally there should only be one.
        count, count_text, count_element = (
            candidates[0]
        )

        break


    print(
        "Item count not ready yet..."
    )

    time.sleep(0.5)


# ============================================================
# STEP 6
# Verify result
# ============================================================

print("")
print("=" * 70)


if count is None:

    print(
        "FAILED"
    )

    print(
        "Could not find text matching:"
    )

    print(
        "'X Items Found'"
    )

    print("=" * 70)

    raise RuntimeError(
        "Machine Learning application "
        "count could not be determined."
    )


print(
    "SUCCESS"
)

print(
    "Studio count text:",
    repr(count_text)
)

print(
    "Machine Learning applications supported:",
    count
)

print("=" * 70)


# ============================================================
# STEP 7
# Clear machine learning filter again
# ============================================================

print("")
print(
    "Clearing machine learning search..."
)

box = studio.child_window(
    title="Filter on keywords",
    control_type="ComboBox"
).wrapper_object()

studio_window.set_focus()

box.click_input()

time.sleep(0.3)

box.type_keys(
    "^a{BACKSPACE}",
    set_foreground=True
)

time.sleep(1)

print(
    "Search cleared."
)

print("")
print(
    "FINAL RESULT:"
)

print(
    f"Machine Learning application count = {count}"
)