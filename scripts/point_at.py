#!/usr/bin/env python
"""Point the arm at a square (HARDWARE): hover well above it, hold, tuck home.

The quickest way to answer "which physical square is e2?" — or to sanity-check
the calibration square by square. No descent, no grabbing; it stays about a
hand's width above the board, so it's safe even over a full board.

    python scripts/point_at.py --square e2
    python scripts/point_at.py --square h8 --hold 15
"""
from __future__ import annotations

import argparse
import time

from chessbot.config import load
from chessbot.runtime import build_arm


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--square", required=True, help="square to point at, e.g. e2")
    p.add_argument("--hold", type=float, default=10.0, help="seconds to hover there (default 10)")
    p.add_argument("--config", help="path to a board.local.yaml")
    args = p.parse_args()

    s = load(args.config)
    x, y = (float(v) for v in s.transform.xy(s.geometry.square_center(args.square)))
    z = s.heights.table_z + s.pieces.grasp_z("P") + s.heights.hover
    print(f"{args.square} -> robot ({x:.3f}, {y:.3f}); hovering at z={z:.3f}")

    arm = build_arm(s, hardware=True)
    arm.connect()
    try:
        arm.goto(x, y, z)
        print(f"HOVERING over {args.square} — look now ({args.hold:.0f} s)...")
        time.sleep(args.hold)
        print("tucking home...")
        arm.home()
        time.sleep(1.5)
    except ConnectionError:
        print("\nThe motor bus stopped answering — power-cycle the arm and re-run.")
    finally:
        arm.disconnect()


if __name__ == "__main__":
    main()
