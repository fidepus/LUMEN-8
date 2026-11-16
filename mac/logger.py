
# ============================================================
# LUMEN-8
# Lightroom Utility for Manual Editing: 8 Controls
#
# Logging configuration
# ============================================================

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "lumen8.log"

LOG_DIR.mkdir(exist_ok=True)

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

    # Terminal output: important events only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
