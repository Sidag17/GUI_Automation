from pywinauto import Desktop


desktop = Desktop(backend="uia")


def print_element(element, prefix=""):
    try:
        print(
            prefix,
            "Name:", repr(element.element_info.name),
            "| Type:", element.element_info.control_type,
            "| AutomationID:", repr(element.element_info.automation_id),
            "| Class:", repr(element.element_info.class_name),
            "| Rect:", element.rectangle()
        )
    except Exception as error:
        print(prefix, "ERROR:", error)


print("=" * 80)
print("TOP LEVEL WINDOWS")
print("=" * 80)

windows = desktop.windows()

project_window = None


# ============================================================
# STEP 1
# Find which top-level window contains Project Configuration
# ============================================================

for index, window in enumerate(windows):

    try:
        print(
            f"\nWINDOW {index}:",
            repr(window.window_text()),
            "| Rect:",
            window.rectangle()
        )

        descendants = window.descendants()

        for element in descendants:

            try:
                name = (
                    element.element_info.name or ""
                ).strip()

                if name.lower() == "project configuration":

                    print("\n>>> PROJECT CONFIGURATION FOUND HERE <<<")
                    print_element(element, "    ")

                    project_window = window
                    break

            except Exception:
                pass

        if project_window is not None:
            break

    except Exception:
        pass


if project_window is None:
    raise RuntimeError(
        "Project Configuration UI was not found."
    )


print("\n")
print("=" * 80)
print("PROJECT CONFIGURATION WINDOW")
print("=" * 80)

print(
    "Window:",
    repr(project_window.window_text())
)


# ============================================================
# STEP 2
# Search for controls that we care about
# ============================================================

targets = [
    "Project Configuration",
    "Project Name",
    "Target IDE",
    "VS Code (GCC)",
    "FINISH",
    "BACK",
    "Use default location",
    "Copy contents",
]


for element in project_window.descendants():

    try:
        name = (
            element.element_info.name or ""
        ).strip()

        if not name:
            continue

        for target in targets:

            if target.lower() in name.lower():

                print("\nFOUND:")
                print_element(element, "    ")

                try:
                    parent = element.parent()

                    print("    Parent:")
                    print_element(parent, "        ")

                except Exception:
                    pass

                break

    except Exception:
        pass


# ============================================================
# STEP 3
# Print all useful controls
# ============================================================

print("\n")
print("=" * 80)
print("INPUT / SELECTION CONTROLS")
print("=" * 80)


interesting_types = {
    "ComboBox",
    "Edit",
    "Button",
    "RadioButton",
    "CheckBox",
    "List",
    "ListItem",
}


for element in project_window.descendants():

    try:
        control_type = (
            element.element_info.control_type
        )

        if control_type not in interesting_types:
            continue

        if not element.is_visible():
            continue

        print_element(element, "    ")

    except Exception:
        pass