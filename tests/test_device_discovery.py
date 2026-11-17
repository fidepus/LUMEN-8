import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mac"))

from device_discovery import (  # noqa: E402
    IDENTIFY_REQUEST,
    PROTOCOL_VERSION,
    identify_controller,
    is_usb_serial_port,
    matches_usb_filters,
    parse_identity_response,
)


class IdentityResponseTests(unittest.TestCase):
    def test_parses_supported_response(self):
        identity = parse_identity_response("LUMEN8:HELLO:1:0.6.0\r\n")

        self.assertIsNotNone(identity)
        self.assertEqual(identity.protocol_version, PROTOCOL_VERSION)
        self.assertEqual(identity.firmware_version, "0.6.0")

    def test_parses_bytes_response(self):
        identity = parse_identity_response(b"LUMEN8:HELLO:1:0.6.0\n")
        self.assertEqual(identity.firmware_version, "0.6.0")

    def test_rejects_unrelated_or_malformed_lines(self):
        invalid_lines = (
            "",
            "OK",
            "LUMEN8:HELLO",
            "OTHER:HELLO:1:0.6.0",
            "LUMEN8:IDENTIFY?:1:0.6.0",
            "LUMEN8:HELLO:not-a-number:0.6.0",
            "LUMEN8:HELLO:1:",
            "LUMEN8:HELLO:1:bad version",
            b"\xff\xfe",
        )
        for line in invalid_lines:
            with self.subTest(line=line):
                self.assertIsNone(parse_identity_response(line))

    def test_rejects_unsupported_protocol_version(self):
        self.assertIsNone(parse_identity_response("LUMEN8:HELLO:2:0.7.0"))


class UsbCandidateTests(unittest.TestCase):
    def test_accepts_usb_device_without_known_vendor_or_product(self):
        port = SimpleNamespace(vid=0x2341, pid=0x8036, serial_number=None)
        self.assertTrue(is_usb_serial_port(port))
        self.assertTrue(matches_usb_filters(port, {}))

    def test_rejects_non_usb_serial_port(self):
        port = SimpleNamespace(vid=None, pid=None, serial_number=None)
        self.assertFalse(is_usb_serial_port(port))

    def test_optional_filters_can_restrict_scan(self):
        port = SimpleNamespace(vid=0x2341, pid=0x8036, serial_number="ABC123")
        self.assertTrue(matches_usb_filters(port, {"vendor_id": "0x2341"}))
        self.assertTrue(matches_usb_filters(port, {"product_id": 32822}))
        self.assertTrue(matches_usb_filters(port, {"serial_number": "ABC123"}))
        self.assertFalse(matches_usb_filters(port, {"vendor_id": "0x1A86"}))
        self.assertFalse(matches_usb_filters(port, {"serial_number": "OTHER"}))


class IdentifyRequestTests(unittest.TestCase):
    def test_sends_minimal_request_and_accepts_valid_hello(self):
        connection = Mock()
        connection.readline.return_value = b"LUMEN8:HELLO:1:0.6.0\n"

        identity = identify_controller(connection, attempts=1)

        self.assertEqual(identity.firmware_version, "0.6.0")
        connection.write.assert_called_once_with(IDENTIFY_REQUEST)
        connection.flush.assert_called_once()
        connection.reset_input_buffer.assert_called_once()

    def test_retries_when_first_response_is_not_lumen8(self):
        connection = Mock()
        connection.readline.side_effect = [
            b"unrelated serial output\n",
            b"LUMEN8:HELLO:1:0.6.0\n",
        ]

        identity = identify_controller(connection, attempts=2, retry_delay=0)

        self.assertEqual(identity.firmware_version, "0.6.0")
        self.assertEqual(connection.write.call_count, 2)


if __name__ == "__main__":
    unittest.main()
