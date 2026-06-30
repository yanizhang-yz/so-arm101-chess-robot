#!/usr/bin/env python
"""Watch joint angles + gripper xy live while you move the arm by hand (HARDWARE).

A debugging aid for board calibration. With the arm limp, move the gripper across
the board and watch the numbers:
  - the joint degrees should change by tens of degrees, and
  - the gripper xy should change by roughly your board's width (~0.28 m for 4 cm
    squares) between opposite corners.
If they barely move while the arm physically does, the readings aren't tracking
(or the arm isn't actually limp).

    python scripts/joint_watch.py        # Ctrl-C to stop
"""
from __future__ import annotations

import time

from chessbot.config import load


def main() -> None:
    s = load()
    if s.arm.follower_port == "TODO" or s.arm.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")

    from chessbot.arm import LeRobotArm
    arm = LeRobotArm(port=s.arm.follower_port, urdf_path=s.arm.urdf_path, robot_id=s.arm.robot_id)
    arm.connect()
    arm.relax()
    print("Arm is limp — move the gripper around by hand. Ctrl-C to stop.\n")
    try:
        while True:
            q = arm._current_q()
            x, y, z = arm._ik.forward_xyz(q)
            joints = " ".join(f"{v:6.1f}" for v in q)
            print(f"joints(deg): {joints}   |   gripper xyz: ({x:+.3f}, {y:+.3f}, {z:+.3f})")
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        arm.disconnect()


if __name__ == "__main__":
    main()
