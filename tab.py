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
# Connect to Simplicity Studio
# ============================================================

desktop = Desktop(backend="uia")

print("")
print("=" * 70)
print("ADD DEVICE(S) UI AUTOMATION TEST")
print("=" * 70)

print("Searching for Simplicity Studio...")

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

        usable_windows.append(window)

    except Exception:
        pass


if not usable_windows:

    raise RuntimeError(
        "Simplicity Studio is not open."
    )


# ============================================================
# Prefer largest Studio window
# ============================================================

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

print(
    "Studio found:",
    repr(studio_wrapper.window_text())
)

print(
    "Handle:",
    studio_wrapper.handle
)


# ============================================================
# Bring Studio to foreground
# ============================================================

studio_window = studio.wrapper_object()

studio_window.set_focus()

try:
    studio_window.maximize()
except Exception:
    pass

time.sleep(1)


# ============================================================
# STEP 1
# Click DEVICES
# ============================================================

print("")
print("Searching for DEVICES...")

devices = studio.child_window(
    title="DEVICES",
    control_type="Hyperlink"
)

devices.wait(
    "exists visible enabled",
    timeout=15,
    retry_interval=0.5
)

print("DEVICES found.")

devices.click_input()

print("DEVICES clicked.")

time.sleep(2)


# ============================================================
# STEP 2
# Search for Add device(s)
# ============================================================

print("")
print("Searching for Add device(s)...")

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

        normalized = " ".join(
            name.lower().split()
        )

        # Accept small text variations.
        if "add device" not in normalized:
            continue

        if not element.is_visible():
            continue

        rect = element.rectangle()

        if (
            rect.width() <= 0
            or rect.height() <= 0
        ):
            continue

        control_type = (
            element.element_info.control_type
        )

        automation_id = (
            element.element_info.automation_id
            or ""
        ).strip()

        class_name = (
            element.element_info.class_name
            or ""
        ).strip()

        print("")
        print(
            "FOUND CANDIDATE:"
        )
        print(
            "  Name:",
            repr(name)
        )
        print(
            "  Type:",
            control_type
        )
        print(
            "  AutomationID:",
            repr(automation_id)
        )
        print(
            "  Class:",
            repr(class_name)
        )
        print(
            "  Rect:",
            rect
        )

        candidates.append(
            element
        )

    except Exception:
        pass


# ============================================================
# No candidate found
# ============================================================

if not candidates:

    print("")
    print(
        "Add device(s) was NOT found."
    )

    print("")
    print(
        "Printing visible controls containing "
        "'device' for debugging..."
    )

    for element in window.descendants():

        try:

            name = (
                element.element_info.name
                or ""
            ).strip()

            if (
                name
                and
                "device" in name.lower()
                and
                element.is_visible()
            ):

                print(
                    repr(name),
                    "| Type:",
                    element.element_info.control_type,
                    "| AutomationID:",
                    repr(
                        element.element_info.automation_id
                        or ""
                    )
                )

        except Exception:
            pass

    raise RuntimeError(
        "Unable to find Add device(s)."
    )


# ============================================================
# Prefer clickable control
# ============================================================

priority = {
    "Button": 0,
    "Hyperlink": 1,
    "ListItem": 2,
    "Custom": 3,
    "Text": 4,
}

candidates.sort(
    key=lambda element:
        priority.get(
            element.element_info.control_type,
            100
        )
)

target = candidates[0]

print("")
print(
    "SELECTED TARGET:"
)

print(
    "Name:",
    repr(
        target.element_info.name
    )
)

print(
    "Type:",
    target.element_info.control_type
)

print(
    "AutomationID:",
    repr(
        target.element_info.automation_id
        or ""
    )
)


# ============================================================
# STEP 3
# Click Add device(s)
# ============================================================

studio_window.set_focus()

try:

    target.scroll_into_view()

    time.sleep(0.5)

except Exception:
    pass


print("")
print(
    "Clicking Add device(s)..."
)

target.click_input()

print(
    "Add device(s) clicked."
)

time.sleep(2)


# ============================================================
# STEP 4
# Verify some search/edit control appeared
# ============================================================

print("")
print(
    "Checking for board search input..."
)

window = studio.wrapper_object()

visible_edits = []

for element in window.descendants(
    control_type="Edit"
):

    try:

        if not (
            element.is_visible()
            and element.is_enabled()
        ):
            continue

        rect = element.rectangle()

        if (
            rect.width() <= 0
            or rect.height() <= 0
        ):
            continue

        visible_edits.append(
            element
        )

        print(
            "VISIBLE EDIT:",
            repr(
                element.element_info.name
                or ""
            ),
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


print("")
print("=" * 70)

if visible_edits:

    print(
        "SUCCESS:"
    )

    print(
        "Add device(s) was clicked and "
        "a visible input control was found."
    )

else:

    print(
        "Add device(s) was clicked, "
        "but no visible Edit control was detected."
    )

    print(
        "Check the Studio screen and the "
        "candidate information above."
    )

print("=" * 70)