from pywinauto import Desktop

desktop = Desktop(backend="uia")

windows = desktop.windows(
    title_re=r"^Simplicity Studio.*"
)

studio = max(
    windows,
    key=lambda w: w.rectangle().width() * w.rectangle().height()
)

print("Studio:", repr(studio.window_text()))

elements = studio.descendants()

print("Total UI elements detected:", len(elements))
print("\n--- ELEMENTS WITH NAMES ---")

for i, element in enumerate(elements):
    try:
        name = element.element_info.name
        control_type = element.element_info.control_type
        class_name = element.element_info.class_name
        automation_id = element.element_info.automation_id

        if name:
            print(
                f"{i}: "
                f"Name={repr(name)} | "
                f"Type={control_type} | "
                f"Class={repr(class_name)} | "
                f"AutomationID={repr(automation_id)}"
            )

    except Exception:
        pass