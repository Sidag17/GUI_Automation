import pytest

from studio_automation.automation import StudioAutomation


@pytest.fixture(scope="session")
def studio():

    print("")
    print("=" * 70)
    print("SIMPLICITY STUDIO TEST SESSION")
    print("=" * 70)

    automation = StudioAutomation()

    # ========================================================
    # Connect to existing Studio or open it once
    # ========================================================

    automation.ensure_studio_session()

    yield automation

    # ========================================================
    # Final pytest session cleanup
    # ========================================================

    print("")
    print("=" * 70)
    print("PYTEST SESSION COMPLETE")
    print("=" * 70)

    try:

        automation.close_cli_terminal()

    except Exception as error:

        print(
            "Terminal cleanup warning:",
            error
        )