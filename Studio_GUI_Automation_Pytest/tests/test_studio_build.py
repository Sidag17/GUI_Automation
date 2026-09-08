import pytest

from studio_automation.matrix import load_test_cases


TEST_CASES = load_test_cases()


@pytest.mark.gui
@pytest.mark.parametrize(
    "case",
    TEST_CASES,
    ids=[case["name"] for case in TEST_CASES],
)
def test_create_build_and_verify_s37(studio, case):
    """Create the configured Studio example, build it, and verify .s37."""

    studio.open_studio()
    studio.wait_for_main_screen()
    studio.maximize_studio()
    studio.close_previous_tabs()

    studio.open_devices()
    studio.search_board(case["board"])
    studio.select_board(case["board"])

    studio.open_example_projects_and_demos()
    studio.search_application(case["application"])
    studio.create_production_application(case["application"])

    studio.select_target_ide(case["target_ide"])
    studio.finish_project_creation()
    studio.open_project_in_target_ide(case["target_ide"])

    if not case["target_ide"].lower().startswith("cmake"):
        pytest.fail(
            "The current build verification workflow supports CMake targets. "
            f"Configured target_ide was: {case['target_ide']}"
        )

    assert studio.run_cmake_workflow(
        build_folder=case["build_folder"]
    ) is True
