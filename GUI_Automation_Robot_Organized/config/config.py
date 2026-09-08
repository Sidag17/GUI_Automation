import os

STUDIO_EXE = os.getenv(
    "SIMPLICITY_STUDIO_EXE",
    r"C:\Users\siagrawa\.silabs\slt\installs\archive\v6-base-v6.2.1-289\SimplicityStudio-6\studio.exe",
)

STUDIO_TITLE_REGEX = os.getenv(
    "SIMPLICITY_STUDIO_TITLE_REGEX",
    r"^Simplicity Studio.*",
)

STUDIO_START_TIMEOUT = int(os.getenv("STUDIO_START_TIMEOUT", "120"))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "60"))
BOARD_SEARCH_TIMEOUT = int(os.getenv("BOARD_SEARCH_TIMEOUT", "60"))
