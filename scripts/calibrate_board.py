#!/usr/bin/env python
"""Calibrate the board -> robot transform (HARDWARE; run once after setup).

Disables the arm's torque so you can move the gripper by hand. For each of the
four corner squares it shows the gripper's **live (x, y)** — move there, watch the
numbers change, and press ENTER (while holding the gripper on the corner) to
record. It then fits a similarity transform and prints YAML for
config/board.local.yaml.

    python scripts/calibrate_board.py

The four recorded points should be spread ~your board's size apart. If the live
xy barely changes as you move the arm, or it snaps back toward the middle when you
let go, the arm isn't staying put — hold it on each corner while you press ENTER.
"""
from __future__ import annotations

import select
import sys

import numpy as np

from chessbot.arm import LeRobotArm
from chessbot.config import load
from chessbot.kinematics import BoardToRobot

REFERENCE_SQUARES = ["a1", "h1", "a8", "h8"]  # the four corners span the board well


def capture(arm: LeRobotArm, square: str) -> tuple[float, float]:
    """Show live gripper xy until the user presses ENTER, then record that point."""
    print(f"\nHold the gripper on the CENTER of {square}; press ENTER to record.")
    x, y = arm.ee_xy()
    while True:
        x, y = arm.ee_xy()
        print(f"   live {square}: ({x:+.3f}, {y:+.3f})      ", end="\r", flush=True)
        if select.select([sys.stdin], [], [], 0.25)[0]:
            sys.stdin.readline()
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
    print("Torque off — move the arm by hand. The live xy below should change as you move it.")

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

    print(f"\nRecorded-point spread: {span * 100:.1f} cm  (expect ~40 cm corner-to-corner).")
    if span < 0.10 or not (0.5 <= t.scale <= 2.0):
        print(f"\n⚠️  These numbers look WRONG (scale {t.scale:.3f}, spread {span * 100:.1f} cm).")
        print("    The corners came out too close together — the arm didn't actually reach")
        print("    them (it likely drifted back to center). Run scripts/joint_watch.py to")
        print("    confirm the xy moves, hold each corner while pressing ENTER, and re-run.")
        print("    Not pasting these — they'd send the arm to the wrong place.")
        return

    print("\n--- paste into config/board.local.yaml ---\n")
    print("transform:")
    print(f"  scale: {t.scale:.6f}")
    print(f"  theta_rad: {t.theta_rad:.6f}")
    print(f"  offset: [{t.offset[0]:.6f}, {t.offset[1]:.6f}]")


if __name__ == "__main__":
    main()
