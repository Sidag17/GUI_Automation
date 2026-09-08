*** Settings ***
Library    ../library/StudioLibrary.py


*** Variables ***
${BOARD}          2601B
${APPLICATION}    AI/ML - SoC Blink EFR32
${TARGET_IDE}     CMake (GCC/IAR/LLVM)
${BUILD_FOLDER}   cmake_gcc


*** Tasks ***
Create And Build Application
    Open Studio
    Wait For Main Screen
    Maximize Studio
    Close Previous Tabs

    Open Devices
    Search Board    ${BOARD}
    Select Board    ${BOARD}

    Open Example Projects And Demos
    Search Application    ${APPLICATION}
    Create Production Application    ${APPLICATION}

    Select Target IDE    ${TARGET_IDE}
    Finish Project Creation

    Open Project In Target IDE    ${TARGET_IDE}
    Run CMake Workflow    ${BUILD_FOLDER}