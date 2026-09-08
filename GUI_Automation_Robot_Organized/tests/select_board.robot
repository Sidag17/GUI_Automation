*** Settings ***
Resource    ../resources/studio_workflows.resource


*** Variables ***
${BOARD}          2601B
${APPLICATION}    AI/ML - SoC Blink EFR32
${TARGET_IDE}     CMake (GCC/IAR/LLVM)
${BUILD_FOLDER}   cmake_gcc


*** Tasks ***
Create And Build Application
    Create And Build Studio Application
    ...    ${BOARD}
    ...    ${APPLICATION}
    ...    ${TARGET_IDE}
    ...    ${BUILD_FOLDER}
