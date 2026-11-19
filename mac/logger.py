
# ============================================================
# LUMEN-8
# Lightroom Utility for Manual Editing: 8 Controls
#
# Logging configuration
# ============================================================

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = Path(os.environ.get("LUMEN8_LOG_DIR", PROJECT_ROOT / "logs")).expanduser()
LOG_FILE = LOG_DIR / "lumen8.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("lumen8")
logger.setLevel(logging.DEBUG)
logger.propagate = False

if not logger.handlers:
    # Detailed log file with automatic rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    if not os.environ.get("LUMEN8_LOG_DIR"):
        # Interactive runs also get concise terminal output. LaunchAgent runs
        # rely on the rotating file so launchd does not create a second,
        # unbounded copy of every log entry.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
