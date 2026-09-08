from pywinauto.keyboard import send_keys

from .configuration import PAGE_LOAD_TIMEOUT


class DeviceActions:
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
    def select_board(self, board_name):

        self._require_studio()

        board_result = self._wait_for_board_result(board_name)

        name = (board_result.element_info.name or "").strip()
        print(f"Clicking board result: {name}")

        board_result.click_input()

        print("Board clicked successfully.")

