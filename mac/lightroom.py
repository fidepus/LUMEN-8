
# LUMEN-8 – Lightroom API Steuerung

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from config import (
    API_URL,
    API_TIMEOUT,
    PARAMETERS,
    DEFAULT_PARAMETER,
)


selected_parameter = DEFAULT_PARAMETER


def select(parameter: str):
    """Wählt einen aktivierten Lightroom-Parameter aus."""
    global selected_parameter

    if parameter not in PARAMETERS:
        raise ValueError(f"Unbekannter Parameter: {parameter}")

    if not PARAMETERS[parameter].get("enabled", True):
        print(f"{parameter} ist deaktiviert.")
        return

    selected_parameter = parameter
    print(f"Ausgewählt: {PARAMETERS[parameter]['label']}")


def adjust(parameter: str, direction: int):
    """Verändert einen Parameter um einen definierten Schritt."""

    if parameter not in PARAMETERS:
        raise ValueError(f"Unbekannter Parameter: {parameter}")

    if direction not in (-1, 1):
        raise ValueError("Richtung muss -1 oder 1 sein.")

    settings = PARAMETERS[parameter]

    if not settings.get("enabled", True):
        print(f"{settings['label']} ist deaktiviert.")
        return

    action = "increment" if direction > 0 else "decrement"
    amount = settings["step"]

    query = urlencode({"amount": amount})
    url = (
        f"{API_URL}/{settings['api_name']}/"
        f"{action}?{query}"
    )

    try:
        with urlopen(url, timeout=API_TIMEOUT) as response:
            print(
                f"{settings['label']}: "
                f"{'+' if direction > 0 else '-'}{amount} "
                f"(HTTP {response.status})"
            )

    except HTTPError as error:
        print(f"HTTP-Fehler: {error.code}")

    except URLError as error:
        print(f"Verbindungsfehler: {error.reason}")


def adjust_selected(direction: int):
    """Verändert den aktuell ausgewählten Parameter."""
    adjust(selected_parameter, direction)


if __name__ == "__main__":
    print("LUMEN-8 gestartet.")
    print(f"Aktueller Parameter: {PARAMETERS[selected_parameter]['label']}")
    adjust_selected(1)
