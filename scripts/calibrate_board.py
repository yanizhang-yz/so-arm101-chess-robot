#!/usr/bin/env python
"""Calibrate the board -> robot transform (HARDWARE; run once after setup).

Disables the arm's torque so you can gently move the gripper by hand. Place the
gripper tip exactly over the center of each prompted square, press ENTER, and it
records where that square sits in robot space (via forward kinematics). It then
fits a similarity transform and prints YAML to paste into config/board.local.yaml.

    python scripts/calibrate_board.py

Keep the arm powered, support its weight as you move it, and go slowly.
"""
from __future__ import annotations

from chessbot.arm import LeRobotArm
from chessbot.config import load
from chessbot.kinematics import BoardToRobot

REFERENCE_SQUARES = ["a1", "h1", "a8", "h8"]  # the four corners span the board well


def main() -> None:
    settings = load()
    geo = settings.geometry
    a = settings.arm
    if a.follower_port == "TODO" or a.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")

    arm = LeRobotArm(port=a.follower_port, urdf_path=a.urdf_path, robot_id=a.robot_id)
    arm.connect()
    arm.relax()
    print("Torque off — you can move the arm by hand.\n")

    board_pts, robot_pts = [], []
    try:
        for sq in REFERENCE_SQUARES:
            input(f"Place the gripper tip on the CENTER of {sq}, then press ENTER...")
            board_pts.append(geo.square_center(sq))
            robot_pts.append(arm.ee_xy())
            print(f"  recorded {sq}: board={board_pts[-1]} robot={robot_pts[-1]}")
    finally:
        arm.disconnect()

    t = BoardToRobot.from_correspondences(board_pts, robot_pts)
    print("\n--- paste into config/board.local.yaml ---\n")
    print("transform:")
    print(f"  scale: {t.scale:.6f}")
    print(f"  theta_rad: {t.theta_rad:.6f}")
    print(f"  offset: [{t.offset[0]:.6f}, {t.offset[1]:.6f}]")


if __name__ == "__main__":
    main()
