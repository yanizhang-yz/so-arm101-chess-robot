"""Map board-plane coordinates into robot space, and (on hardware) solve IK.

Two stages, deliberately separated so the cheap, testable part runs anywhere:

  BoardToRobot   board-frame (x, y) in meters  ->  robot-frame (x, y)
                 a 2-D similarity transform (rotation + uniform scale +
                 translation) you calibrate once. Pure numpy: runs offline,
                 covered by tests. scripts/calibrate_board.py fits it from a
                 few squares whose robot-space location you measure.

  IKSolver       robot-frame pose (x, y, z) + grasp orientation -> joint degrees
                 thin wrapper over lerobot.model.kinematics.RobotKinematics
                 (placo). Imported lazily; only needed to drive the real arm.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class BoardToRobot:
    """robot_xy = scale * R(theta) @ board_xy + offset (z handled separately)."""

    scale: float = 1.0
    theta_rad: float = 0.0
    offset: np.ndarray | None = None  # shape (2,), meters

    def __post_init__(self) -> None:
        self.offset = np.zeros(2) if self.offset is None else np.asarray(self.offset, float).reshape(2)

    def xy(self, board_xy: tuple[float, float]) -> np.ndarray:
        c, s = math.cos(self.theta_rad), math.sin(self.theta_rad)
        r = np.array([[c, -s], [s, c]])
        return self.scale * (r @ np.asarray(board_xy, float)) + self.offset

    @classmethod
    def from_correspondences(
        cls, board_pts: list[tuple[float, float]], robot_pts: list[tuple[float, float]]
    ) -> "BoardToRobot":
        """Least-squares similarity fit from >=2 (board, robot) point pairs (Umeyama)."""
        b = np.asarray(board_pts, float)
        w = np.asarray(robot_pts, float)
        if b.shape != w.shape or len(b) < 2:
            raise ValueError("need matching board/robot point lists of length >= 2")
        bc, wc = b.mean(0), w.mean(0)
        bb, ww = b - bc, w - wc
        cov = (ww.T @ bb) / len(b)
        u, sv, vt = np.linalg.svd(cov)
        d = np.ones(2)
        if np.linalg.det(u @ vt) < 0:
            d[-1] = -1.0
        r = u @ np.diag(d) @ vt
        var_b = float((bb ** 2).sum() / len(b))
        scale = float((sv * d).sum() / var_b) if var_b > 0 else 1.0
        offset = wc - scale * (r @ bc)
        return cls(scale=scale, theta_rad=math.atan2(r[1, 0], r[0, 0]), offset=offset)


def default_grasp_orientation() -> np.ndarray:
    """A gripper-pointing-down rotation (tool +z aligned with world -z).

    IK runs with a low orientation weight, so this is a soft preference: the
    solver prioritizes reaching the (x, y, z) target. Tune to your URDF's
    gripper frame if grasps come in at an awkward angle.
    """
    return np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, -1.0]])


class IKSolver:
    """Wraps LeRobot's RobotKinematics; constructed lazily (needs lerobot + placo)."""

    ARM_JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]

    def __init__(self, urdf_path: str | Path, target_frame: str = "gripper_frame_link"):
        from lerobot.model.kinematics import RobotKinematics  # lazy: optional dep
        self.kin = RobotKinematics(str(urdf_path), target_frame_name=target_frame,
                                   joint_names=self.ARM_JOINTS)

    def joints_for(self, xyz, current_q_deg, orientation: np.ndarray | None = None) -> np.ndarray:
        """Solve IK for an end-effector position. Returns the 5 arm-joint degrees."""
        t = np.eye(4)
        t[:3, :3] = orientation if orientation is not None else default_grasp_orientation()
        t[:3, 3] = np.asarray(xyz, float)
        return self.kin.inverse_kinematics(np.asarray(current_q_deg, float), t)


def find_urdf() -> Path | None:
    """Best-effort locate an SO-101/SO-100 URDF shipped with the installed LeRobot.

    If this returns None, point config arm.urdf_path at your SO-ARM URDF (e.g.
    from the TheRobotStudio/SO-ARM100 repo or your local lerobot-repo checkout).
    """
    try:
        import lerobot
    except ImportError:
        return None
    root = Path(lerobot.__file__).parent
    for pattern in ("**/so101*.urdf", "**/so100*.urdf", "**/SO101*.urdf", "**/SO100*.urdf"):
        hits = sorted(root.glob(pattern))
        if hits:
            return hits[0]
    return None
