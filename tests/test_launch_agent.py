import plistlib
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from launch_agent import LABEL, make_plist


class LaunchAgentPlistTests(unittest.TestCase):
    def test_bridge_runs_at_login_and_restarts_after_exit(self):
        root = Path("/project/LUMEN-8")
        python = Path("/project/LUMEN-8/.venv/bin/python3")
        log_dir = Path("/Users/example/Library/Logs/LUMEN-8")

        plist = plistlib.loads(plistlib.dumps(make_plist(root, python, log_dir)))

        self.assertEqual(plist["Label"], LABEL)
        self.assertEqual(
            plist["ProgramArguments"],
            [str(python), str(root / "mac/bridge.py"), "--auto"],
        )
        self.assertTrue(plist["RunAtLoad"])
        self.assertTrue(plist["KeepAlive"])
        self.assertEqual(plist["ThrottleInterval"], 10)
        self.assertEqual(plist["EnvironmentVariables"]["LUMEN8_LOG_DIR"], str(log_dir))

    def test_rotating_log_location_and_launchd_error_log(self):
        log_dir = Path("/Users/example/Library/Logs/LUMEN-8")
        plist = make_plist(
            Path("/project/LUMEN-8"),
            Path("/project/LUMEN-8/.venv/bin/python3"),
            log_dir,
        )

        self.assertEqual(plist["StandardOutPath"], "/dev/null")
        self.assertEqual(plist["StandardErrorPath"], str(log_dir / "launch-agent-error.log"))


if __name__ == "__main__":
    unittest.main()
