"""Arm backends. Everything else talks to an ArmBackend; swap the implementation
to go from desk-checking logic to driving the real SO-ARM101.

  MockArm     records every motion to a log and prints it. No hardware, no
              heavy dependencies — what stage1_demo uses by default and what the
              tests exercise.
  LeRobotArm  drives a physical SO-ARM101 follower via LeRobot 0.5.x: a
              robot-frame goto() -> IK -> SOFollower.send_action(). The lerobot
              import is lazy, so importing this module never requires hardware.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class ArmBackend(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def goto(self, x: float, y: float, z: float) -> None: ...
    def set_gripper(self, open_: bool) -> None: ...
    def home(self) -> None: ...


@dataclass
class MockArm:
    """Offline stand-in: logs motions so you can verify the choreography by eye."""

    verbose: bool = True
    log: list[tuple] = field(default_factory=list)

    def connect(self) -> None:
        self._emit(("connect",))

    def disconnect(self) -> None:
        self._emit(("disconnect",))

    def goto(self, x: float, y: float, z: float) -> None:
        self._emit(("goto", round(x, 4), round(y, 4), round(z, 4)))

    def set_gripper(self, open_: bool) -> None:
        self._emit(("gripper", "open" if open_ else "close"))

    def home(self) -> None:
        self._emit(("home",))

    def _emit(self, entry: tuple) -> None:
        self.log.append(entry)
        if self.verbose:
            print("   arm:", " ".join(str(p) for p in entry))


@dataclass
class LeRobotArm:
    """Drive a physical SO-ARM101 follower via LeRobot 0.5.x.

    goto() takes a robot-frame (x, y, z) in meters, solves IK to joint degrees,
    and sends an absolute joint target. Simple point-to-point with a settle
    delay — fine for stage 1; add interpolation/speed shaping later.

    NOTE: gripper_open/closed and the home pose are setup-dependent — tune them
    on your arm. Keep movements slow and supervised (see README safety notes).
    """

    port: str
    urdf_path: str
    robot_id: str = "chessbot_follower"
    gripper_open: float = 60.0     # 0..100; tune after calibration
    gripper_closed: float = 10.0
    settle_s: float = 0.6

    def __post_init__(self) -> None:
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig  # lazy
        from .kinematics import IKSolver
        self._robot = SO101Follower(
            SO101FollowerConfig(port=self.port, id=self.robot_id, use_degrees=True)
        )
        self._ik = IKSolver(self.urdf_path)
        self._arm_motors = IKSolver.ARM_JOINTS
        self._gripper = self.gripper_open

    def connect(self) -> None:
        self._robot.connect()

    def disconnect(self) -> None:
        self._robot.disconnect()

    def _current_q(self):
        import numpy as np
        obs = self._robot.get_observation()
        return np.array([obs[f"{m}.pos"] for m in self._arm_motors], float)

    def goto(self, x: float, y: float, z: float) -> None:
        import time
        q = self._ik.joints_for((x, y, z), self._current_q())
        action = {f"{m}.pos": float(q[i]) for i, m in enumerate(self._arm_motors)}
        action["gripper.pos"] = self._gripper
        self._robot.send_action(action)
        time.sleep(self.settle_s)

    def set_gripper(self, open_: bool) -> None:
        import time
        self._gripper = self.gripper_open if open_ else self.gripper_closed
        obs = self._robot.get_observation()  # hold the arm still, only move the gripper
        action = {f"{m}.pos": obs[f"{m}.pos"] for m in self._arm_motors}
        action["gripper.pos"] = self._gripper
        self._robot.send_action(action)
        time.sleep(self.settle_s)

    def home(self) -> None:
        # A neutral, tucked pose. These joint angles are a starting guess — tune.
        self._robot.send_action({
            "shoulder_pan.pos": 0.0, "shoulder_lift.pos": -90.0, "elbow_flex.pos": 90.0,
            "wrist_flex.pos": 0.0, "wrist_roll.pos": 0.0, "gripper.pos": self._gripper,
        })

    # --- calibration helpers ------------------------------------------------
    def relax(self) -> None:
        """Disable torque so the arm can be moved by hand (board calibration)."""
        self._robot.bus.disable_torque()

    def ee_xy(self) -> tuple[float, float]:
        """Current end-effector (x, y) in the robot frame, via forward kinematics."""
        t = self._ik.kin.forward_kinematics(self._current_q())
        return float(t[0, 3]), float(t[1, 3])
