"""Map board-plane coordinates into robot space, and (on hardware) solve IK.

Two stages, deliberately separated so the cheap, testable part runs anywhere:

  BoardToRobot   board-frame (x, y) in meters  ->  robot-frame (x, y)
                 a 2-D similarity transform (rotation + uniform scale +
                 translation) you calibrate once. Pure numpy: runs offline,
                 covered by tests. scripts/calibrate_board.py fits it from a
                 few squares whose robot-space location you measure.

  IKSolver       robot-frame point (x, y, z) -> 5 joint degrees (position IK)
                 backed by ikpy (pure Python, reads the URDF). Imported lazily;
                 only needed to drive the real arm.
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


class IKSolver:
    """Inverse/forward kinematics for the SO-101 arm, via ikpy (pure Python).

    We use ikpy rather than LeRobot's placo-based RobotKinematics: the placo
    wheels have native-library (urdfdom/tinyxml2) version conflicts on macOS,
    while ikpy reads the same URDF with no compiled dependencies. Position-only
    IK, which is the right fit for a 5-DOF arm reaching points on a flat board.
    """

    ARM_JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]

    def __init__(self, urdf_path: str | Path, target_frame: str = "gripper_frame_link"):
        import warnings

        from ikpy.chain import Chain  # lazy: optional hardware dep
        actuated = ("revolute", "prismatic", "continuous")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ikpy is chatty about non-actuated links
            # Probe once to read joint types, then rebuild marking only the real
            # (revolute) joints active — the base link and the fixed tip frame must
            # stay inactive, or the IK solver tries to "move" them.
            probe = Chain.from_urdf_file(str(urdf_path))
            mask = [getattr(link, "joint_type", "fixed") in actuated for link in probe.links]
            self.chain = Chain.from_urdf_file(str(urdf_path), active_links_mask=mask)
        self._active = [i for i, on in enumerate(mask) if on]
        if len(self._active) != len(self.ARM_JOINTS):
            raise ValueError(
                f"URDF chain has {len(self._active)} movable joints, expected "
                f"{len(self.ARM_JOINTS)}: {urdf_path}"
            )

    def _full(self, q_deg) -> np.ndarray:
        """A full ikpy joint vector (radians) built from our 5 arm-joint degrees."""
        full = np.zeros(len(self.chain.links))
        full[self._active] = np.deg2rad(np.asarray(q_deg, float))
        return full

    def joints_for(self, xyz, current_q_deg, orientation: np.ndarray | None = None) -> np.ndarray:
        """Position IK for a target gripper point. Returns the 5 arm-joint degrees.

        `orientation` is accepted for API compatibility but ignored — position-only
        IK is the right call for a 5-DOF arm on a flat board.
        """
        full = self.chain.inverse_kinematics(
            target_position=np.asarray(xyz, float),
            initial_position=self._full(current_q_deg),
        )
        return np.rad2deg(full[self._active])

    def forward_xyz(self, q_deg) -> np.ndarray:
        """Forward kinematics: 5 arm-joint degrees -> gripper (x, y, z) in meters."""
        return self.chain.forward_kinematics(self._full(q_deg))[:3, 3]


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
