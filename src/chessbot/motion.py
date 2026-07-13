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
    grasp_lift: float = 0.0   # global trim added to every grab height
    hover: float = 0.08       # travel clearance above the GRIP POINT — a carried
                              # piece hangs below the jaws, so this must be more
                              # than your tallest piece (the king), plus a little


# Full piece heights in meters for a small set (40 mm squares) — measure YOURS
# with a ruler and put the real numbers in config/board.local.yaml.
DEFAULT_PIECE_HEIGHTS = {"P": 0.032, "N": 0.045, "B": 0.050, "R": 0.040, "Q": 0.058, "K": 0.065}


@dataclass
class PieceGrasp:
    """Where the jaws should close on each piece.

    A pawn and a rook are different heights, so one fixed grab height can't work:
    close at the pawn's height on a rook and you hit its body; close at the
    rook's height on a pawn and you grab air. Instead we know each piece's full
    height and close the jaws a bit below its top — under the head/collar, where
    the piece is narrow and the head above stops it slipping out.
    """
    heights_m: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_PIECE_HEIGHTS))
    grip_below_top_m: float = 0.012   # close this far below the piece's tip
    min_z_m: float = 0.008            # never grab lower than this (jaws vs. board)

    def height_of(self, piece: str | None) -> float:
        return self.heights_m.get((piece or "P").upper(), self.heights_m["P"])

    def grasp_z(self, piece: str | None) -> float:
        """Height above the board surface where the jaws should close."""
        return max(self.height_of(piece) - self.grip_below_top_m, self.min_z_m)


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
    pieces: PieceGrasp = field(default_factory=PieceGrasp)
    offboard: OffBoard = field(default_factory=OffBoard)
    descend_step_m: float = 0.015   # vertical waypoint spacing near the pieces
    _grave_used: int = 0

    # --- coordinate helpers -------------------------------------------------
    def _goto_board(self, board_xy: tuple[float, float], z: float) -> None:
        x, y = self.transform.xy(board_xy)
        self.arm.goto(float(x), float(y), float(z))

    def _grasp_z(self, piece: str | None) -> float:
        return self.heights.table_z + self.heights.grasp_lift + self.pieces.grasp_z(piece)

    def _travel_z(self, piece: str | None) -> float:
        # hover is clearance above the grip point: a carried piece hangs
        # grasp_z below the jaws, so its bottom travels `hover` above the board.
        return self._grasp_z(piece) + self.heights.hover

    def _vertical(self, board_xy: tuple[float, float], z_from: float, z_to: float) -> None:
        """Descend/ascend through close waypoints so the jaws move in a straight
        vertical line instead of a joint-space arc that can sideswipe pieces."""
        z = z_from
        while abs(z - z_to) > 1e-9:
            z = max(z - self.descend_step_m, z_to) if z_to < z else min(z + self.descend_step_m, z_to)
            self._goto_board(board_xy, z)

    # --- primitives ---------------------------------------------------------
    def _pick_at(self, board_xy: tuple[float, float], piece: str | None) -> None:
        travel, grasp = self._travel_z(piece), self._grasp_z(piece)
        self._goto_board(board_xy, travel)
        self.arm.set_gripper(True)   # open
        self._vertical(board_xy, travel, grasp)
        self.arm.set_gripper(False)  # close on the piece
        self._vertical(board_xy, grasp, travel)

    def _place_at(self, board_xy: tuple[float, float], piece: str | None) -> None:
        travel, grasp = self._travel_z(piece), self._grasp_z(piece)
        self._goto_board(board_xy, travel)
        self._vertical(board_xy, travel, grasp)
        self.arm.set_gripper(True)   # release
        self._vertical(board_xy, grasp, travel)

    def carry(self, src: str, dst: str, piece: str | None = None) -> None:
        self._pick_at(self.geometry.square_center(src), piece)
        self._place_at(self.geometry.square_center(dst), piece)

    def remove(self, square: str, piece: str | None = None) -> None:
        if self._grave_used >= len(self.offboard.graveyard):
            raise RuntimeError("no free graveyard slots — add more under offboard.graveyard in config")
        slot = self.offboard.graveyard[self._grave_used]
        self._grave_used += 1
        self._pick_at(self.geometry.square_center(square), piece)
        self._place_at(slot, piece)

    def place_spare(self, piece: str, dst: str) -> None:
        slots = self.offboard.spares.get(piece.upper())
        if not slots:
            raise RuntimeError(f"no spare {piece!r} configured for promotion (offboard.spares)")
        src = slots.pop(0)
        self._pick_at(src, piece)
        self._place_at(self.geometry.square_center(dst), piece)

    # --- op dispatch --------------------------------------------------------
    def execute(self, ops: list[Op]) -> None:
        for op in ops:
            if op.kind == "carry":
                self.carry(op.src, op.dst, op.piece)
            elif op.kind == "remove":
                self.remove(op.src, op.piece)
            elif op.kind == "place_spare":
                self.place_spare(op.piece, op.dst)
            else:
                raise ValueError(f"unknown op kind: {op.kind!r}")
        self.arm.home()
