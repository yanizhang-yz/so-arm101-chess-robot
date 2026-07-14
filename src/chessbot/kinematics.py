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
    """robot_xy = scale * R(theta) @ (board_xy mirrored by `flip`) + offset [+ warp].

    `flip` is +1 or -1. The board's layout can be MIRRORED relative to the arm's
    frame (a left/right handedness flip, depending on how the board is placed), so
    the fit has to allow a reflection — not just a rotation. Forcing a pure
    rotation makes the least-squares scale collapse toward 0 on a mirrored board.

    `warp_x`/`warp_y` (optional, 6 coefficients each) add a small quadratic
    correction on top of the rigid map. A rigid similarity assumes the arm's own
    position sense is perfect; in reality it's distorted by 1-2 cm that varies
    smoothly across the workspace, and the warp soaks that up. Outside `warp_box`
    (the region the calibration points covered) the correction is held at the
    box edge instead of extrapolating — quadratics explode when extrapolated.
    """

    scale: float = 1.0
    theta_rad: float = 0.0
    offset: np.ndarray | None = None  # shape (2,), meters
    flip: float = 1.0                 # +1 normal, -1 mirrored (reflection on the y axis)
    warp_x: np.ndarray | None = None  # quadratic residual coeffs [1, x, y, x², xy, y²]
    warp_y: np.ndarray | None = None
    warp_box: np.ndarray | None = None  # [xmin, ymin, xmax, ymax] the warp was fitted on

    def __post_init__(self) -> None:
        self.offset = np.zeros(2) if self.offset is None else np.asarray(self.offset, float).reshape(2)
        self.warp_x = None if self.warp_x is None else np.asarray(self.warp_x, float).reshape(6)
        self.warp_y = None if self.warp_y is None else np.asarray(self.warp_y, float).reshape(6)
        self.warp_box = None if self.warp_box is None else np.asarray(self.warp_box, float).reshape(4)

    @staticmethod
    def _quad_features(x: float, y: float) -> np.ndarray:
        return np.array([1.0, x, y, x * x, x * y, y * y])

    def xy(self, board_xy: tuple[float, float]) -> np.ndarray:
        c, s = math.cos(self.theta_rad), math.sin(self.theta_rad)
        r = np.array([[c, -s], [s, c]])
        p = np.asarray(board_xy, float) * np.array([1.0, self.flip])
        out = self.scale * (r @ p) + self.offset
        if self.warp_x is not None and self.warp_y is not None:
            bx, by = float(board_xy[0]), float(board_xy[1])
            if self.warp_box is not None:
                bx = float(np.clip(bx, self.warp_box[0], self.warp_box[2]))
                by = float(np.clip(by, self.warp_box[1], self.warp_box[3]))
            f = self._quad_features(bx, by)
            out = out + np.array([f @ self.warp_x, f @ self.warp_y])
        return out

    @classmethod
    def from_correspondences(
        cls, board_pts: list[tuple[float, float]], robot_pts: list[tuple[float, float]]
    ) -> "BoardToRobot":
        """Least-squares similarity fit (Umeyama) that allows a reflection."""
        b = np.asarray(board_pts, float)
        w = np.asarray(robot_pts, float)
        if b.shape != w.shape or len(b) < 2:
            raise ValueError("need matching board/robot point lists of length >= 2")
        bc, wc = b.mean(0), w.mean(0)
        bb, ww = b - bc, w - wc
        cov = (ww.T @ bb) / len(b)
        u, sv, vt = np.linalg.svd(cov)
        r = u @ vt  # orthogonal part; det may be -1 (a mirror) — and that's allowed
        var_b = float((bb ** 2).sum() / len(b))
        scale = float(sv.sum() / var_b) if var_b > 0 else 1.0
        if np.linalg.det(r) < 0:  # mirrored board: pull the reflection out into `flip`
            flip = -1.0
            rot = r @ np.array([[1.0, 0.0], [0.0, -1.0]])
        else:
            flip = 1.0
            rot = r
        offset = wc - scale * (rot @ (bc * np.array([1.0, flip])))
        return cls(scale=scale, theta_rad=math.atan2(rot[1, 0], rot[0, 0]), offset=offset, flip=flip)

    @classmethod
    def with_warp(
        cls, board_pts: list[tuple[float, float]], robot_pts: list[tuple[float, float]]
    ) -> "BoardToRobot":
        """Similarity fit plus a quadratic warp over the leftover residuals.

        Needs >= 8 well-spread points (the warp has 6 coefficients per axis);
        with fewer, returns the plain similarity fit.
        """
        t = cls.from_correspondences(board_pts, robot_pts)
        if len(board_pts) < 8:
            return t
        b = np.asarray(board_pts, float)
        resid = np.asarray(robot_pts, float) - np.array([t.xy(p) for p in board_pts])
        feats = np.array([cls._quad_features(x, y) for x, y in b])
        wx, *_ = np.linalg.lstsq(feats, resid[:, 0], rcond=None)
        wy, *_ = np.linalg.lstsq(feats, resid[:, 1], rcond=None)
        t.warp_x, t.warp_y = wx, wy
        t.warp_box = np.array([b[:, 0].min(), b[:, 1].min(), b[:, 0].max(), b[:, 1].max()])
        return t


# The 8 ways a square board's labels can be oriented (4 rotations x mirror),
# as (file, rank) index maps. Used to fix a transform whose idea of "a1" doesn't
# match the user's — one observed square pins down which of the 8 it is.
BOARD_SYMMETRIES = {
    "as-is": lambda f, r: (f, r),
    "rot90": lambda f, r: (r, 7 - f),
    "rot180": lambda f, r: (7 - f, 7 - r),
    "rot270": lambda f, r: (7 - r, f),
    "mirror-file": lambda f, r: (7 - f, r),
    "mirror-rank": lambda f, r: (f, 7 - r),
    "transpose": lambda f, r: (r, f),
    "anti-transpose": lambda f, r: (7 - r, 7 - f),
}
_SYM_INVERSE = {"as-is": "as-is", "rot90": "rot270", "rot270": "rot90", "rot180": "rot180",
                "mirror-file": "mirror-file", "mirror-rank": "mirror-rank",
                "transpose": "transpose", "anti-transpose": "anti-transpose"}


def _sq_idx(sq: str) -> tuple[int, int]:
    return ord(sq[0]) - ord("a"), int(sq[1:]) - 1


def _sq_name(f: int, r: int) -> str:
    return chr(ord("a") + f) + str(r + 1)


def orientation_candidates(expected_sq: str) -> list[str]:
    """The 8 squares the arm could be over if the map's orientation is off."""
    e = _sq_idx(expected_sq)
    return sorted({_sq_name(*s(*e)) for s in BOARD_SYMMETRIES.values()})


def reorient_transform(transform: BoardToRobot, expected_sq: str, actual_sq: str, geometry) -> BoardToRobot | None:
    """Fix a transform whose board labeling is rotated/mirrored vs the user's.

    The transform was told to go to `expected_sq` but physically hovered over
    `actual_sq` (as identified by the user). That single observation identifies
    which of the 8 orientations the old labeling used; returns a reseeded
    transform in the user's labeling, or None if the pair is inconsistent with
    every orientation (i.e. the square was misread, not mislabeled).
    """
    e, a = _sq_idx(expected_sq), _sq_idx(actual_sq)
    match = [n for n, s in BOARD_SYMMETRIES.items() if s(*e) == a]
    if not match:
        return None
    inv = BOARD_SYMMETRIES[_SYM_INVERSE[match[0]]]
    ref = ["a1", "h1", "a8", "h8", "d4", "e6"]
    board = [geometry.square_center(s) for s in ref]
    mapped = [tuple(transform.xy(geometry.square_center(_sq_name(*inv(*_sq_idx(s)))))) for s in ref]
    return BoardToRobot.from_correspondences(board, mapped)


class IKSolver:
    """Inverse/forward kinematics for the SO-101 arm, via ikpy (pure Python).

    We use ikpy rather than LeRobot's placo-based RobotKinematics: the placo
    wheels have native-library (urdfdom/tinyxml2) version conflicts on macOS,
    while ikpy reads the same URDF with no compiled dependencies. The gripper is
    aimed straight down (a top-down grasp) so the jaws straddle a piece from above.
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
        # The arm's measured pose can read slightly past the URDF joint limits
        # (calibration offsets), and ikpy/scipy reject an IK starting guess that's
        # out of bounds. Widen the active joints a little, then clamp the guess in
        # joints_for() so the solver always starts inside the bounds. The TRUE
        # limits are kept: solutions are clamped back to them before being
        # returned, so we never command a servo past its physical range.
        margin = 0.35  # radians (~20 deg)
        self._true_lo, self._true_hi = {}, {}
        for i in self._active:
            b = self.chain.links[i].bounds
            if b and b[0] is not None and b[1] is not None:
                self._true_lo[i], self._true_hi[i] = b
                self.chain.links[i].bounds = (b[0] - margin, b[1] + margin)
        lows, highs = [], []
        for link in self.chain.links:
            b = getattr(link, "bounds", (None, None)) or (None, None)
            lows.append(-np.inf if b[0] is None else b[0])
            highs.append(np.inf if b[1] is None else b[1])
        self._lower = np.array(lows, dtype=float)
        self._upper = np.array(highs, dtype=float)

    def _full(self, q_deg) -> np.ndarray:
        """A full ikpy joint vector (radians) built from our 5 arm-joint degrees."""
        full = np.zeros(len(self.chain.links))
        full[self._active] = np.deg2rad(np.asarray(q_deg, float))
        return full

    # Fallback IK starting poses (degrees). The solver is a local optimizer: from
    # one unlucky starting pose it can settle 5 cm away from a target it could
    # reach perfectly from another. Trying a few spread-out poses fixes that.
    _RESTARTS = [(0.0, -45.0, 60.0, 45.0, 0.0), (0.0, -90.0, 90.0, 0.0, 0.0),
                 (45.0, -45.0, 60.0, 45.0, 0.0), (-45.0, -45.0, 60.0, 45.0, 0.0)]

    def joints_for(self, xyz, current_q_deg, tol_mm: float = 3.0) -> np.ndarray:
        """IK for a target gripper point with a top-down approach. Returns 5 joint degrees.

        Tries a perfectly vertical approach first (jaws come straight down and open
        horizontally). If that can't reach — far squares sit at the edge of the
        arm's reach when the wrist must hang straight down — it retries with the
        approach tilted a little outward, which lets the wrist lean toward the
        target. Each approach is solved from the current pose plus a few fallback
        poses, because the underlying solver is local and can get stuck.
        """
        target = np.asarray(xyz, float)
        guesses = [np.clip(self._full(current_q_deg), self._lower, self._upper)]
        guesses += [np.clip(self._full(g), self._lower, self._upper) for g in self._RESTARTS]
        best_err, best_full = np.inf, None
        for approach in self._approaches(target):
            for guess in guesses:
                full = self.chain.inverse_kinematics(
                    target_position=target,
                    target_orientation=list(approach),
                    orientation_mode="Z",
                    initial_position=guess,
                )
                for i in self._active:  # never command past the REAL servo range
                    if i in self._true_lo:
                        full[i] = min(max(full[i], self._true_lo[i]), self._true_hi[i])
                err = 1000.0 * float(np.linalg.norm(self.chain.forward_kinematics(full)[:3, 3] - target))
                if err < best_err:
                    best_err, best_full = err, full
                if err <= tol_mm:
                    return np.rad2deg(full[self._active])
        print(f"  ik: closest solution is {best_err:.0f} mm from "
              f"({target[0]:.3f}, {target[1]:.3f}, {target[2]:.3f}) — is this spot within reach?")
        return np.rad2deg(best_full[self._active])

    def _approaches(self, target) -> list[np.ndarray]:
        """Approach directions to try: straight down, then tilted a few degrees
        outward (away from the base) — trading a slightly angled grab for the
        extra reach the far squares need."""
        out = [np.array([0.0, 0.0, -1.0])]
        r = float(np.hypot(target[0], target[1]))
        if r > 1e-6:
            ux, uy = target[0] / r, target[1] / r
            # measured on hardware: each rung buys reach; 32 deg is what gets
            # the far corners (a1/a8 sit ~1 cm past what 24 deg can touch)
            for deg in (8.0, 16.0, 24.0, 32.0):
                t = np.deg2rad(deg)
                out.append(np.array([np.sin(t) * ux, np.sin(t) * uy, -np.cos(t)]))
        return out

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
