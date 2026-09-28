import pytest

from studio_automation.matrix import load_test_cases


# ============================================================
# Load all enabled test cases from YAML
# ============================================================

TEST_CASES = load_test_cases()


# ============================================================
# Pytest test
# ============================================================

@pytest.mark.gui
@pytest.mark.parametrize(
    "case",
    TEST_CASES,
    ids=[
        case["name"]
        for case in TEST_CASES
    ],
)
def test_create_build_and_verify_s37(studio,case):
    print("")
    print("=" * 70)
    print(
        f"TEST: {case['name']}"
    )
    print(
        f"BOARD: {case['board']}"
    )
    print(
        f"APPLICATION: {case['application']}"
    )
    print(
        f"TARGET IDE: {case['target_ide']}"
    )
    print(
        f"BUILD FOLDER: {case['build_folder']}"
    )
    print("=" * 70)

    # ========================================================
    # STEP 1
    # Prepare Studio for this application
    # ========================================================

    print(
        "Preparing Studio for current test case..."
    )

    studio.close_previous_tabs()

    print(
        "Studio workspace cleaned."
    )

    # ========================================================
    # STEP 2
    # Open Devices page
    # ========================================================

    print(
        f"Opening Devices page for board: "
        f"{case['board']}"
    )

    studio.open_devices()

    # ========================================================
    # STEP 3
    # Click Add Device(s)
    # ========================================================

    studio.open_add_device_search()

    # ========================================================
    # STEP 4
    # Search board
    # ========================================================

    studio.search_board(
        case["board"]
    )

    # ========================================================
    # STEP 5
    # Select board
    # ========================================================

    studio.select_board(
        case["board"]
    )

    print(
        f"Board selected successfully: "
        f"{case['board']}"
    )

    # ========================================================
    # STEP 6
    # Open Example Projects & Demos
    # ========================================================

    studio.open_example_projects_and_demos()

    # ========================================================
    # STEP 7
    # Count Machine Learning applications
    # ========================================================

    ml_application_count = (
        studio.count_machine_learning_applications()
    )

    print("")
    print("-" * 70)

    print(
        f"Board: {case['board']}"
    )

    print(
        "Machine Learning applications supported:",
        ml_application_count
    )

    print("-" * 70)

    # ========================================================
    # STEP 8
    # Search actual application from YAML
    # ========================================================

    studio.search_application(
        case["application"]
    )

    # ========================================================
    # STEP 9
    # Create Production application
    # ========================================================

    studio.create_production_application(
        case["application"]
    )

    # ========================================================
    # STEP 10
    # Select Target IDE
    # ========================================================

    studio.select_target_ide(
        case["target_ide"]
    )

    # ========================================================
    # STEP 11
    # Finish project creation
    # ========================================================

    studio.finish_project_creation()

    # ========================================================
    # STEP 12
    # Open project using configured IDE
    # ========================================================

    studio.open_project_in_target_ide(
        case["target_ide"]
    )

    # ========================================================
    # STEP 13
    # Current automation supports CMake build verification
    # ========================================================

    if not (
        case["target_ide"]
        .strip()
        .lower()
        .startswith("cmake")
    ):

        pytest.fail(
            "Current build verification supports "
            "CMake targets only. "
            f"Configured target: "
            f"{case['target_ide']}"
        )

    # ========================================================
    # STEP 14
    # Build application and verify .s37
    # ========================================================

    try:

        print(
            "Starting CMake build verification..."
        )

        result = studio.run_cmake_workflow(
            build_folder=case[
                "build_folder"
            ]
        )

        assert result is True, (
            f"Build verification failed for "
            f"application "
            f"'{case['application']}' "
            f"on board "
            f"'{case['board']}'."
        )

        # ====================================================
        # Final PASS output
        # ====================================================

        print("")
        print("=" * 70)
        print("TEST PASSED")

        print(
            f"Board: "
            f"{case['board']}"
        )

        print(
            f"Application: "
            f"{case['application']}"
        )

        print(
            f"Machine Learning applications supported: "
            f"{ml_application_count}"
        )

        print(
            ".s37 binary verified successfully."
        )

        print("=" * 70)

    finally:

        # ====================================================
        # Always clean terminal state.
        #
        # run_cmake_workflow() already closes the terminal
        # after successful .s37 verification.
        #
        # This also guarantees cleanup if the build fails.
        # ====================================================

        try:

            studio.close_cli_terminal()

        except Exception as error:

            print(
                "Terminal cleanup warning:",
                error
            )