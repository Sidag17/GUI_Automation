import subprocess
import time

from pywinauto import Desktop
from pywinauto.keyboard import send_keys


# ============================================================
# CONFIGURATION
# ============================================================

STUDIO_EXE = (
    r"C:\Users\siagrawa\.silabs\slt\installs\archive"
    r"\v6-base-v6.2.1-289\SimplicityStudio-6\studio.exe"
)

STUDIO_TITLE_REGEX = r"^Simplicity Studio.*"

BOARD_NAME = "2601B"

STUDIO_START_TIMEOUT = 120
PAGE_LOAD_TIMEOUT = 60
BOARD_SEARCH_TIMEOUT = 60

desktop = Desktop(backend="uia")


# ============================================================
# STEP 1
# Launch Simplicity Studio if it is not already running
# ============================================================

def launch_studio():

    windows = desktop.windows(
        title_re=STUDIO_TITLE_REGEX
    )

    if windows:
        print("Simplicity Studio is already open.")
        return

    print("Opening Simplicity Studio...")

    subprocess.Popen(STUDIO_EXE)


# ============================================================
# STEP 2
# Wait until the REAL main Studio screen is ready
#
# Important:
# We do NOT return the splash/loading screen.
#
# We consider Studio ready only when the DEVICES navigation
# control exists.
# ============================================================

def wait_for_studio(timeout=STUDIO_START_TIMEOUT):

    print("Waiting for Simplicity Studio main screen...")

    start_time = time.time()

    while time.time() - start_time < timeout:

        windows = desktop.windows(
            title_re=STUDIO_TITLE_REGEX
        )

        for studio_wrapper in windows:

            try:

                studio = desktop.window(
                    handle=studio_wrapper.handle
                )

                devices = studio.child_window(
                    title="DEVICES",
                    control_type="Hyperlink"
                )

                # Splash screen does not contain DEVICES.
                if devices.exists(timeout=1):

                    print(
                        "Main Studio screen ready:",
                        repr(studio_wrapper.window_text())
                    )

                    return studio

            except Exception:
                pass

        print("Studio is still loading...")

        time.sleep(2)

    raise RuntimeError(
        "Simplicity Studio main screen did not load."
    )


# ============================================================
# STEP 3
# Maximize the REAL main Studio window
# ============================================================

def maximize_studio(studio):

    print("Maximizing main Simplicity Studio window...")

    window = studio.wrapper_object()

    window.set_focus()

    try:
        window.maximize()
    except Exception:
        pass

    print("Main Studio window maximized.")


# ============================================================
# STEP 4A
# Detect the TOP Studio tabs
#
# From our inspection:
#
# Home
#   Type = Text
#
# EFR32xG24 Dev Kit Board (...)
#   Type = Text
#
# Both appear on approximately the same horizontal tab row.
# ============================================================

def get_top_tabs(studio):

    window = studio.wrapper_object()

    text_elements = window.descendants(
        control_type="Text"
    )

    home_tab = None

    # --------------------------------------------------------
    # First find the top "Home" tab.
    #
    # Note:
    # Sidebar is "HOME" (uppercase Button)
    # Top tab is "Home" (Text)
    # --------------------------------------------------------

    for element in text_elements:

        try:

            name = (
                element.element_info.name or ""
            ).strip()

            if (
                name == "Home"
                and element.is_visible()
                and element.parent().element_info.control_type == "Group"
            ):

                home_tab = element
                break

        except Exception:
            pass

    if home_tab is None:
        print("Could not detect the top Home tab.")
        return []

    home_rect = home_tab.rectangle()

    home_center_y = (
        home_rect.top + home_rect.bottom
    ) // 2

    tabs = []

    # --------------------------------------------------------
    # Find Text elements located on the same horizontal row
    # as the Home tab.
    # --------------------------------------------------------

    for element in text_elements:

        try:

            name = (
                element.element_info.name or ""
            ).strip()

            if not name:
                continue

            if not element.is_visible():
                continue

            if (
                element.parent().element_info.control_type
                != "Group"
            ):
                continue

            rect = element.rectangle()

            # Ignore invisible/off-screen elements
            if rect.width() <= 0 or rect.height() <= 0:
                continue

            center_y = (
                rect.top + rect.bottom
            ) // 2

            # Same tab row as Home
            if abs(center_y - home_center_y) <= 12:
                tabs.append(element)

        except Exception:
            pass

    # Sort tabs left -> right
    tabs.sort(
        key=lambda item: item.rectangle().left
    )

    return tabs


# ============================================================
# STEP 4B
# Print currently open tabs
# ============================================================

def print_open_tabs(studio):

    tabs = get_top_tabs(studio)

    names = []

    for tab in tabs:

        try:
            names.append(
                (
                    tab.element_info.name or ""
                ).strip()
            )
        except Exception:
            pass

    print("Open top tabs:", names)

    return tabs


# ============================================================
# STEP 4C
# Check whether a specific tab still exists
# ============================================================

def tab_exists(studio, tab_name):

    tabs = get_top_tabs(studio)

    for tab in tabs:

        try:

            name = (
                tab.element_info.name or ""
            ).strip()

            if name == tab_name:
                return True

        except Exception:
            pass

    return False


# ============================================================
# STEP 4D
# Wait until a tab disappears after closing it
# ============================================================

def wait_for_tab_to_close(
    studio,
    tab_name,
    timeout=10
):

    start_time = time.time()

    while time.time() - start_time < timeout:

        if not tab_exists(
            studio,
            tab_name
        ):

            return True

        time.sleep(0.5)

    return False


# ============================================================
# STEP 4E
# Close ALL tabs except Home
# ============================================================

def close_non_home_tabs(studio):

    print("\nChecking previous Studio tabs...")

    # Maximum safety limit
    for _ in range(20):

        tabs = print_open_tabs(studio)

        non_home_tabs = []

        for tab in tabs:

            try:

                name = (
                    tab.element_info.name or ""
                ).strip()

                if (
                    name
                    and name.lower() != "home"
                ):

                    non_home_tabs.append(tab)

            except Exception:
                pass

        # ----------------------------------------------------
        # Nothing to close
        # ----------------------------------------------------

        if not non_home_tabs:

            print("No previous board/project tabs are open.")

            return

        # ----------------------------------------------------
        # Close one tab at a time.
        #
        # Important because UI tree changes after each close.
        # ----------------------------------------------------

        tab = non_home_tabs[-1]

        tab_name = (
            tab.element_info.name or ""
        ).strip()

        print(
            f"Previous tab detected: {tab_name}"
        )

        print(
            f"Activating tab: {tab_name}"
        )

        try:
            tab.click_input()
        except Exception as error:
            raise RuntimeError(
                f"Could not activate tab '{tab_name}': {error}"
            )

        # Small UI focus delay
        time.sleep(0.5)

        print(
            f"Closing tab: {tab_name}"
        )

        # Ctrl+W closes the currently selected Studio tab.
        # No screen coordinates are used.
        send_keys("^w")

        # ----------------------------------------------------
        # Verify that the tab actually disappeared.
        # ----------------------------------------------------

        if wait_for_tab_to_close(
            studio,
            tab_name,
            timeout=10
        ):

            print(
                f"Tab closed successfully: {tab_name}"
            )

        else:

            raise RuntimeError(
                f"Ctrl+W was sent but tab "
                f"'{tab_name}' did not close."
            )

    raise RuntimeError(
        "Too many tabs detected or unable to clean Studio tabs."
    )


# ============================================================
# STEP 5
# Open DEVICES page
# ============================================================

def open_devices_page(studio):

    print("\nWaiting for DEVICES...")

    devices = studio.child_window(
        title="DEVICES",
        control_type="Hyperlink"
    )

    devices.wait(
        "exists visible enabled",
        timeout=PAGE_LOAD_TIMEOUT,
        retry_interval=1
    )

    print("DEVICES found.")

    devices.click_input()

    print("DEVICES clicked.")


# ============================================================
# STEP 6
# Wait for Devices page to finish loading
#
# Instead of:
#
#     sleep(10)
#
# We wait until a usable Edit/Search field appears.
# ============================================================

def wait_for_search_box(studio):

    print("\nWaiting for Devices search box...")

    start_time = time.time()

    while (
        time.time() - start_time
        < PAGE_LOAD_TIMEOUT
    ):

        try:

            window = studio.wrapper_object()

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

                    name = (
                        edit.element_info.name
                        or ""
                    )

                    automation_id = (
                        edit.element_info.automation_id
                        or ""
                    )

                    print(
                        "Possible Edit:",
                        repr(name),
                        "| AutomationID:",
                        repr(automation_id)
                    )

                    # Best case:
                    # control accessibility name contains Search.
                    if "search" in name.lower():

                        print(
                            "Devices search box found."
                        )

                        return edit

                except Exception:
                    pass

            # ------------------------------------------------
            # Fallback:
            # If there is exactly one visible Edit field,
            # use that as the Devices search box.
            # ------------------------------------------------

            if len(visible_edits) == 1:

                print(
                    "Single visible Edit detected. "
                    "Using it as Devices search box."
                )

                return visible_edits[0]

        except Exception:
            pass

        print(
            "Devices page is still loading..."
        )

        time.sleep(1)

    raise RuntimeError(
        "Devices search box was not found."
    )


# ============================================================
# STEP 7
# Search for board
# ============================================================

def search_board(
    search_box,
    board_name
):

    print(
        f"\nSearching for board: {board_name}"
    )

    search_box.click_input()

    try:

        # Clear previous text if any
        search_box.set_edit_text("")

        search_box.set_edit_text(
            board_name
        )

    except Exception:

        # Chromium/UIA fallback
        send_keys("^a")
        send_keys("{BACKSPACE}")

        send_keys(
            board_name,
            with_spaces=True
        )

    print(
        f"Search text entered: {board_name}"
    )


# ============================================================
# STEP 8
# Wait for matching board search result
# ============================================================

def wait_for_board_result(
    studio,
    board_name,
    timeout=BOARD_SEARCH_TIMEOUT
):

    print(
        f"\nWaiting for board result containing "
        f"'{board_name}'..."
    )

    start_time = time.time()

    while (
        time.time() - start_time
        < timeout
    ):

        try:

            window = studio.wrapper_object()

            candidates = []

            for element in window.descendants():

                try:

                    name = (
                        element.element_info.name
                        or ""
                    ).strip()

                    control_type = (
                        element.element_info.control_type
                    )

                    if not name:
                        continue

                    if (
                        board_name.lower()
                        not in name.lower()
                    ):
                        continue

                    if not element.is_visible():
                        continue

                    # Search field itself must not be selected
                    if control_type == "Edit":
                        continue

                    candidates.append(
                        element
                    )

                    print(
                        "Possible board result:",
                        repr(name),
                        "| Type:",
                        control_type
                    )

                except Exception:
                    pass

            if candidates:

                # ------------------------------------------------
                # Prefer naturally clickable controls over Text.
                # ------------------------------------------------

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
                    key=lambda item:
                        priority.get(
                            item.element_info.control_type,
                            100
                        )
                )

                result = candidates[0]

                print(
                    "Selected board result:",
                    repr(
                        result.element_info.name
                    ),
                    "| Type:",
                    result.element_info.control_type
                )

                return result

        except Exception:
            pass

        print(
            "Board result not ready yet..."
        )

        time.sleep(1)

    raise RuntimeError(
        f"No result found for board '{board_name}'."
    )


# ============================================================
# STEP 9
# Click board result
# ============================================================

def click_board(board_result):

    board_name = (
        board_result.element_info.name
        or ""
    ).strip()

    print(
        f"\nClicking board result: {board_name}"
    )

    board_result.click_input()

    print(
        "Board clicked successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 55)
    print("SIMPLICITY STUDIO GUI AUTOMATION")
    print("=" * 55)

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    launch_studio()

    # --------------------------------------------------------
    # STEP 2
    # Wait for actual main screen, NOT splash screen.
    # --------------------------------------------------------

    studio = wait_for_studio()

    # --------------------------------------------------------
    # STEP 3
    # Maximize only after main screen has loaded.
    # --------------------------------------------------------

    maximize_studio(studio)

    # --------------------------------------------------------
    # STEP 4
    # Close previous board/project tabs.
    # Home is preserved.
    # --------------------------------------------------------

    close_non_home_tabs(studio)

    # --------------------------------------------------------
    # STEP 5
    # Open Devices page.
    # --------------------------------------------------------

    open_devices_page(studio)

    # --------------------------------------------------------
    # STEP 6
    # Wait until Devices page actually loaded.
    # --------------------------------------------------------

    search_box = wait_for_search_box(
        studio
    )

    # --------------------------------------------------------
    # STEP 7
    # Search board.
    # --------------------------------------------------------

    search_board(
        search_box,
        BOARD_NAME
    )

    # --------------------------------------------------------
    # STEP 8
    # Wait for search result.
    # --------------------------------------------------------

    board_result = wait_for_board_result(
        studio,
        BOARD_NAME
    )

    # --------------------------------------------------------
    # STEP 9
    # Click board.
    # --------------------------------------------------------

    click_board(
        board_result
    )

    print("\n")
    print("=" * 55)
    print("AUTOMATION COMPLETED")
    print("=" * 55)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()