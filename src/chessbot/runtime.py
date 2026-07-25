"""Construct the arm + motion stack from Settings.

Shared by the CLIs so the "MockArm vs. real arm" decision lives in exactly one
place. This is the only spot, besides arm.py, that knows LeRobotArm exists — and
it imports it lazily, so nothing here drags in lerobot unless --hardware is used.
"""
from __future__ import annotations

import numpy as np

from .arm import ArmBackend, MockArm
from .config import Settings
from .motion import ChessMotion


def _validate_hardware_transform(transform) -> None:
    fields = [transform.offset]
    fields.extend(
        value
        for value in (transform.warp_x, transform.warp_y, transform.warp_box)
        if value is not None
    )
    scalars = np.array([transform.scale, transform.theta_rad, transform.flip])
    if not np.all(np.isfinite(scalars)) or any(
        not np.all(np.isfinite(field)) for field in fields
    ):
        raise ValueError("board transform must contain only finite values")
    if transform.scale <= 0:
        raise ValueError("board transform scale must be positive")
    if transform.flip not in (-1.0, 1.0):
        raise ValueError("board transform flip must be +1 or -1")
    if (transform.warp_x is None) != (transform.warp_y is None):
        raise ValueError("board transform warp_x and warp_y must be configured together")
    if transform.warp_box is not None and transform.warp_x is None:
        raise ValueError("board transform warp_box requires warp_x and warp_y")
    if transform.warp_box is not None and (
        transform.warp_box[2] <= transform.warp_box[0]
        or transform.warp_box[3] <= transform.warp_box[1]
    ):
        raise ValueError("board transform warp_box must have positive width and height")
    if (
        transform.scale == 1.0
        and transform.theta_rad == 0.0
        and transform.flip == 1.0
        and np.array_equal(transform.offset, np.zeros(2))
        and transform.warp_x is None
        and transform.warp_y is None
        and transform.warp_box is None
    ):
        raise ValueError(
            "board transform is still the unseeded default; calibrate it before hardware use"
        )


def build_arm(settings: Settings, *, hardware: bool) -> ArmBackend:
    if not hardware:
        return MockArm()
    a = settings.arm
    if a.follower_port == "TODO" or a.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")
    _validate_hardware_transform(settings.transform)
    from .arm import LeRobotArm  # lazy: only import lerobot for real hardware
    return LeRobotArm(port=a.follower_port, urdf_path=a.urdf_path, robot_id=a.robot_id,
                      gripper_open=a.gripper_open, gripper_closed=a.gripper_closed)


def build_motion(settings: Settings, *, hardware: bool) -> ChessMotion:
    return ChessMotion(
        arm=build_arm(settings, hardware=hardware),
        geometry=settings.geometry,
        transform=settings.transform,
        heights=settings.heights,
        pieces=settings.pieces,
        offboard=settings.offboard,
    )
