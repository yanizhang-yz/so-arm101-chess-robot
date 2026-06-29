#!/usr/bin/env python
"""Find good gripper_open / gripper_closed values (HARDWARE).

The gripper is a single position 0-100 (set when you sweep it during
`lerobot-calibrate`). Which end is "open" vs. "closed" depends on your build, so
this tool lets you send values and watch. It holds the arm still; only the
gripper moves.

    python scripts/gripper_test.py

Type a number 0-100 to move the gripper; put a chess piece in the jaws to feel
the grip. Note the value that opens wide enough to clear a piece (-> gripper_open)
and the value that holds a piece firmly without straining (-> gripper_closed),
then put both in config/board.local.yaml. Type q to quit.
"""
from __future__ import annotations

from chessbot.config import load


def main() -> None:
    s = load()
    if s.arm.follower_port == "TODO":
        raise SystemExit("Set arm.follower_port in config/board.local.yaml first.")

    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    robot = SO101Follower(
        SO101FollowerConfig(port=s.arm.follower_port, id=s.arm.robot_id, use_degrees=True)
    )
    robot.connect()
    try:
        obs = robot.get_observation()
        print(f"current gripper.pos = {round(obs.get('gripper.pos', 0.0), 1)}")
        print("Type a value 0-100 (q to quit). Keep fingers clear of the jaws.")
        while True:
            raw = input("gripper > ").strip().lower()
            if raw in ("q", "quit", "exit"):
                break
            try:
                value = max(0.0, min(100.0, float(raw)))
            except ValueError:
                print("  enter a number 0-100, or q")
                continue
            obs = robot.get_observation()
            action = {k: v for k, v in obs.items() if k.endswith(".pos")}  # hold the pose
            action["gripper.pos"] = value
            robot.send_action(action)
            print(f"  sent gripper.pos = {value}")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
