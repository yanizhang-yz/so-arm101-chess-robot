#!/usr/bin/env python
"""Find your SO-ARM101 follower's serial port. Thin wrapper over LeRobot's CLI.

    python scripts/find_port.py        # runs `lerobot-find-port`

Then put the printed /dev/tty.usbmodem... into config/board.local.yaml as
arm.follower_port. (Run from a shell that has the lerobot venv active.)
"""
from __future__ import annotations

import subprocess
import sys


def main() -> None:
    try:
        subprocess.run(["lerobot-find-port"], check=True)
    except FileNotFoundError:
        sys.exit("lerobot-find-port not found — activate your lerobot venv first (see README).")


if __name__ == "__main__":
    main()
