import time
import win32gui

from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from robot.api.deco import keyword


class TerminalKeywords:
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
    
