import time

from .configuration import BOARD_SEARCH_TIMEOUT, PAGE_LOAD_TIMEOUT
from .uia_helpers import (
    UIA_TRANSIENT_ERRORS,
    board_match_score,
    element_name,
    element_type,
    is_usable,
)


class NavigationMixin:
    def _require_studio(self):
        if self.studio is None:
            raise RuntimeError(
                "Studio is not ready. Run 'Wait For Main Screen' first."
            )

    def _find_home_tab_text(self, window):
        """Locate the Home tab Text control under a Group parent."""
        for element in window.descendants(control_type="Text"):
            try:
                if element_name(element) != "Home":
                    continue
                if not element.is_visible():
                    continue
                parent = element.parent()
                if element_type(parent) != "Group":
                    continue
                return element
            except UIA_TRANSIENT_ERRORS:
                continue
        return None

    def _tab_label_from_group(self, group):
        """Return the primary Text label inside a tab Group, if any."""
        try:
            # Prefer direct children first (stable, shallow).
            for child in group.children():
                try:
                    if element_type(child) != "Text":
                        continue
                    name = element_name(child)
                    if name and is_usable(child):
                        return child
                except UIA_TRANSIENT_ERRORS:
                    continue

            for text in group.descendants(control_type="Text"):
                try:
                    name = element_name(text)
                    if name and is_usable(text):
                        return text
                except UIA_TRANSIENT_ERRORS:
                    continue
        except UIA_TRANSIENT_ERRORS:
            return None
        return None

    def _get_top_tabs(self):
        """Discover top document tabs via UIA tree structure.

        Tabs are sibling Groups under the same parent as the Home tab
        Group. This is screen-independent (no pixel Y banding / DPI
        assumptions) and avoids absolute coordinates for interaction.
        """
        window = self.studio.wrapper_object()
        home_tab = self._find_home_tab_text(window)

        if home_tab is None:
            return []

        try:
            home_group = home_tab.parent()
            tab_row = home_group.parent()
        except UIA_TRANSIENT_ERRORS:
            return [home_tab]

        tabs = []
        seen_handles = set()

        try:
            siblings = tab_row.children()
        except UIA_TRANSIENT_ERRORS:
            return [home_tab]

        for sibling in siblings:
            try:
                if element_type(sibling) != "Group":
                    continue

                label = self._tab_label_from_group(sibling)
                if label is None:
                    continue

                handle = getattr(label, "handle", None)
                if handle is not None:
                    if handle in seen_handles:
                        continue
                    seen_handles.add(handle)

                tabs.append(label)
            except UIA_TRANSIENT_ERRORS:
                continue

        if not tabs:
            return [home_tab]

        # Relative left-to-right order among already-found siblings only.
        # Used for close order — never for click targeting by pixels.
        try:
            tabs.sort(key=lambda item: item.rectangle().left)
        except UIA_TRANSIENT_ERRORS:
            pass

        return tabs

    def _tab_exists(self, tab_name):
        for tab in self._get_top_tabs():
            try:
                if element_name(tab) == tab_name:
                    return True
            except UIA_TRANSIENT_ERRORS:
                continue
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
                edits = window.descendants(control_type="Edit")
                visible_edits = []

                for edit in edits:
                    try:
                        if not (edit.is_visible() and edit.is_enabled()):
                            continue

                        visible_edits.append(edit)
                        name = element_name(edit)
                        if "search" in name.lower():
                            print("Devices search box found.")
                            return edit
                    except UIA_TRANSIENT_ERRORS:
                        continue

                # Current Devices page normally has one usable Edit.
                if len(visible_edits) == 1:
                    print(
                        "Single visible Edit detected. "
                        "Using it as Devices search box."
                    )
                    return visible_edits[0]

            except UIA_TRANSIENT_ERRORS:
                pass

            print("Devices page is still loading...")
            time.sleep(1)

        raise RuntimeError("Devices search box was not found.")

    def _activate_home_tab(self, timeout=20):
        self._require_studio()
        print("Ensuring Studio Home tab is active...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                for tab in self._get_top_tabs():
                    try:
                        if element_name(tab).lower() != "home":
                            continue
                        if not tab.is_visible():
                            continue

                        print("Home tab found.")
                        self.studio.wrapper_object().set_focus()
                        tab.click_input()
                        print("Home tab clicked.")
                        self.search_box = None

                        devices = self.studio.child_window(
                            title="DEVICES",
                            control_type="Hyperlink",
                        )
                        if devices.exists(timeout=3):
                            print("Home tab is active.")
                            return

                        print(
                            "Home clicked but DEVICES is "
                            "not ready yet..."
                        )
                    except UIA_TRANSIENT_ERRORS:
                        continue
            except UIA_TRANSIENT_ERRORS as error:
                print("Unable to activate Home:", error)

            time.sleep(0.5)

        raise RuntimeError(
            "Unable to activate Simplicity Studio Home tab."
        )

    def _wait_for_board_result(self, board_name):
        print(
            f"Waiting for board result containing '{board_name}'..."
        )
        start_time = time.time()

        while time.time() - start_time < BOARD_SEARCH_TIMEOUT:
            try:
                window = self.studio.wrapper_object()
                ranked = []

                for element in window.descendants():
                    try:
                        name = element_name(element)
                        control_type = element_type(element)
                        score = board_match_score(name, board_name)

                        if score is None:
                            continue
                        if not element.is_visible():
                            continue
                        if control_type == "Edit":
                            continue

                        type_priority = {
                            "TreeItem": 0,
                            "Hyperlink": 1,
                            "Button": 2,
                            "ListItem": 3,
                            "DataItem": 4,
                            "Custom": 5,
                            "Text": 6,
                        }
                        ranked.append(
                            (
                                score,
                                type_priority.get(control_type, 100),
                                element,
                            )
                        )
                    except UIA_TRANSIENT_ERRORS:
                        continue

                if ranked:
                    ranked.sort(key=lambda item: (item[0], item[1]))
                    result = ranked[0][2]
                    print(
                        "Selected board result:",
                        repr(element_name(result)),
                        "| Type:",
                        element_type(result),
                        "| Match score:",
                        ranked[0][0],
                    )
                    return result

            except UIA_TRANSIENT_ERRORS:
                pass

            print("Board result not ready yet...")
            time.sleep(1)

        raise RuntimeError(
            f"No result found for board '{board_name}'."
        )

    def prepare_for_test_case(self):
        """Normalize Studio UI before each matrix case.

        Re-attaches if needed, activates Home, and closes leftover
        project/board tabs so a prior failure cannot poison the next case.
        """
        self._require_studio()
        print("Preparing Studio workspace for next test case...")

        try:
            self.studio.wrapper_object().set_focus()
        except UIA_TRANSIENT_ERRORS as error:
            print("Could not focus Studio:", error)

        try:
            self._activate_home_tab(timeout=20)
        except RuntimeError as error:
            print("Home activation warning:", error)

        self.close_previous_tabs()
        self.search_box = None
        print("Studio workspace ready.")
