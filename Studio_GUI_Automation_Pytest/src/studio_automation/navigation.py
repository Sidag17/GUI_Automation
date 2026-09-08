import time

from .configuration import BOARD_SEARCH_TIMEOUT, PAGE_LOAD_TIMEOUT


class NavigationMixin:
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
        
