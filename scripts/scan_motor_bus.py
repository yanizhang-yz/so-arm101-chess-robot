#!/usr/bin/env python
"""Diagnose an SO-100/SO-101 Feetech motor bus.

Probes a serial port at every Feetech baudrate and reports which motor IDs
answer. Run this when lerobot-calibrate / lerobot-teleoperate fails with
"Missing motor IDs" / "Full found motor list: {}".

Usage (arm's DC power supply must be ON, not just USB):
    python scan_motor_bus.py /dev/tty.usbmodemXXXX
"""

import argparse
import sys

from lerobot.motors.feetech import FeetechMotorsBus

EXPECTED_IDS = {1, 2, 3, 4, 5, 6}  # SO-10x arm: 6x STS3215 (model number 777)
WORKING_BAUDRATE = 1_000_000       # what lerobot's so101 configs talk at


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("port", help="e.g. /dev/tty.usbmodem5B415325701 (from lerobot-find-port)")
    args = parser.parse_args()

    try:
        found = FeetechMotorsBus.scan_port(args.port)
    except Exception as e:
        print(f"\nCould not open/scan {args.port}: {e}")
        print("Is the USB cable plugged in, and the port name current? Re-check with lerobot-find-port.")
        return 2

    print(f"\nScan result (baudrate -> ids): {found if found else 'nothing answered at any baudrate'}")

    if set(found.get(WORKING_BAUDRATE, [])) == EXPECTED_IDS:
        print(
            "\nVERDICT: all 6 motors answer at 1 Mbps with the expected ids."
            "\nConfiguration is fine — do NOT run lerobot-setup-motors."
            "\nThe earlier failure was electrical/transient (power supply, loose 3-pin"
            "\ncable, USB hiccup). Re-run lerobot-calibrate now."
        )
        return 0

    if not found:
        print(
            "\nVERDICT: total silence on the bus -> electrical, not configuration."
            "\n  1. Is THIS arm's DC power supply plugged in and switched on?"
            "\n     (USB only powers the little controller board — lerobot-find-port"
            "\n     succeeding says nothing about servo power.)"
            "\n  2. Is it the right supply for this arm? Leader/follower bricks can differ."
            "\n  3. Re-seat the 3-pin cable from the controller board to the shoulder motor."
            "\n  4. Waveshare board: both jumpers on the B (USB) channel."
            "\nCaveat: a chain where every motor still has factory id 1 can also scan"
            "\nempty (replies collide). Confirm power first, then re-run this scan."
        )
        return 1

    print(
        "\nVERDICT: the bus is alive but the config does not match what lerobot"
        f"\nexpects (ids 1-6 at {WORKING_BAUDRATE:,} baud)."
        "\n  - ids 1-6 all present but at a DIFFERENT baudrate: fixable in software,"
        "\n    no unplugging — ask Claude for the baud-rewrite snippet."
        "\n  - only id 1 (or a partial/flickering set): motor ids were never assigned;"
        "\n    run lerobot-setup-motors one motor at a time. On an assembled arm you"
        "\n    only unplug 3-pin daisy-chain connectors — no disassembly."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
