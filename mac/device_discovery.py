"""
LUMEN-8 USB identity protocol.

This is deliberately separate from configuration provisioning. The host sends
one short ASCII request and the firmware answers with its protocol and firmware
versions. No settings are transferred during identification.
"""

import time
from dataclasses import dataclass
from typing import Optional, Union


IDENTIFY_REQUEST = b"LUMEN8:IDENTIFY?\n"
PROTOCOL_VERSION = 1
DEFAULT_PROBE_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 0.12


@dataclass(frozen=True)
class ControllerIdentity:
    protocol_version: int
    firmware_version: str


def parse_identity_response(raw_line: Union[str, bytes]) -> Optional[ControllerIdentity]:
    """Parse a LUMEN-8 HELLO response; return None for unrelated/unsupported data."""

    if isinstance(raw_line, bytes):
        try:
            line = raw_line.decode("ascii")
        except UnicodeDecodeError:
            return None
    else:
        line = raw_line

    parts = line.strip().split(":")
    if len(parts) != 4 or parts[0] != "LUMEN8" or parts[1] != "HELLO":
        return None

    try:
        protocol_version = int(parts[2])
    except ValueError:
        return None

    firmware_version = parts[3]
    if protocol_version != PROTOCOL_VERSION:
        return None
    if not firmware_version or len(firmware_version) > 32:
        return None
    if not all(character.isalnum() or character in ".-_+" for character in firmware_version):
        return None

    return ControllerIdentity(
        protocol_version=protocol_version,
        firmware_version=firmware_version,
    )


def is_usb_serial_port(port_info) -> bool:
    """Accept USB serial ports regardless of their VID/PID values."""

    return (
        getattr(port_info, "vid", None) is not None
        and getattr(port_info, "pid", None) is not None
    )


def _normalize_usb_id(value):
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def matches_usb_filters(port_info, usb_config: dict) -> bool:
    """
    Apply optional user-specified USB filters.

    Empty filters do not restrict discovery. These values are hints only;
    a successful LUMEN-8 protocol response is still required.
    """

    filters = (
        ("vendor_id", "vid"),
        ("product_id", "pid"),
        ("serial_number", "serial_number"),
    )

    for config_key, port_attribute in filters:
        expected = usb_config.get(config_key)
        if expected is None:
            continue

        actual = getattr(port_info, port_attribute, None)
        if config_key in ("vendor_id", "product_id"):
            expected = _normalize_usb_id(expected)
            if expected is None or actual != expected:
                return False
        elif actual != expected:
            return False

    return True


def prepare_serial_connection(connection, port_name: str):
    """Open a CDC serial port with DTR asserted and RTS inactive.

    Native USB CDC implementations such as the ATmega32U4 Arduino core only
    transmit from ``Serial`` while the host has an active control-line state.
    Keeping DTR low lets the board receive requests but can silently discard
    its identity response.
    """

    connection.rts = False
    connection.dtr = True
    connection.port = port_name
    connection.open()
    return connection


def identify_controller(
    connection,
    attempts: int = DEFAULT_PROBE_ATTEMPTS,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Optional[ControllerIdentity]:
    """Probe an already-open serial connection with the minimal identify request."""

    try:
        connection.reset_input_buffer()
    except (AttributeError, OSError):
        # Some serial-like implementations do not expose an input-buffer reset.
        pass

    for attempt in range(attempts):
        connection.write(IDENTIFY_REQUEST)
        connection.flush()

        response = parse_identity_response(connection.readline())
        if response is not None:
            return response

        if attempt + 1 < attempts and retry_delay > 0:
            time.sleep(retry_delay)

    return None
