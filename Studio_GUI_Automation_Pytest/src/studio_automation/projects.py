import time


from .configuration import PAGE_LOAD_TIMEOUT


class ProjectActions:
    def select_target_ide(self, target_ide):
        self._require_studio()

        print(f"Requested Target IDE: {target_ide}")

        # --------------------------------------------------------
        # STEP 1: Wait for Project Configuration
        # --------------------------------------------------------

        self._wait_for_project_configuration()

        window = self.studio.wrapper_object()

        # --------------------------------------------------------
        # STEP 2: Find Target IDE ComboBox
        # --------------------------------------------------------

        ide_combo = None

        for element in window.descendants():

            try:
                if (
                    element.element_info.control_type == "ComboBox"
                    and element.is_visible()
                    and element.is_enabled()
                ):

                    name = (
                        element.element_info.name or ""
                    ).strip()

                    # Known Target IDE values
                    if (
                        "VS Code" in name
                        or "Cursor" in name
                        or "CMake" in name
                        or "Makefile" in name
                    ):
                        ide_combo = element
                        break

            except Exception:
                pass

        if ide_combo is None:
            raise RuntimeError(
                "Target IDE ComboBox was not found."
            )

        current_ide = (
            ide_combo.element_info.name or ""
        ).strip()

        print(f"Current Target IDE: {current_ide}")

        # --------------------------------------------------------
        # STEP 3: Already selected?
        # --------------------------------------------------------

        if current_ide.lower() == target_ide.lower():

            print(
                f"Target IDE already selected: {target_ide}"
            )

            return

        # --------------------------------------------------------
        # STEP 4: Open dropdown
        # --------------------------------------------------------

        print(
            f"Changing Target IDE from "
            f"'{current_ide}' to '{target_ide}'"
        )

        ide_combo.click_input()

        time.sleep(0.5)

        # --------------------------------------------------------
        # STEP 5: Find dropdown option
        #
        # IMPORTANT:
        # Do NOT compare Windows handles.
        #
        # The ComboBox itself can have the same name as an option.
        # We specifically want a non-ComboBox element.
        # --------------------------------------------------------

        start_time = time.time()

        while time.time() - start_time < 10:

            window = self.studio.wrapper_object()

            candidates = []

            for element in window.descendants():

                try:

                    name = (
                        element.element_info.name or ""
                    ).strip()

                    control_type = (
                        element.element_info.control_type
                    )

                    if (
                        name.lower() == target_ide.lower()
                        and control_type != "ComboBox"
                        and element.is_visible()
                    ):

                        rect = element.rectangle()

                        # Ignore hidden Chromium elements
                        if (
                            rect.width() > 0
                            and rect.height() > 0
                        ):

                            candidates.append(element)

                            print(
                                "Possible IDE option:",
                                repr(name),
                                "| Type:",
                                control_type,
                                "| Rect:",
                                rect
                            )

                except Exception:
                    pass

            if candidates:

                # Prefer naturally selectable controls.
                priority = {
                    "ListItem": 0,
                    "DataItem": 1,
                    "Button": 2,
                    "Text": 3,
                    "Custom": 4,
                }

                candidates.sort(
                    key=lambda item:
                        priority.get(
                            item.element_info.control_type,
                            100
                        )
                )

                option = candidates[0]

                print(
                    "Selecting IDE option:",
                    repr(option.element_info.name),
                    "| Type:",
                    option.element_info.control_type
                )

                option.click_input()

                break

            print(
                f"Waiting for IDE option '{target_ide}'..."
            )

            time.sleep(0.5)

        else:
            raise RuntimeError(
                f"Target IDE option '{target_ide}' "
                f"was not found."
            )

        # --------------------------------------------------------
        # STEP 6: Verify selection actually changed
        # --------------------------------------------------------

        time.sleep(0.5)

        window = self.studio.wrapper_object()

        selected = False

        for element in window.descendants():

            try:

                if (
                    element.element_info.control_type
                    == "ComboBox"
                    and
                    (
                        element.element_info.name or ""
                    ).strip().lower()
                    == target_ide.lower()
                    and element.is_visible()
                ):

                    selected = True
                    break

            except Exception:
                pass

        if not selected:

            raise RuntimeError(
                f"Target IDE '{target_ide}' "
                f"was clicked but selection was not confirmed."
            )

        print(
            f"Target IDE selected successfully: {target_ide}"
        )
    def finish_project_creation(self):
        self._require_studio()

        print("Waiting for FINISH button...")

        self._wait_for_project_configuration()

        finish_button = self.studio.child_window(
            title="FINISH",
            control_type="Button"
        )

        finish_button.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=1
        )

        print("FINISH button found.")

        finish_button.click_input()

        print("FINISH clicked.")

        # Wait until Project Configuration closes.
        self._wait_for_project_configuration_to_close()
    def open_project_in_target_ide(self, target_ide):
        self._require_studio()

        print(f"Target IDE: {target_ide}")

        normalized_ide = (
            str(target_ide)
            .replace(" ", "")
            .lower()
        )

        ide_button_map = {
            "vscode(gcc)": "Open in VS Code",
            "vscode(llvm)": "Open in VS Code",

            "cursor(gcc)": "Open in Cursor",
            "cursor(llvm)": "Open in Cursor",

            "cmake(gcc/iar/llvm)": "Open in CLI CMake",

            "makefile(gcc)": "Open in CLI Make",
        }

        if normalized_ide not in ide_button_map:
            raise RuntimeError(
                f"Unsupported Target IDE: '{target_ide}'"
            )

        expected_button_name = ide_button_map[
            normalized_ide
        ]

        cli_targets = {
            "cmake(gcc/iar/llvm)",
            "makefile(gcc)",
        }

        print(
            f"Waiting for button: {expected_button_name}"
        )

        # ========================================================
        # STEP 1
        # Wait for the correct Open In button
        # ========================================================

        launch_button = None

        start_time = time.time()
        timeout = 120

        while time.time() - start_time < timeout:

            window = self.studio.wrapper_object()

            for button in window.descendants(
                control_type="Button"
            ):

                try:

                    name = (
                        button.element_info.name
                        or ""
                    ).strip()

                    automation_id = (
                        button.element_info.automation_id
                        or ""
                    ).strip()

                    if (
                        name == expected_button_name
                        and
                        automation_id == "open-in-ide-button"
                        and
                        button.is_visible()
                        and
                        button.is_enabled()
                    ):

                        launch_button = button
                        break

                except Exception:
                    pass

            if launch_button is not None:
                break

            print(
                f"Waiting for '{expected_button_name}'..."
            )

            time.sleep(1)

        if launch_button is None:
            raise RuntimeError(
                f"Button '{expected_button_name}' "
                f"did not appear within {timeout} seconds."
            )

        print(
            "Target IDE button found:",
            expected_button_name
        )

        # ========================================================
        # STEP 2
        # Click Open In ...
        # ========================================================

        self.studio.wrapper_object().set_focus()

        launch_button.click_input()

        print(
            f"Clicked: {expected_button_name}"
        )

        # ========================================================
        # STEP 3
        # For CLI targets, wait for the Windows Terminal that
        # actually becomes visible.
        #
        # IMPORTANT:
        # We are NOT checking for a "new handle" anymore.
        # ========================================================

        if normalized_ide in cli_targets:

            print(
                "Waiting for CLI terminal..."
            )

            self.cli_window_handle = (
                self._wait_for_cli_terminal(
                    timeout=30
                )
            )

            print(
                "CLI terminal ready."
            )

        else:

            print(
                f"Project opened using: {target_ide}"
            )

