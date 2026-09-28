import time

from pywinauto.keyboard import send_keys

from .configuration import PAGE_LOAD_TIMEOUT


class DeviceActions:

    def open_devices(self):
        """
        Open the DEVICES page directly from Studio's permanent
        left navigation.

        Home does not need to be active.
        """

        self._require_studio()

        print("")
        print(
            "Preparing to open DEVICES..."
        )

        # Old device-search controls must not be reused.
        self.search_box = None

        # ========================================================
        # STEP 1
        # Find visible DEVICES control
        # ========================================================

        print(
            "Searching for DEVICES navigation control..."
        )

        start_time = time.time()

        devices_target = None

        while (
            time.time() - start_time
            < PAGE_LOAD_TIMEOUT
        ):

            window = (
                self.studio.wrapper_object()
            )

            candidates = []

            for element in window.descendants():

                try:

                    name = (
                        element.element_info.name
                        or ""
                    ).strip()

                    if name.lower() != "devices":
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
                        element
                        .element_info
                        .control_type
                    )

                    automation_id = (
                        element
                        .element_info
                        .automation_id
                        or ""
                    ).strip()

                    print(
                        "DEVICES candidate:",
                        repr(name),
                        "| Type:",
                        control_type,
                        "| AutomationID:",
                        repr(automation_id),
                        "| Rect:",
                        rect,
                    )

                    # Prefer naturally clickable controls.
                    priority = {
                        "Hyperlink": 0,
                        "Button": 1,
                        "ListItem": 2,
                        "TreeItem": 3,
                        "Custom": 4,
                        "Group": 5,
                        "Text": 6,
                    }

                    score = priority.get(
                        control_type,
                        100
                    )

                    candidates.append(
                        (
                            score,
                            element,
                        )
                    )

                except Exception:
                    pass

            if candidates:

                candidates.sort(
                    key=lambda item: item[0]
                )

                devices_target = (
                    candidates[0][1]
                )

                break

            print(
                "DEVICES control not ready yet..."
            )

            time.sleep(0.5)

        if devices_target is None:

            raise RuntimeError(
                "DEVICES navigation control "
                "was not found."
            )

        print(
            "Selected DEVICES control:",
            repr(
                devices_target.element_info.name
            ),
            "| Type:",
            devices_target
            .element_info
            .control_type,
        )

        # ========================================================
        # STEP 2
        # Click DEVICES
        # ========================================================

        self.studio.wrapper_object().set_focus()

        try:

            devices_target.click_input()

        except Exception as error:

            raise RuntimeError(
                "DEVICES was found but could "
                f"not be clicked: {error}"
            )

        print(
            "DEVICES clicked."
        )

        # ========================================================
        # STEP 3
        # Wait for Add Device(s)
        #
        # This also proves that the DEVICES page actually opened.
        # ========================================================

        print(
            "Waiting for Add Device(s)..."
        )

        add_device_button = (
            self.studio.child_window(
                title="Add Device(s)",
                control_type="Button",
                auto_id="panel-page-add-device-btn",
            )
        )

        add_device_button.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=0.5,
        )

        print(
            "Devices page loaded. "
            "Add Device(s) is ready."
        )

    def open_add_device_search(self):

        self._require_studio()

        print("Looking for Add Device(s)...")

        add_device_button = self.studio.child_window(
            title="Add Device(s)",
            control_type="Button",
            auto_id="panel-page-add-device-btn",
        )

        add_device_button.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=0.5,
        )

        print(
            "Add Device(s) found.",
            "| AutomationID:",
            "panel-page-add-device-btn",
        )

        self.studio.wrapper_object().set_focus()

        add_device_button.click_input()

        print("Add Device(s) clicked.")

        # --------------------------------------------------------
        # This is the exact search control discovered by the
        # diagnostic test.
        #
        # AutomationID is dynamic, so DO NOT hardcode it.
        # The accessible name is stable.
        # --------------------------------------------------------

        search_box = self.studio.child_window(
            title="Search by product name - kit, board or part",
            control_type="Edit",
        )

        search_box.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=0.5,
        )

        self.search_box = (
            search_box.wrapper_object()
        )

        print(
            "Board search input ready."
        )


    def search_board(self, board_name):

        self._require_studio()

        if self.search_box is None:

            raise RuntimeError(
                "Board search box is not available. "
                "Run open_add_device_search() first."
            )

        print(
            f"Searching for board: {board_name}"
        )

        self.studio.wrapper_object().set_focus()

        self.search_box.click_input()

        try:

            self.search_box.set_edit_text("")

            self.search_box.set_edit_text(
                str(board_name)
            )

        except Exception:

            send_keys("^a")
            send_keys("{BACKSPACE}")

            send_keys(
                str(board_name),
                with_spaces=True,
            )

        print(
            f"Search text entered: {board_name}"
        )

        # Give Studio a small amount of time to rebuild
        # the filtered device-result UI.
        time.sleep(0.5)


    def select_board(self, board_name):


        self._require_studio()

        board_result = (
            self._wait_for_board_result(
                board_name
            )
        )

        name = (
            board_result.element_info.name
            or ""
        ).strip()

        control_type = (
            board_result
            .element_info
            .control_type
        )

        print(
            "Board result found:",
            repr(name),
            "| Type:",
            control_type,
        )

        self.studio.wrapper_object().set_focus()

        try:

            board_result.scroll_into_view()

            time.sleep(0.3)

        except Exception:
            pass

        # UI may rebuild after scrolling, so resolve again.
        board_result = (
            self._wait_for_board_result(
                board_name
            )
        )

        print(
            f"Clicking board result: "
            f"{board_result.element_info.name}"
        )

        board_result.click_input()

        print(
            "Board clicked successfully."
        )

        # Add-device search wrapper is now obsolete.
        self.search_box = None