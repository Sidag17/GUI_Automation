import time

from pywinauto import Desktop
from pywinauto.keyboard import send_keys


desktop = Desktop(backend="uia")

print("Searching for Windows Terminal...")


terminal_candidates = []


for window in desktop.windows():

    try:
        class_name = (
            window.element_info.class_name
            or ""
        ).strip()

        if class_name != "CASCADIA_HOSTING_WINDOW_CLASS":
            continue

        if not window.is_visible():
            continue

        print(
            "Windows Terminal found:",
            repr(window.window_text()),
            "| Handle:",
            window.handle
        )

        # --------------------------------------------
        # Look for actual terminal input/display area.
        #
        # Our inspection showed:
        #
        # Type  = Text
        # Class = TermControl
        # --------------------------------------------

        term_controls = []

        for element in window.descendants():

            try:
                if (
                    element.element_info.control_type == "Text"
                    and
                    element.element_info.class_name == "TermControl"
                    and
                    element.is_visible()
                ):
                    term_controls.append(element)

            except Exception:
                pass

        if not term_controls:
            print("  No visible TermControl found.")
            continue

        print(
            f"  Found {len(term_controls)} TermControl(s)"
        )

        terminal_candidates.append(
            (
                window,
                term_controls[0]
            )
        )

    except Exception:
        pass


if not terminal_candidates:
    raise RuntimeError(
        "No usable Windows Terminal was found."
    )


# ============================================================
# Pick visible candidate
# ============================================================

terminal_window, terminal_area = terminal_candidates[0]


print("\nSelected terminal:")
print(
    "Title:",
    repr(terminal_window.window_text())
)
print(
    "Handle:",
    terminal_window.handle
)
print(
    "TermControl:",
    terminal_area.rectangle()
)


# ============================================================
# Bring terminal to foreground
# ============================================================

print("\nBringing terminal to foreground...")

terminal_window.set_focus()

time.sleep(1)


# ============================================================
# Click actual terminal content
# ============================================================

print("Focusing TermControl...")

terminal_area.click_input()

time.sleep(0.5)


# ============================================================
# TEST COMMAND
#
# Do NOT run CMake yet.
# First verify that keyboard input works.
# ============================================================

print("Sending test command...")

send_keys(
    "echo ROBOT_TERMINAL_TEST",
    with_spaces=True,
    pause=0.05
)

send_keys("{ENTER}")

print("Test command sent.")