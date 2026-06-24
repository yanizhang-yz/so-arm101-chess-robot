"""Pick-and-place choreography: execute a list of moves.Op on an ArmBackend.

motion is frame-aware but hardware-agnostic: it computes board-frame points
(via BoardGeometry), maps them to robot space (via BoardToRobot), and issues
goto/gripper calls. Give it a MockArm to dry-run, a LeRobotArm to play for real.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .arm import ArmBackend
from .board import BoardGeometry
from .kinematics import BoardToRobot
from .moves import Op


@dataclass
class Heights:
    """Robot-frame z heights, in meters."""
    table_z: float = 0.02     # the board surface
    grasp_lift: float = 0.0   # close the gripper this far above the surface
    hover: float = 0.06       # safe travel height above the board


@dataclass
class OffBoard:
    """Board-frame (x, y) slots for captured pieces and spare promotion pieces."""
    graveyard: list[tuple[float, float]] = field(default_factory=list)
    spares: dict[str, list[tuple[float, float]]] = field(default_factory=dict)


@dataclass
class ChessMotion:
    arm: ArmBackend
    geometry: BoardGeometry
    transform: BoardToRobot
    heights: Heights = field(default_factory=Heights)
    offboard: OffBoard = field(default_factory=OffBoard)
    _grave_used: int = 0

    # --- coordinate helpers -------------------------------------------------
    def _goto_board(self, board_xy: tuple[float, float], z: float) -> None:
        x, y = self.transform.xy(board_xy)
        self.arm.goto(float(x), float(y), float(z))

    def _hover_over(self, board_xy: tuple[float, float]) -> None:
        self._goto_board(board_xy, self.heights.table_z + self.heights.hover)

    def _down_to(self, board_xy: tuple[float, float]) -> None:
        self._goto_board(board_xy, self.heights.table_z + self.heights.grasp_lift)

    # --- primitives ---------------------------------------------------------
    def _pick_at(self, board_xy: tuple[float, float]) -> None:
        self._hover_over(board_xy)
        self.arm.set_gripper(True)   # open
        self._down_to(board_xy)
        self.arm.set_gripper(False)  # close on the piece
        self._hover_over(board_xy)

    def _place_at(self, board_xy: tuple[float, float]) -> None:
        self._hover_over(board_xy)
        self._down_to(board_xy)
        self.arm.set_gripper(True)   # release
        self._hover_over(board_xy)

    def carry(self, src: str, dst: str) -> None:
        self._pick_at(self.geometry.square_center(src))
        self._place_at(self.geometry.square_center(dst))

    def remove(self, square: str) -> None:
        if self._grave_used >= len(self.offboard.graveyard):
            raise RuntimeError("no free graveyard slots — add more under offboard.graveyard in config")
        slot = self.offboard.graveyard[self._grave_used]
        self._grave_used += 1
        self._pick_at(self.geometry.square_center(square))
        self._place_at(slot)

    def place_spare(self, piece: str, dst: str) -> None:
        slots = self.offboard.spares.get(piece.upper())
        if not slots:
            raise RuntimeError(f"no spare {piece!r} configured for promotion (offboard.spares)")
        src = slots.pop(0)
        self._pick_at(src)
        self._place_at(self.geometry.square_center(dst))

    # --- op dispatch --------------------------------------------------------
    def execute(self, ops: list[Op]) -> None:
        for op in ops:
            if op.kind == "carry":
                self.carry(op.src, op.dst)
            elif op.kind == "remove":
                self.remove(op.src)
            elif op.kind == "place_spare":
                self.place_spare(op.piece, op.dst)
            else:
                raise ValueError(f"unknown op kind: {op.kind!r}")
        self.arm.home()
