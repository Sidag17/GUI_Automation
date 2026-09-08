*** Settings ***
Library    ../library/StudioLibrary.py


*** Keywords ***
Create And Build Studio Application
    [Arguments]    ${board}    ${application}    ${target_ide}    ${build_folder}=cmake_gcc

    Open Studio
    Wait For Main Screen
    Maximize Studio
    Close Previous Tabs

    Open Devices
    Search Board    ${board}
    Select Board    ${board}

    Open Example Projects And Demos
    Search Application    ${application}
    Create Production Application    ${application}

    Select Target IDE    ${target_ide}
    Finish Project Creation
    Open Project In Target IDE    ${target_ide}

    Run CMake Workflow    ${build_folder}
