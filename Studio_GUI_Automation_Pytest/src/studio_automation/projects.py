import time

from .configuration import PAGE_LOAD_TIMEOUT
from .uia_helpers import (
    UIA_TRANSIENT_ERRORS,
    element_name,
    element_type,
    is_usable,
)


class ProjectActions:
    def _find_target_ide_combo(self, window):
        """Locate the Target IDE ComboBox without a global first-match scan.

        Prefer a ComboBox near a 'Target IDE' label; fall back to a
        visible ComboBox whose current value looks like a known IDE.
        """
        known_markers = ("vs code", "cursor", "cmake", "makefile")
        labeled_candidates = []
        unmarked_candidates = []

        # Collect labels that identify the Target IDE field.
        label_parents = []
        for element in window.descendants(control_type="Text"):
            try:
                name = element_name(element).lower()
                if "target ide" not in name:
                    continue
                if not is_usable(element):
                    continue
                parent = element.parent()
                if parent is not None:
                    label_parents.append(parent)
            except UIA_TRANSIENT_ERRORS:
                continue

        for element in window.descendants(control_type="ComboBox"):
            try:
                if not (element.is_visible() and element.is_enabled()):
                    continue
                if not is_usable(element):
                    continue

                name = element_name(element)
                name_l = name.lower()
                looks_like_ide = any(
                    marker in name_l for marker in known_markers
                )

                near_label = False
                try:
                    parent = element.parent()
                    if parent is not None:
                        for label_parent in label_parents:
                            if parent == label_parent:
                                near_label = True
                                break
                            # Same container one level up (common Chromium layout).
                            if (
                                parent.parent() is not None
                                and label_parent.parent() is not None
                                and parent.parent() == label_parent.parent()
                            ):
                                near_label = True
                                break
                except UIA_TRANSIENT_ERRORS:
                    near_label = False

                if near_label and looks_like_ide:
                    labeled_candidates.append(element)
                elif looks_like_ide:
                    unmarked_candidates.append(element)
            except UIA_TRANSIENT_ERRORS:
                continue

        if labeled_candidates:
            return labeled_candidates[0]
        if unmarked_candidates:
            return unmarked_candidates[0]
        return None

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

        ide_combo = self._find_target_ide_combo(window)

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
        option_selected = False

        while time.time() - start_time < 10:

            window = self.studio.wrapper_object()

            candidates = []

            for element in window.descendants():

                try:

                    name = element_name(element)
                    control_type = element_type(element)

                    if (
                        name.lower() == target_ide.lower()
                        and control_type != "ComboBox"
                        and is_usable(element)
                    ):

                        candidates.append(element)

                        print(
                            "Possible IDE option:",
                            repr(name),
                            "| Type:",
                            control_type,
                        )

                except UIA_TRANSIENT_ERRORS:
                    continue

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
                            element_type(item),
                            100
                        )
                )

                option = candidates[0]

                print(
                    "Selecting IDE option:",
                    repr(element_name(option)),
                    "| Type:",
                    element_type(option)
                )

                option.click_input()
                option_selected = True
                break

            print(
                f"Waiting for IDE option '{target_ide}'..."
            )

            time.sleep(0.5)

        if not option_selected:
            raise RuntimeError(
                f"Target IDE option '{target_ide}' "
                f"was not found."
            )

        # --------------------------------------------------------
        # STEP 6: Verify selection actually changed
        # --------------------------------------------------------

        verify_deadline = time.time() + 10
        selected = False

        while time.time() < verify_deadline:
            window = self.studio.wrapper_object()
            combo = self._find_target_ide_combo(window)
            if combo is not None:
                current = element_name(combo).lower()
                if current == target_ide.lower():
                    selected = True
                    break
            time.sleep(0.3)

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

