import subprocess
import sys
import time
import win32gui
from pathlib import Path

from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from robot.api.deco import keyword

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.config import (
    STUDIO_EXE,
    STUDIO_TITLE_REGEX,
    STUDIO_START_TIMEOUT,
    PAGE_LOAD_TIMEOUT,
    BOARD_SEARCH_TIMEOUT,
)


class StudioLibrary:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self.desktop = Desktop(backend="uia")
        self.studio = None
        self.search_box = None


    @keyword("Open Studio")
    def open_studio(self):
        windows = self.desktop.windows(title_re=STUDIO_TITLE_REGEX)

        if windows:
            print("Simplicity Studio is already open.")
            return

        print("Opening Simplicity Studio...")
        subprocess.Popen(STUDIO_EXE)

    @keyword("Wait For Main Screen")
    def wait_for_main_screen(self):
        print("Waiting for Simplicity Studio main screen...")

        start_time = time.time()

        while time.time() - start_time < STUDIO_START_TIMEOUT:
            windows = self.desktop.windows(title_re=STUDIO_TITLE_REGEX)

            for wrapper in windows:
                try:
                    studio = self.desktop.window(handle=wrapper.handle)

                    devices = studio.child_window(
                        title="DEVICES",
                        control_type="Hyperlink",
                    )

                    # Splash/loading screen does not contain DEVICES.
                    if devices.exists(timeout=1):
                        self.studio = studio
                        print(
                            "Main Studio screen ready:",
                            repr(wrapper.window_text()),
                        )
                        return
                except Exception:
                    pass

            print("Studio is still loading...")
            time.sleep(2)

        raise RuntimeError(
            "Simplicity Studio main screen did not load."
        )

    @keyword("Maximize Studio")
    def maximize_studio(self):
        self._require_studio()

        window = self.studio.wrapper_object()
        window.set_focus()

        try:
            window.maximize()
        except Exception:
            pass

        print("Main Studio window maximized.")

    @keyword("Close Previous Tabs")
    def close_previous_tabs(self):
        self._require_studio()

        print("Checking previous Studio tabs...")

        # Re-scan after every close because the UI tree changes.
        for _ in range(20):
            tabs = self._get_top_tabs()

            names = [
                (tab.element_info.name or "").strip()
                for tab in tabs
            ]
            print("Open top tabs:", names)

            non_home_tabs = [
                tab
                for tab in tabs
                if (tab.element_info.name or "").strip().lower()
                != "home"
            ]

            if not non_home_tabs:
                print("No previous board/project tabs are open.")
                return

            tab = non_home_tabs[-1]
            tab_name = (tab.element_info.name or "").strip()

            print(f"Closing tab: {tab_name}")

            tab.click_input()
            time.sleep(0.5)
            send_keys("^w")

            if not self._wait_for_tab_to_close(
                tab_name,
                timeout=10,
            ):
                raise RuntimeError(
                    f"Tab '{tab_name}' did not close."
                )

            print(f"Tab closed successfully: {tab_name}")

        raise RuntimeError(
            "Could not clean all previous Studio tabs."
        )

    @keyword("Open Devices")
    def open_devices(self):
        self._require_studio()

        print("Waiting for DEVICES...")

        devices = self.studio.child_window(
            title="DEVICES",
            control_type="Hyperlink",
        )

        devices.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=1,
        )

        devices.click_input()

        print("DEVICES clicked.")

        # Wait for the page instead of using a fixed sleep.
        self.search_box = self._wait_for_search_box()

    @keyword("Search Board")
    def search_board(self, board_name):
        self._require_studio()

        if self.search_box is None:
            self.search_box = self._wait_for_search_box()

        print(f"Searching for board: {board_name}")

        self.search_box.click_input()

        try:
            self.search_box.set_edit_text("")
            self.search_box.set_edit_text(board_name)
        except Exception:
            send_keys("^a")
            send_keys("{BACKSPACE}")
            send_keys(str(board_name), with_spaces=True)

        print(f"Search text entered: {board_name}")

    @keyword("Select Board")
    def select_board(self, board_name):

        self._require_studio()

        board_result = self._wait_for_board_result(board_name)

        name = (board_result.element_info.name or "").strip()
        print(f"Clicking board result: {name}")

        board_result.click_input()

        print("Board clicked successfully.")

    @keyword("Open Example Projects And Demos")
    def open_example_projects_and_demos(self):
        self._require_studio()

        print("Looking for EXAMPLE PROJECTS & DEMOS...")

        start_time = time.time()

        while time.time() - start_time < PAGE_LOAD_TIMEOUT:

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

                    normalized = " ".join(
                        name.upper().split()
                    )

                    if (
                        "EXAMPLE PROJECTS" in normalized
                        and "DEMOS" in normalized
                        and element.is_visible()
                    ):
                        candidates.append(element)

                        print(
                            "FOUND:",
                            repr(name),
                            "| Type:",
                            control_type,
                            "| AutomationID:",
                            repr(
                                element.element_info.automation_id
                            )
                        )

                except Exception:
                    pass

            if candidates:

                # Prefer controls that are normally clickable
                priority = {
                    "Hyperlink": 0,
                    "Button": 1,
                    "TabItem": 2,
                    "Text": 3,
                    "Custom": 4,
                }

                candidates.sort(
                    key=lambda element:
                        priority.get(
                            element.element_info.control_type,
                            100
                        )
                )

                target = candidates[0]

                print(
                    "Using:",
                    repr(target.element_info.name),
                    "| Type:",
                    target.element_info.control_type
                )

                # Bring focus to Studio
                self.studio.wrapper_object().set_focus()

                # Click the actual UI element
                target.click_input()

                print(
                    "EXAMPLE PROJECTS & DEMOS clicked."
                )

                # Wait for next page
                self._wait_for_example_filter_page()

                return

            print(
                "EXAMPLE PROJECTS & DEMOS not ready yet..."
            )

            time.sleep(1)

        raise RuntimeError(
            "EXAMPLE PROJECTS & DEMOS was not found."
        )

    @keyword("Search Application")
    def search_application(self, application_name):
        self._require_studio()

        print(f"Searching for application: {application_name}")

        # Wait until Example Projects page is actually ready.
        self._wait_for_example_filter_page()

        filter_box = self.studio.child_window(
            title="Filter on keywords",
            control_type="ComboBox"
        )

        filter_box.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=1
        )

        # Use the actual ComboBox wrapper.
        box = filter_box.wrapper_object()

        # Bring Studio to foreground.
        self.studio.wrapper_object().set_focus()

        # Click search/filter box.
        box.click_input()

        time.sleep(0.3)

        # Clear previous search.
        box.type_keys(
            "^a{BACKSPACE}",
            set_foreground=True
        )

        # Search exact application name.
        box.type_keys(
            str(application_name),
            with_spaces=True,
            set_foreground=True
        )

        print(
            f"Application search entered: {application_name}"
        )

        time.sleep(0.3)

        box.type_keys(
            "{ENTER}",
            set_foreground=True
        )

        # Wait until requested application becomes visible.
        self._wait_for_application_visible(
            application_name
        )
    
    @keyword("Create Production Application")
    def create_production_application(self, application_name):
        self._require_studio()

        print(f"Looking for application: {application_name}")

        window = self.studio.wrapper_object()

        # --------------------------------------------------------
        # STEP 1: Get UI elements in accessibility/document order
        # --------------------------------------------------------

        elements = window.descendants()

        application_index = None

        for index, element in enumerate(elements):
            try:
                name = (
                    element.element_info.name or ""
                ).strip()

                control_type = (
                    element.element_info.control_type
                )

                if (
                    name.lower() == application_name.lower()
                    and control_type == "Text"
                ):
                    application_index = index
                    break

            except Exception:
                pass

        if application_index is None:
            raise RuntimeError(
                f"Application not found: {application_name}"
            )

        print(
            f"Application found: {application_name}"
        )

        application_element = elements[
            application_index
        ]


        # --------------------------------------------------------
        # STEP 2: Bring application into view
        # --------------------------------------------------------

        try:
            application_element.scroll_into_view()
            print("Application scrolled into view.")
            time.sleep(0.5)

        except Exception as error:
            print(
                "Application scroll_into_view not available:",
                error
            )


        # --------------------------------------------------------
        # IMPORTANT:
        # Re-read UI tree after scrolling because rectangles/UI
        # state may have changed.
        # --------------------------------------------------------

        window = self.studio.wrapper_object()
        elements = window.descendants()

        application_index = None

        for index, element in enumerate(elements):

            try:
                name = (
                    element.element_info.name or ""
                ).strip()

                if (
                    name.lower()
                    == application_name.lower()
                    and
                    element.element_info.control_type
                    == "Text"
                ):
                    application_index = index
                    break

            except Exception:
                pass

        if application_index is None:
            raise RuntimeError(
                "Application disappeared after scrolling."
            )


        # --------------------------------------------------------
        # STEP 3:
        # Search only forward from THIS application.
        #
        # Stop at "View Project Documentation", which marks the
        # end of this application card.
        # --------------------------------------------------------

        production_found = False
        quality_found = None
        create_button = None

        for element in elements[
            application_index + 1:
        ]:

            try:

                name = (
                    element.element_info.name or ""
                ).strip()

                control_type = (
                    element.element_info.control_type
                )

                if not name:
                    continue


                # -----------------------------------------------
                # End of current application's card
                # -----------------------------------------------

                if (
                    name.lower()
                    == "view project documentation"
                ):
                    break


                # -----------------------------------------------
                # Quality tag
                # -----------------------------------------------

                if (
                    name.lower()
                    in {
                        "production",
                        "experimental",
                        "evaluation",
                    }
                    and control_type == "Text"
                ):
                    quality_found = name

                    if name.lower() == "production":
                        production_found = True

                    print(
                        "Application quality:",
                        quality_found
                    )


                # -----------------------------------------------
                # CREATE button
                # -----------------------------------------------

                if (
                    name.upper() == "CREATE"
                    and control_type == "Button"
                ):

                    automation_id = (
                        element.element_info.automation_id
                        or ""
                    )

                    if (
                        automation_id
                        == "resource_item-btn-create"
                    ):
                        create_button = element

                        print(
                            "CREATE button found."
                        )

            except Exception:
                pass


        # --------------------------------------------------------
        # STEP 4: Verify Production is mandatory
        # --------------------------------------------------------

        if not production_found:

            if quality_found:

                raise RuntimeError(
                    f"Application '{application_name}' "
                    f"is '{quality_found}', not Production."
                )

            raise RuntimeError(
                f"Production tag was not found for "
                f"'{application_name}'."
            )


        # --------------------------------------------------------
        # STEP 5: Verify CREATE exists
        # --------------------------------------------------------

        if create_button is None:
            raise RuntimeError(
                f"CREATE button was not found for "
                f"'{application_name}'."
            )


        # --------------------------------------------------------
        # STEP 6: Scroll CREATE into view if necessary
        # --------------------------------------------------------

        try:

            create_button.scroll_into_view()

            print(
                "CREATE button scrolled into view."
            )

            time.sleep(0.5)

        except Exception as error:

            print(
                "CREATE scroll_into_view not available:",
                error
            )


        # --------------------------------------------------------
        # STEP 7: Click CREATE
        # --------------------------------------------------------

        create_button.click_input()

        print(
            f"CREATE clicked for Production application: "
            f"{application_name}"
        )
    
    @keyword("Select Target IDE")
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
    
    @keyword("Finish Project Creation")
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

    @keyword("Open Project In Target IDE")
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

    @keyword("Run CMake Workflow")
    def run_cmake_workflow(
        self,
        build_folder="cmake_gcc",
        timeout=600
    ):

        print("Starting CMake workflow...")

        # ========================================================
        # STEP 1
        # Enter cmake_gcc folder
        # ========================================================

        print(
            f"Changing directory to: {build_folder}"
        )

        self._send_cli_command(
            f'cd /d "{build_folder}" '
            f'&& title CMAKE_DIR_READY '
            f'|| title CMAKE_DIR_FAIL'
        )

        result = self._wait_for_terminal_title(
            success_marker="CMAKE_DIR_READY",
            failure_marker="CMAKE_DIR_FAIL",
            timeout=30
        )

        if not result:
            raise RuntimeError(
                f"Failed to enter folder: {build_folder}"
            )

        print(
            f"Successfully entered folder: "
            f"{build_folder}"
        )

        # ========================================================
        # STEP 2
        # Run CMake workflow
        # ========================================================

        print(
            "Running: "
            "cmake --workflow --preset project"
        )

        self._send_cli_command(
            "cmake --workflow --preset project "
            "&& title CMAKE_WORKFLOW_PASS "
            "|| title CMAKE_WORKFLOW_FAIL"
        )

        result = self._wait_for_terminal_title(
            success_marker="CMAKE_WORKFLOW_PASS",
            failure_marker="CMAKE_WORKFLOW_FAIL",
            timeout=int(timeout)
        )

        if not result:
            raise RuntimeError(
                "CMake workflow failed."
            )

        print(
            "CMake workflow completed successfully."
        )

        # ========================================================
        # STEP 3
        # Enter build/base folder
        # ========================================================

        print(
            "Checking generated binary folder: "
            "build/base"
        )

        self._send_cli_command(
            'cd /d ".\\build\\base" '
            '&& title BINARY_DIR_READY '
            '|| title BINARY_DIR_FAIL'
        )

        result = self._wait_for_terminal_title(
            success_marker="BINARY_DIR_READY",
            failure_marker="BINARY_DIR_FAIL",
            timeout=30
        )

        if not result:
            raise RuntimeError(
                "Build binary folder "
                "'build/base' was not found."
            )

        print(
            "Successfully entered build/base folder."
        )

        # ========================================================
        # STEP 4
        # Check whether .s37 binary exists
        # ========================================================

        print(
            "Searching for generated .s37 binary..."
        )

        self._send_cli_command(
            'dir /b *.s37 '
            '&& title S37_BINARY_FOUND '
            '|| title S37_BINARY_NOT_FOUND'
        )

        result = self._wait_for_terminal_title(
            success_marker="S37_BINARY_FOUND",
            failure_marker="S37_BINARY_NOT_FOUND",
            timeout=30
        )

        if not result:

            raise RuntimeError(
                "Cannot find the binary file. "
                "No .s37 file was generated in "
                "build/base."
            )

        # ========================================================
        # FINAL SUCCESS
        # ========================================================

        print(
            "========================================"
        )

        print(
            "AUTOMATION SUCCESSFUL"
        )

        print(
            ".s37 binary file found in build/base."
        )

        print(
            "========================================"
        )
    
    # ========================================================
    # PRIVATE HELPERS
    # ========================================================

    def _require_studio(self):
        if self.studio is None:
            raise RuntimeError(
                "Studio is not ready. Run 'Wait For Main Screen' first."
            )

    def _get_top_tabs(self):
        window = self.studio.wrapper_object()

        text_elements = window.descendants(
            control_type="Text"
        )

        home_tab = None

        for element in text_elements:
            try:
                name = (element.element_info.name or "").strip()

                if (
                    name == "Home"
                    and element.is_visible()
                    and element.parent().element_info.control_type
                    == "Group"
                ):
                    home_tab = element
                    break
            except Exception:
                pass

        if home_tab is None:
            return []

        home_rect = home_tab.rectangle()
        home_center_y = (
            home_rect.top + home_rect.bottom
        ) // 2

        tabs = []

        for element in text_elements:
            try:
                name = (element.element_info.name or "").strip()

                if not name or not element.is_visible():
                    continue

                if (
                    element.parent().element_info.control_type
                    != "Group"
                ):
                    continue

                rect = element.rectangle()

                if rect.width() <= 0 or rect.height() <= 0:
                    continue

                center_y = (rect.top + rect.bottom) // 2

                if abs(center_y - home_center_y) <= 12:
                    tabs.append(element)

            except Exception:
                pass

        tabs.sort(key=lambda item: item.rectangle().left)

        return tabs

    def _tab_exists(self, tab_name):
        for tab in self._get_top_tabs():
            try:
                name = (tab.element_info.name or "").strip()

                if name == tab_name:
                    return True
            except Exception:
                pass

        return False

    def _wait_for_tab_to_close(self, tab_name, timeout=10):
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self._tab_exists(tab_name):
                return True

            time.sleep(0.5)

        return False

    def _wait_for_search_box(self):
        print("Waiting for Devices search box...")

        start_time = time.time()

        while time.time() - start_time < PAGE_LOAD_TIMEOUT:
            try:
                window = self.studio.wrapper_object()

                edits = window.descendants(
                    control_type="Edit"
                )

                visible_edits = []

                for edit in edits:
                    try:
                        if not (
                            edit.is_visible()
                            and edit.is_enabled()
                        ):
                            continue

                        visible_edits.append(edit)

                        name = edit.element_info.name or ""

                        if "search" in name.lower():
                            print("Devices search box found.")
                            return edit

                    except Exception:
                        pass

                # Current Devices page normally has one usable Edit.
                if len(visible_edits) == 1:
                    print(
                        "Single visible Edit detected. "
                        "Using it as Devices search box."
                    )
                    return visible_edits[0]

            except Exception:
                pass

            print("Devices page is still loading...")
            time.sleep(1)

        raise RuntimeError(
            "Devices search box was not found."
        )

    def _wait_for_board_result(self, board_name):
        print(
            f"Waiting for board result containing '{board_name}'..."
        )

        start_time = time.time()

        while time.time() - start_time < BOARD_SEARCH_TIMEOUT:
            try:
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

                        if not name:
                            continue

                        if (
                            str(board_name).lower()
                            not in name.lower()
                        ):
                            continue

                        if not element.is_visible():
                            continue

                        if control_type == "Edit":
                            continue

                        candidates.append(element)

                    except Exception:
                        pass

                if candidates:
                    priority = {
                        "TreeItem": 0,
                        "Hyperlink": 1,
                        "Button": 2,
                        "ListItem": 3,
                        "DataItem": 4,
                        "Custom": 5,
                        "Text": 6,
                    }

                    candidates.sort(
                        key=lambda item: priority.get(
                            item.element_info.control_type,
                            100,
                        )
                    )

                    result = candidates[0]

                    print(
                        "Selected board result:",
                        repr(result.element_info.name),
                        "| Type:",
                        result.element_info.control_type,
                    )

                    return result

            except Exception:
                pass

            print("Board result not ready yet...")
            time.sleep(1)

        raise RuntimeError(
            f"No result found for board '{board_name}'."
        )
        
    def _wait_for_example_filter_page(self):
        
        print("Waiting for Example Projects & Demos page...")
        self._wait_for_example_page_ready(
            timeout=PAGE_LOAD_TIMEOUT
        )

        filter_box = self.studio.child_window(
            title="Filter on keywords",
            control_type="ComboBox"
        )

        filter_box.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=1
        )

        print("Example Projects & Demos page loaded.")

    def _wait_for_example_page_ready(self, timeout=60):

        print("Waiting for Example Projects page to become ready...")

        start_time = time.time()

        while time.time() - start_time < timeout:

            window = self.studio.wrapper_object()

            # --------------------------------------------------
            # 1. Filter must exist and be usable
            # --------------------------------------------------
            try:
                filter_box = self.studio.child_window(
                    title="Filter on keywords",
                    control_type="ComboBox"
                )

                if not filter_box.exists(timeout=1):
                    time.sleep(0.5)
                    continue

                wrapper = filter_box.wrapper_object()

                if not (
                    wrapper.is_visible()
                    and wrapper.is_enabled()
                ):
                    time.sleep(0.5)
                    continue

            except Exception:
                time.sleep(0.5)
                continue

            # --------------------------------------------------
            # 2. Check whether a loader/progress element exists
            # --------------------------------------------------
            loading = False

            for element in window.descendants():

                try:
                    name = (
                        element.element_info.name or ""
                    ).lower()

                    control_type = (
                        element.element_info.control_type
                    )

                    if not element.is_visible():
                        continue

                    if control_type == "ProgressBar":
                        loading = True
                        break

                    if (
                        "loading" in name
                        or "please wait" in name
                    ):
                        loading = True
                        break

                except Exception:
                    pass

            if loading:

                print("Example page is still loading...")
                time.sleep(0.5)
                continue

            print("Example Projects page is ready.")
            return filter_box

        raise RuntimeError(
            "Example Projects page did not become ready."
        )
    
    def _wait_for_project_configuration(self):
        print("Waiting for Project Configuration...")

        start_time = time.time()

        while time.time() - start_time < PAGE_LOAD_TIMEOUT:

            window = self.studio.wrapper_object()

            for element in window.descendants():

                try:

                    name = (
                        element.element_info.name or ""
                    ).strip()

                    if (
                        name == "Project Configuration"
                        and
                        element.element_info.control_type == "Text"
                        and
                        element.is_visible()
                    ):

                        print(
                            "Project Configuration is ready."
                        )

                        return

                except Exception:
                    pass

            print(
                "Project Configuration still loading..."
            )

            time.sleep(0.5)

        raise RuntimeError(
            "Project Configuration did not load."
        )

    def _wait_for_project_configuration_to_close(
        self,
        timeout=120
    ):
        print(
            "Waiting for Project Configuration to close..."
        )

        start_time = time.time()

        while time.time() - start_time < timeout:

            found = False

            try:

                window = self.studio.wrapper_object()

                for element in window.descendants():

                    try:

                        name = (
                            element.element_info.name or ""
                        ).strip()

                        if (
                            name == "Project Configuration"
                            and
                            element.element_info.control_type == "Text"
                            and
                            element.is_visible()
                        ):

                            found = True
                            break

                    except Exception:
                        pass

            except Exception:
                pass

            if not found:

                print(
                    "Project Configuration closed."
                )

                return

            print(
                "Project creation in progress..."
            )

            time.sleep(1)

        raise RuntimeError(
            "Project Configuration did not close "
            "after clicking FINISH."
        )

    def _wait_for_cli_terminal(
        self,
        timeout=30
    ):
        print(
            "Searching for visible Windows Terminal..."
        )

        desktop = Desktop(
            backend="uia"
        )

        start_time = time.time()

        while time.time() - start_time < timeout:

            foreground_handle = (
                win32gui.GetForegroundWindow()
            )

            candidates = []

            for window in desktop.windows():

                try:

                    class_name = (
                        window.element_info.class_name
                        or ""
                    ).strip()

                    title = (
                        window.window_text()
                        or ""
                    ).strip()

                    if (
                        class_name
                        != "CASCADIA_HOSTING_WINDOW_CLASS"
                    ):
                        continue

                    if not window.is_visible():
                        continue

                    terminal_area = None

                    for element in window.descendants():

                        try:

                            if (
                                element.element_info.control_type
                                == "Text"
                                and
                                element.element_info.class_name
                                == "TermControl"
                                and
                                element.is_visible()
                            ):

                                terminal_area = element
                                break

                        except Exception:
                            pass

                    if terminal_area is None:
                        continue

                    # --------------------------------------------
                    # Prefer the terminal that became foreground
                    # after clicking "Open in CLI CMake".
                    # --------------------------------------------

                    score = 0

                    if window.handle == foreground_handle:
                        score += 100

                    if "cmd.exe" in title.lower():
                        score += 20

                    rect = window.rectangle()

                    if (
                        rect.width() > 0
                        and
                        rect.height() > 0
                    ):
                        score += 10

                    candidates.append(
                        (
                            score,
                            window,
                            terminal_area
                        )
                    )

                except Exception:
                    pass

            if candidates:

                candidates.sort(
                    key=lambda item: item[0],
                    reverse=True
                )

                score, terminal_window, terminal_area = (
                    candidates[0]
                )

                print(
                    "CLI terminal found:",
                    repr(
                        terminal_window.window_text()
                    ),
                    "| Handle:",
                    terminal_window.handle,
                    "| Score:",
                    score
                )

                # Make sure it can actually receive input.
                terminal_window.set_focus()

                time.sleep(0.3)

                terminal_area.click_input()

                time.sleep(0.3)

                return terminal_window.handle

            print(
                "CLI terminal not ready yet..."
            )

            time.sleep(0.5)

        raise RuntimeError(
            "Visible Windows Terminal with "
            "TermControl was not found."
        )

    def _send_cli_command(
        self,
        command
    ):
        print(
            f"Sending command: {command}"
        )

        # --------------------------------------------------------
        # If handle was somehow not stored, try to recover.
        # --------------------------------------------------------

        if self.cli_window_handle is None:

            print(
                "CLI handle not stored. "
                "Searching for terminal..."
            )

            self.cli_window_handle = (
                self._wait_for_cli_terminal(
                    timeout=30
                )
            )

        desktop = Desktop(
            backend="uia"
        )

        try:

            terminal_window = desktop.window(
                handle=self.cli_window_handle
            )

            terminal_window.wait(
                "exists visible",
                timeout=10,
                retry_interval=0.5
            )

        except Exception as error:

            raise RuntimeError(
                "Stored CLI terminal is no longer available: "
                f"{error}"
            )

        # ========================================================
        # Find TermControl inside THIS terminal
        # ========================================================

        terminal_area = None

        for element in terminal_window.descendants():

            try:

                if (
                    element.element_info.control_type
                    == "Text"
                    and
                    element.element_info.class_name
                    == "TermControl"
                    and
                    element.is_visible()
                ):

                    terminal_area = element
                    break

            except Exception:
                pass

        if terminal_area is None:

            raise RuntimeError(
                "TermControl was not found inside "
                "the selected CLI terminal."
            )

        # ========================================================
        # Focus the exact terminal
        # ========================================================

        terminal_window.set_focus()

        time.sleep(0.5)

        terminal_area.click_input()

        time.sleep(0.3)

        # ========================================================
        # Type command
        #
        # This is the exact method that worked in your
        # ROBOT_TERMINAL_TEST.
        # ========================================================

        send_keys(
            str(command),
            with_spaces=True,
            pause=0.01
        )

        send_keys("{ENTER}")

        print(
            "Command submitted successfully."
        )

        time.sleep(0.5)

    def _wait_for_terminal_title(
        self,
        success_marker,
        failure_marker,
        timeout
    ):
        if self.cli_window_handle is None:
            raise RuntimeError(
                "CLI terminal handle is not available."
            )

        desktop = Desktop(
            backend="uia"
        )

        print(
            f"Waiting for terminal result: "
            f"{success_marker}"
        )

        start_time = time.time()

        while time.time() - start_time < timeout:

            try:

                terminal_window = desktop.window(
                    handle=self.cli_window_handle
                )

                title = (
                    terminal_window.window_text()
                    or ""
                ).strip()

                if success_marker in title:

                    print(
                        f"Success detected: "
                        f"{success_marker}"
                    )

                    return True

                if failure_marker in title:

                    print(
                        f"Failure detected: "
                        f"{failure_marker}"
                    )

                    return False

            except Exception as error:

                print(
                    "Unable to read terminal title:",
                    error
                )

            time.sleep(0.5)

        raise RuntimeError(
            f"Terminal command did not finish "
            f"within {timeout} seconds."
        )
    
    def _wait_for_application_visible(self,
    application_name,
    timeout=60
):
        print(f"Waiting for application result: {application_name}")

        start_time = time.time()

        while time.time() - start_time < timeout:
            window = self.studio.wrapper_object()
            for element in window.descendants():
                try:
                    name = (element.element_info.name or "").strip()

                    control_type = (element.element_info.control_type)

                    if ( name.lower() == application_name.lower() and control_type == "Text" and element.is_visible()):
                        print( f"Application result found: " f"{application_name}")
                        return

                except Exception:
                    pass

            print("Waiting for application result..." )
            time.sleep(0.5)

        raise RuntimeError(f"Application '{application_name}' " f"did not become visible.")