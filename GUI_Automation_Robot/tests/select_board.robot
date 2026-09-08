*** Settings ***
Library    ../library/StudioLibrary.py


*** Variables ***
${BOARD}          2601B
${APPLICATION}    AI/ML - SoC Blink EFR32
${TARGET_IDE}     VS Code (LLVM)


*** Tasks ***
Create Machine Learning Application
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