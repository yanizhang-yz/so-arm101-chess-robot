"""Central runtime config — ports, board geometry, heights, off-board slots.

Defaults are sensible placeholders so the offline demo and tests just run. Once
your arm and board are set up, copy config/board.example.yaml to
config/board.local.yaml and fill in measured values; load() overlays it.
Hardware-only fields are marked TODO.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .board import BoardGeometry
from .kinematics import BoardToRobot
from .motion import Heights, OffBoard

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ArmHardware:
    follower_port: str = "TODO"   # from `lerobot-find-port`, e.g. /dev/tty.usbmodem...
    robot_id: str = "chessbot_follower"
    urdf_path: str = "TODO"       # SO-101 URDF (see kinematics.find_urdf)
    gripper_open: float = 60.0
    gripper_closed: float = 10.0


def _default_offboard() -> OffBoard:
    # Board-frame (x, y) in meters: a column to the left of file a for captures,
    # plus one spare queen. Replace with measured positions once on hardware.
    return OffBoard(
        graveyard=[(-0.05, i * 0.04) for i in range(8)] + [(-0.09, i * 0.04) for i in range(8)],
        spares={"Q": [(-0.13, 0.0)], "R": [(-0.13, 0.04)], "B": [(-0.13, 0.08)], "N": [(-0.13, 0.12)]},
    )


@dataclass
class Settings:
    geometry: BoardGeometry = field(default_factory=BoardGeometry)
    transform: BoardToRobot = field(default_factory=BoardToRobot)
    heights: Heights = field(default_factory=Heights)
    offboard: OffBoard = field(default_factory=_default_offboard)
    arm: ArmHardware = field(default_factory=ArmHardware)


def load(path: str | Path | None = None) -> Settings:
    """Load Settings, overlaying config/board.local.yaml (or `path`) if present."""
    s = Settings()
    p = Path(path) if path else ROOT / "config" / "board.local.yaml"
    if p.exists():
        _overlay(s, yaml.safe_load(p.read_text()) or {})
    return s


def _overlay(s: Settings, data: dict) -> None:
    if "square_size_m" in data:
        s.geometry = BoardGeometry(square_size_m=float(data["square_size_m"]))
    if (t := data.get("transform")):
        s.transform = BoardToRobot(scale=t.get("scale", 1.0), theta_rad=t.get("theta_rad", 0.0),
                                   offset=t.get("offset", [0.0, 0.0]))
    if (h := data.get("heights")):
        s.heights = Heights(**h)
    if (ob := data.get("offboard")):
        s.offboard = OffBoard(
            graveyard=[tuple(p) for p in ob.get("graveyard", [])],
            spares={k: [tuple(p) for p in v] for k, v in ob.get("spares", {}).items()},
        )
    if (a := data.get("arm")):
        s.arm = ArmHardware(**a)
