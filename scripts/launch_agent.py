#!/usr/bin/env python3
"""Install or remove the LUMEN-8 bridge LaunchAgent."""

import argparse
import os
import plistlib
import shutil
import subprocess
from pathlib import Path
from typing import Optional


LABEL = "org.lumen8.bridge"


def make_plist(root: Path, python: Path, log_dir: Path) -> dict:
    bridge = root / "mac" / "bridge.py"
    search_path = [str(python.parent), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"]
    return {
        "Label": LABEL,
        "ProgramArguments": [str(python), str(bridge), "--auto"],
        "WorkingDirectory": str(root),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "EnvironmentVariables": {
            "LUMEN8_LOG_DIR": str(log_dir),
            "PATH": ":".join(search_path),
            "PYTHONUNBUFFERED": "1",
        },
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": str(log_dir / "launch-agent-error.log"),
    }


def launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/bin/launchctl", *args],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def find_python(root: Path, requested: Optional[Path] = None) -> Path:
    candidates = [requested] if requested else []
    candidates += [
        root / ".venv" / "bin" / "python3",
        root / ".venv" / "bin" / "python",
    ]
    candidates += [Path(value) for value in [
        shutil.which("python3"),
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        "/usr/bin/python3",
    ] if value]
    seen = set()
    for candidate in candidates:
        if candidate is None:
            continue
        # Keep virtualenv interpreter symlinks intact: resolving the symlink
        # points at the base interpreter and drops the venv's site-packages.
        candidate = candidate.expanduser().absolute()
        if candidate in seen or not os.access(candidate, os.X_OK):
            continue
        seen.add(candidate)
        result = subprocess.run(
            [str(candidate), "-c", "import serial"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return candidate
    raise SystemExit(
        "Could not find Python 3 with pyserial. Set up the repository .venv first: "
        "python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    )


def install(args: argparse.Namespace) -> None:
    root = args.root.expanduser().resolve()
    if not (root / "mac" / "bridge.py").is_file():
        raise SystemExit(f"LUMEN-8 bridge not found in {root}")
    python = find_python(root, args.python)

    agent_dir = Path.home() / "Library" / "LaunchAgents"
    log_dir = Path.home() / "Library" / "Logs" / "LUMEN-8"
    agent_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = agent_dir / f"{LABEL}.plist"
    temporary = target.with_suffix(".plist.tmp")
    with temporary.open("wb") as output:
        plistlib.dump(make_plist(root, python, log_dir), output, sort_keys=True)
    temporary.replace(target)

    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{LABEL}"
    if launchctl("print", service).returncode == 0:
        result = launchctl("bootout", service)
        if result.returncode:
            raise SystemExit(f"Could not stop existing {LABEL}: {result.stderr.strip()}")
    result = launchctl("bootstrap", domain, str(target))
    if result.returncode:
        detail = result.stderr.strip() or f"status {result.returncode}"
        raise SystemExit(f"launchctl bootstrap failed ({detail}); plist saved at {target}")
    print(f"Installed and started {LABEL} with {python}: {target}")


def uninstall(_args: argparse.Namespace) -> None:
    target = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    service = f"gui/{os.getuid()}/{LABEL}"
    if launchctl("print", service).returncode == 0:
        result = launchctl("bootout", service)
        if result.returncode:
            raise SystemExit(f"Could not stop {LABEL}: {result.stderr.strip()}")
    target.unlink(missing_ok=True)
    print(f"Removed {LABEL}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install_parser = commands.add_parser("install")
    install_parser.add_argument("--root", type=Path, required=True)
    install_parser.add_argument("--python", type=Path)
    install_parser.set_defaults(handler=install)
    remove_parser = commands.add_parser("uninstall")
    remove_parser.set_defaults(handler=uninstall)
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
