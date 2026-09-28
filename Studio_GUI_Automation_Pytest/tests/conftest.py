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


@pytest.fixture(autouse=True)
def recover_studio_between_cases(request):
    """Normalize Studio UI before every GUI test case.

    Keeps the shared session-scoped Studio process, but clears leftover
    tabs / Home state so a failure does not poison the next case.
    """
    if request.node.get_closest_marker("gui") is None:
        yield
        return

    studio = request.getfixturevalue("studio")
    studio.prepare_for_test_case()
    yield
