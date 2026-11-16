
# ============================================================
# LUMEN-8
# Lightroom Utility for Manual Editing: 8 Controls
#
# Mac Bridge
# Version: 0.5.0
#
# Operating modes:
#   --simulate       Read JSON input from the terminal
#   --serial PORT    Connect to a specific serial port
#   --auto           Automatically discover and reconnect
# ============================================================

import argparse
import json
import time

import serial
from serial.tools import list_ports

from lightroom import select, adjust_selected
from config import (
    USB_CONFIG,
    PARAMETERS,
    DEFAULT_PARAMETER
)
from logger import logger


# ------------------------------------------------------------
# Serial protocol
# ------------------------------------------------------------

# Configuration is provisioned into firmware before installation.
# Runtime USB communication carries input events only.


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
# USB device discovery
# ------------------------------------------------------------

def find_controller_port():
    """
    Find the controller using configured USB identifiers.

    No port is selected unless at least one identifier
    has been configured.
    """

    vendor_id = USB_CONFIG.get("vendor_id")
    product_id = USB_CONFIG.get("product_id")
    serial_number = USB_CONFIG.get("serial_number")

    if (
        vendor_id is None
        and product_id is None
        and serial_number is None
    ):
        return None

    for port in list_ports.comports():

        if vendor_id is not None and port.vid != vendor_id:
            continue

        if product_id is not None and port.pid != product_id:
            continue

        if (
            serial_number is not None
            and port.serial_number != serial_number
        ):
            continue

        return port.device

    return None


# ------------------------------------------------------------
# Serial connection
# ------------------------------------------------------------

def read_serial_connection(port_name: str):
    """
    Open one serial connection, perform the handshake
    and process incoming controller messages.
    """

    baud_rate = USB_CONFIG["baud_rate"]

    with serial.Serial(
        port=port_name,
        baudrate=baud_rate,
        timeout=1,
        write_timeout=2
    ) as connection:

        logger.info(f"LUMEN-8 connected on {port_name}.")

        # Opening the USB serial port may reset the Pro Micro.
        # Allow its firmware to finish starting before processing events.
        time.sleep(2)
        logger.info("LUMEN-8 is ready.")

        while True:

            raw_line = connection.readline()

            if not raw_line:
                continue

            try:
                line = raw_line.decode("utf-8").strip()

                if line:
                    logger.debug(f"Received: {line}")
                    process_line(line)

            except UnicodeDecodeError:
                logger.warning("Received invalid serial data.")


def run_serial(port_name: str):
    """Connect to a fixed port and retry if the connection fails."""

    reconnect_interval = USB_CONFIG["reconnect_interval"]

    logger.info(f"Serial mode started on {port_name}.")

    try:
        while True:

            try:
                read_serial_connection(port_name)

            except serial.SerialException as error:

                logger.warning(f"Serial connection lost: {error}")

                logger.info(
                    f"Retrying connection in {reconnect_interval} seconds."
                )

                time.sleep(reconnect_interval)

    except KeyboardInterrupt:
        logger.info("Serial mode stopped.")


# ------------------------------------------------------------
# Automatic USB discovery and reconnection
# ------------------------------------------------------------

def run_auto():
    """
    Automatically discover the controller and reconnect.

    After a connection failure, the port is searched again.
    This also handles devices that reappear under a new port name.
    """

    reconnect_interval = USB_CONFIG["reconnect_interval"]
    waiting_logged = False

    logger.info("Automatic USB discovery started.")

    try:
        while True:

            port_name = find_controller_port()

            if port_name is None:

                if not waiting_logged:
                    logger.info("Waiting for LUMEN-8 controller.")

                logger.debug("No matching USB controller found.")

                waiting_logged = True

                time.sleep(reconnect_interval)
                continue

            waiting_logged = False

            logger.info(f"Controller discovered: {port_name}.")

            try:
                read_serial_connection(port_name)

            except serial.SerialException as error:

                logger.warning(f"USB connection interrupted: {error}")
                logger.info("Searching for controller again.")

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
        help="Read JSON input from the terminal"
    )

    mode.add_argument(
        "--serial",
        metavar="PORT",
        help="Connect to a specific serial port"
    )

    mode.add_argument(
        "--auto",
        action="store_true",
        help="Automatically discover the USB controller"
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
