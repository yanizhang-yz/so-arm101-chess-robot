#!/usr/bin/env python
"""Calibrate the board -> robot transform (HARDWARE; run once after setup).

Disables the arm's torque so you can move the gripper by hand. For each corner
square, **hold the gripper on the corner with both hands and keep still** — it
records automatically once the reading holds steady (no key press, so you never
have to let go and let a limp arm sag). It then fits a similarity transform and
prints YAML for config/board.local.yaml.

    python scripts/calibrate_board.py

The four recorded points should be spread ~your board's size apart. The script
reports the spread and refuses to emit values if the corners came out clustered.
"""
from __future__ import annotations

import select
import sys

import numpy as np

from chessbot.arm import LeRobotArm
from chessbot.config import load
from chessbot.kinematics import BoardToRobot

REFERENCE_SQUARES = ["a1", "h1", "a8", "h8"]  # the four corners span the board well
STEADY_M = 0.004  # auto-record once xy jitter stays under 4 mm for ~1.6 s


def capture(arm: LeRobotArm, square: str) -> tuple[float, float]:
    """Show live gripper xy; record automatically when steady (or on ENTER)."""
    print(f"\nHold the gripper on the CENTER of {square} and keep still "
          "(auto-records when steady, or press ENTER).")
    recent: list[tuple[float, float]] = []
    while True:
        x, y = arm.ee_xy()
        recent = (recent + [(x, y)])[-8:]
        jitter = float(np.array(recent).std(axis=0).max()) if len(recent) == 8 else 9.9
        print(f"   {square}: ({x:+.3f}, {y:+.3f})   jitter {jitter * 1000:4.1f} mm   ",
              end="\r", flush=True)
        forced = bool(select.select([sys.stdin], [], [], 0.2)[0])
        if forced:
            sys.stdin.readline()
        if jitter < STEADY_M or forced:
            print(f"\n   recorded {square}: ({x:+.3f}, {y:+.3f})")
            return float(x), float(y)


def main() -> None:
    settings = load()
    geo = settings.geometry
    a = settings.arm
    if a.follower_port == "TODO" or a.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")

    arm = LeRobotArm(port=a.follower_port, urdf_path=a.urdf_path, robot_id=a.robot_id)
    arm.connect()
    arm.relax()
    print("Torque off — move the arm by hand. Hold each corner steady; it captures itself.")

    board_pts, robot_pts = [], []
    try:
        for sq in REFERENCE_SQUARES:
            board_pts.append(geo.square_center(sq))
            robot_pts.append(capture(arm, sq))
    finally:
        arm.disconnect()

    pts = np.array(robot_pts)
    span = max(float(np.linalg.norm(p - q)) for p in pts for q in pts)
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
        print("    The corners came out clustered. Hold each corner steadier/longer and")
        print("    re-run — not pasting these, they'd send the arm to the wrong place.")
        return

    print("\n--- paste into config/board.local.yaml ---\n")
    print("transform:")
    print(f"  scale: {t.scale:.6f}")
    print(f"  theta_rad: {t.theta_rad:.6f}")
    print(f"  offset: [{t.offset[0]:.6f}, {t.offset[1]:.6f}]")


if __name__ == "__main__":
    main()
