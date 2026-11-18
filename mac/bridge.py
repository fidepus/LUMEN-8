#!/usr/bin/env python3

# ============================================================
# LUMEN-8
# Lightroom Utility for Manual Editing: 8 Controls
#
# macOS Bridge
# Version: 0.6.0
#
# Operating modes:
#   --simulate       Read JSON input from the terminal
#   --serial PORT    Connect to a specific port (diagnostics)
#   --auto           Discover and reconnect automatically
# ============================================================

import argparse
import json
import time

import serial
from serial.tools import list_ports

from device_discovery import (
    identify_controller,
    is_usb_serial_port,
    matches_usb_filters,
    prepare_serial_connection,
)
from lightroom import select, adjust_selected
from config import USB_CONFIG
from logger import logger


# ------------------------------------------------------------
# Message handling
# ------------------------------------------------------------

def handle_message(message: dict):
    """Process a single controller message."""

    event = message.get("event")

    if event == "select":
        parameter = message.get("parameter")

        if not isinstance(parameter, str):
            logger.warning("Invalid parameter in select message.")
            return

        try:
            select(parameter)
            logger.info(f"Selected parameter: {parameter}")
        except ValueError as error:
            logger.warning(f"Could not select parameter: {error}")

    elif event == "delta":
        delta = message.get("delta")

        if type(delta) is not int or delta not in (-1, 1):
            logger.warning(f"Invalid encoder direction: {delta}")
            return

        logger.debug(f"Encoder movement: {delta:+d}")
        adjust_selected(delta)

    elif event == "press":
        control = message.get("control")
        logger.info(f"Button pressed: {control}")
        # Button actions will be implemented later.

    else:
        logger.warning(f"Unknown event: {event}")


def process_line(line: str):
    """Decode and process a single JSON line."""

    try:
        message = json.loads(line)
        if not isinstance(message, dict):
            logger.warning("Received message is not a JSON object.")
            return
        handle_message(message)
    except json.JSONDecodeError as error:
        logger.warning(f"Invalid JSON received: {error}")


# ------------------------------------------------------------
# Simulation mode
# ------------------------------------------------------------

def run_simulation():
    """Read test messages from the terminal."""

    logger.info("LUMEN-8 simulation mode started.")
    print("Enter JSON messages. Press Ctrl+C to exit.\n")

    try:
        while True:
            line = input("> ").strip()
            if line:
                process_line(line)
    except KeyboardInterrupt:
        logger.info("Simulation mode stopped.")


# ------------------------------------------------------------
# USB discovery and identification
# ------------------------------------------------------------

def open_serial_connection(port_name: str):
    """
    Open the native USB CDC serial connection required by the Pro Micro.

    DTR must be asserted for the ATmega32U4 CDC implementation to transmit the
    handshake response. RTS stays inactive.
    """

    connection = serial.Serial(
        port=None,
        baudrate=USB_CONFIG["baud_rate"],
        timeout=0.20,
        write_timeout=1,
    )
    return prepare_serial_connection(connection, port_name)


def probe_controller_port(port_name: str):
    """
    Open a candidate port and identify LUMEN-8 using the runtime protocol.

    Returns (open_connection, identity) on success, or None when the device
    does not answer as a supported LUMEN-8 controller.
    """

    connection = open_serial_connection(port_name)

    try:
        # Allow USB CDC enumeration/firmware startup to settle. DTR is held low.
        time.sleep(0.15)
        identity = identify_controller(connection)

        if identity is None:
            connection.close()
            return None

        return connection, identity

    except Exception:
        if connection.is_open:
            connection.close()
        raise


def configured_usb_port(port_info) -> bool:
    """Return whether a USB serial port passes optional user filters."""

    return (
        is_usb_serial_port(port_info)
        and matches_usb_filters(port_info, USB_CONFIG)
    )


def current_port_names():
    """Return the currently enumerated serial device names."""

    return {port.device for port in list_ports.comports()}


# ------------------------------------------------------------
# Serial event loop
# ------------------------------------------------------------

def read_serial_connection(connection, port_name: str, identity):
    """Process input events on an already identified, open controller."""

    logger.info(f"LUMEN-8 connected on {port_name}.")
    logger.info(
        "Controller identified: protocol v%s, firmware %s.",
        identity.protocol_version,
        identity.firmware_version,
    )
    logger.info("LUMEN-8 is ready.")

    last_port_check = time.monotonic()

    while True:
        raw_line = connection.readline()

        if not raw_line:
            # Some USB CDC drivers return an empty timeout instead of raising
            # when a device is unplugged. Check enumeration periodically.
            now = time.monotonic()
            if now - last_port_check >= 1.0:
                last_port_check = now
                if port_name not in current_port_names():
                    raise serial.SerialException(
                        f"USB device disappeared: {port_name}"
                    )
            continue

        try:
            line = raw_line.decode("utf-8").strip()
            if line:
                logger.debug(f"Received: {line}")
                process_line(line)
        except UnicodeDecodeError:
            logger.warning("Received invalid serial data.")


def close_connection(connection):
    if connection is not None and connection.is_open:
        connection.close()


def run_serial(port_name: str):
    """Connect to a manually specified port and retry on that same path."""

    reconnect_interval = USB_CONFIG["reconnect_interval"]
    logger.info(f"Fixed serial mode started on {port_name}.")

    try:
        while True:
            connection = None
            try:
                result = probe_controller_port(port_name)
                if result is None:
                    logger.warning(f"No supported LUMEN-8 response on {port_name}.")
                    time.sleep(reconnect_interval)
                    continue

                connection, identity = result
                read_serial_connection(connection, port_name, identity)

            except (serial.SerialException, OSError) as error:
                logger.warning(f"Serial connection interrupted: {error}")
                logger.info(
                    f"Retrying connection in {reconnect_interval} seconds."
                )
                time.sleep(reconnect_interval)
            finally:
                close_connection(connection)

    except KeyboardInterrupt:
        logger.info("Serial mode stopped.")


# ------------------------------------------------------------
# Automatic USB discovery and reconnection
# ------------------------------------------------------------

def run_auto():
    """
    Discover LUMEN-8 by protocol response, not by a fixed device-node name.

    Any USB serial device can be a candidate, regardless of its VID/PID or
    serial number. Optional values in config/default.json can narrow the scan,
    but a matching LUMEN-8 HELLO response is always required.
    """

    reconnect_interval = USB_CONFIG["reconnect_interval"]
    last_wait_message = None

    logger.info("Automatic LUMEN-8 USB discovery started.")

    try:
        while True:
            found_controller = False
            candidate_ports = []
            unidentified_ports = []

            for port_info in list_ports.comports():
                if not configured_usb_port(port_info):
                    continue

                port_name = port_info.device
                candidate_ports.append(port_name)
                logger.debug(
                    "Probing USB serial device %s (VID=%s, PID=%s).",
                    port_name,
                    port_info.vid,
                    port_info.pid,
                )

                connection = None
                try:
                    result = probe_controller_port(port_name)
                    if result is None:
                        unidentified_ports.append(port_name)
                        continue

                    connection, identity = result
                    found_controller = True
                    last_wait_message = None

                    try:
                        read_serial_connection(connection, port_name, identity)
                    except (serial.SerialException, OSError) as error:
                        logger.warning(f"USB connection interrupted: {error}")
                        logger.info("Searching for LUMEN-8 again.")
                    finally:
                        close_connection(connection)

                    # A connected controller disconnected; restart the scan.
                    break

                except (serial.SerialException, OSError) as error:
                    unidentified_ports.append(port_name)
                    logger.debug("Could not probe %s: %s", port_name, error)
                    close_connection(connection)

            if not found_controller:
                if not candidate_ports:
                    wait_message = (
                        "No USB serial candidates match the configured filters; "
                        "waiting for LUMEN-8 controller."
                    )
                elif unidentified_ports:
                    wait_message = (
                        "USB serial candidate(s) did not answer the LUMEN-8 "
                        "handshake: " + ", ".join(unidentified_ports)
                    )
                else:
                    wait_message = "Waiting for LUMEN-8 controller."

                if wait_message != last_wait_message:
                    logger.info(wait_message)
                    last_wait_message = wait_message

                time.sleep(reconnect_interval)

    except KeyboardInterrupt:
        logger.info("Automatic USB discovery stopped.")


# ------------------------------------------------------------
# Application entry point
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LUMEN-8 Lightroom Controller Bridge"
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--simulate",
        action="store_true",
        help="Read JSON input from the terminal",
    )
    mode.add_argument(
        "--serial",
        metavar="PORT",
        help="Connect to a specific serial port (diagnostics)",
    )
    mode.add_argument(
        "--auto",
        action="store_true",
        help="Identify LUMEN-8 on USB and reconnect automatically",
    )

    args = parser.parse_args()
    logger.info("LUMEN-8 Bridge started.")

    try:
        if args.simulate:
            run_simulation()
        elif args.serial:
            run_serial(args.serial)
        elif args.auto:
            run_auto()
    finally:
        logger.info("LUMEN-8 Bridge stopped.")


if __name__ == "__main__":
    main()
