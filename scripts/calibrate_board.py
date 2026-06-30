#!/usr/bin/env python
"""Calibrate the board -> robot transform (HARDWARE; run once after setup).

Disables the arm's torque so you can move the gripper by hand. For each corner
square: rest the gripper tip on the CENTER of that square, then press ENTER to
record. You control the timing — take as long as you need. The script shows the
live position and how far it is from the previous corner, and refuses to record a
point that's too close to the last one (which would mean the arm hadn't moved).

    python scripts/calibrate_board.py

Touch all four corners (a1, h1, a8, h8) — they're ~30 cm apart, so the arm is in
a very different pose at each. It then fits a transform and prints YAML for
config/board.local.yaml (and saves the raw points to outputs/).
"""
from __future__ import annotations

import select
import sys

import numpy as np

from chessbot.arm import LeRobotArm
from chessbot.config import load
from chessbot.kinematics import BoardToRobot

REFERENCE_SQUARES = ["a1", "h1", "a8", "h8"]  # the four corners span the board well
MIN_GAP_M = 0.05  # refuse a corner within 5 cm of the previous one (arm hadn't moved)


def _dist(a, b) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def capture(arm: LeRobotArm, square: str, prev: tuple[float, float] | None) -> tuple[float, float]:
    """Show live position; record on ENTER. Rejects points too close to `prev`."""
    print(f"\nRest the gripper tip on the CENTER of {square}, then press ENTER.")
    while True:
        x, y = arm.ee_xy()
        note = f"  ({_dist((x, y), prev) * 100:.0f} cm from last)" if prev else ""
        print(f"   {square}: ({x:+.3f}, {y:+.3f}){note}      ", end="\r", flush=True)
        if select.select([sys.stdin], [], [], 0.2)[0]:
            sys.stdin.readline()
            if prev and _dist((x, y), prev) < MIN_GAP_M:
                print(f"\n   only {_dist((x, y), prev) * 100:.0f} cm from the last corner — "
                      "move to the real corner and press ENTER again.")
                continue
            print(f"\n   recorded {square}: ({x:+.3f}, {y:+.3f})")
            return (float(x), float(y))


def main() -> None:
    settings = load()
    geo = settings.geometry
    a = settings.arm
    if a.follower_port == "TODO" or a.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")

    arm = LeRobotArm(port=a.follower_port, urdf_path=a.urdf_path, robot_id=a.robot_id)
    arm.connect()
    arm.relax()
    print("Torque off — move the arm by hand. Take your time; press ENTER at each corner.")

    board_pts, robot_pts = [], []
    prev: tuple[float, float] | None = None
    try:
        for sq in REFERENCE_SQUARES:
            pt = capture(arm, sq, prev)
            board_pts.append(geo.square_center(sq))
            robot_pts.append(pt)
            prev = pt
    finally:
        arm.disconnect()

    pts = np.array(robot_pts)
    span = max(_dist(p, q) for p in pts for q in pts)
    t = BoardToRobot.from_correspondences(board_pts, robot_pts)

    import json
    import os
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/last_calibration.json", "w") as f:
        json.dump({
            "squares": REFERENCE_SQUARES,
            "board_pts": [list(p) for p in board_pts],
            "robot_pts": [list(p) for p in robot_pts],
            "span_cm": round(span * 100, 2),
            "scale": round(t.scale, 6),
            "theta_rad": round(t.theta_rad, 6),
            "offset": [round(float(t.offset[0]), 6), round(float(t.offset[1]), 6)],
        }, f, indent=2)

    print(f"\nRecorded-point spread: {span * 100:.1f} cm  (expect ~40 cm corner-to-corner).")
    print("(raw points saved to outputs/last_calibration.json)")
    if span < 0.10 or not (0.5 <= t.scale <= 2.0):
        print(f"\n⚠️  These look WRONG (scale {t.scale:.3f}, spread {span * 100:.1f} cm).")
        print("    The corners came out clustered — re-run, touching four distinct corners.")
        return

    print("\n--- paste into config/board.local.yaml ---\n")
    print("transform:")
    print(f"  scale: {t.scale:.6f}")
    print(f"  theta_rad: {t.theta_rad:.6f}")
    print(f"  flip: {int(t.flip)}")
    print(f"  offset: [{t.offset[0]:.6f}, {t.offset[1]:.6f}]")


if __name__ == "__main__":
    main()
