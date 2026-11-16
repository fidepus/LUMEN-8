
# ============================================================
# LUMEN-8
# Configuration loader
# ============================================================

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"

DEFAULT_CONFIG = CONFIG_DIR / "default.json"
USER_CONFIG = CONFIG_DIR / "user.json"


def merge_config(default: dict, override: dict) -> dict:
    """Recursively merge user settings into default settings."""

    result = default.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value

    return result


def load_config() -> dict:
    """Load default and user configuration."""

    with DEFAULT_CONFIG.open("r", encoding="utf-8") as file:
        defaults = json.load(file)

    if USER_CONFIG.exists():
        with USER_CONFIG.open("r", encoding="utf-8") as file:
            user_settings = json.load(file)
    else:
        user_settings = {}

    config = merge_config(defaults, user_settings)

    validate_config(config)

    return config


def validate_config(config: dict):
    """Validate configuration values."""

    api = config.get("api", {})
    controller = config.get("controller", {})
    usb = config.get("usb", {})
    parameters = controller.get("parameters", {})

    if not isinstance(api.get("url"), str) or not api["url"].strip():
        raise ValueError("Invalid API URL.")

    if not isinstance(api.get("timeout"), (int, float)):
        raise ValueError("Invalid API timeout.")

    if api["timeout"] <= 0:
        raise ValueError("API timeout must be positive.")

    if not parameters:
        raise ValueError("No controller parameters configured.")

    for name, settings in parameters.items():
        if not settings.get("api_name"):
            raise ValueError(f"{name}: Missing API name.")

        step = settings.get("step")

        if not isinstance(step, (int, float)) or isinstance(step, bool):
            raise ValueError(f"{name}: Invalid step size.")

        if step <= 0:
            raise ValueError(f"{name}: Step size must be positive.")

    default_parameter = controller.get("default_parameter")

    if default_parameter not in parameters:
        raise ValueError("Default parameter does not exist.")

    if not isinstance(usb.get("baud_rate"), int) or usb["baud_rate"] <= 0:
        raise ValueError("Invalid USB baud rate.")

    if (
        not isinstance(usb.get("reconnect_interval"), (int, float))
        or usb["reconnect_interval"] <= 0
    ):
        raise ValueError("Invalid USB reconnect interval.")


# Load configuration at import time
CONFIG = load_config()

API_URL = CONFIG["api"]["url"].rstrip("/")
API_TIMEOUT = CONFIG["api"]["timeout"]

PARAMETERS = CONFIG["controller"]["parameters"]
DEFAULT_PARAMETER = CONFIG["controller"]["default_parameter"]

USB_CONFIG = CONFIG["usb"]
