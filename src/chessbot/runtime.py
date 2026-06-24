"""Construct the arm + motion stack from Settings.

Shared by the CLIs so the "MockArm vs. real arm" decision lives in exactly one
place. This is the only spot, besides arm.py, that knows LeRobotArm exists — and
it imports it lazily, so nothing here drags in lerobot unless --hardware is used.
"""
from __future__ import annotations

from .arm import ArmBackend, MockArm
from .config import Settings
from .motion import ChessMotion


def build_arm(settings: Settings, *, hardware: bool) -> ArmBackend:
    if not hardware:
        return MockArm()
    from .arm import LeRobotArm  # lazy: only import lerobot for real hardware
    a = settings.arm
    if a.follower_port == "TODO" or a.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")
    return LeRobotArm(port=a.follower_port, urdf_path=a.urdf_path, robot_id=a.robot_id,
                      gripper_open=a.gripper_open, gripper_closed=a.gripper_closed)


def build_motion(settings: Settings, *, hardware: bool) -> ChessMotion:
    return ChessMotion(
        arm=build_arm(settings, hardware=hardware),
        geometry=settings.geometry,
        transform=settings.transform,
        heights=settings.heights,
        offboard=settings.offboard,
    )
