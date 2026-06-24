"""Board geometry: chess square names <-> coordinates on the physical board.

Pure math — no hardware, no chess engine — so it is fully unit-testable. The
board frame has its origin at the center of square a1, +x pointing a1 -> h1
(along the files) and +y pointing a1 -> a8 (along the ranks), in meters.
motion.py turns these board-frame points into robot-frame points via
kinematics.BoardToRobot.
"""
from __future__ import annotations

from dataclasses import dataclass

FILES = "abcdefgh"
RANKS = "12345678"


def parse_square(square: str) -> tuple[int, int]:
    """'e2' -> (file_index 0..7, rank_index 0..7). Raises ValueError if invalid."""
    s = square.strip().lower()
    if len(s) != 2 or s[0] not in FILES or s[1] not in RANKS:
        raise ValueError(f"not a board square: {square!r}")
    return FILES.index(s[0]), RANKS.index(s[1])


def square_name(file_idx: int, rank_idx: int) -> str:
    if not (0 <= file_idx < 8 and 0 <= rank_idx < 8):
        raise ValueError(f"file/rank out of range: {file_idx},{rank_idx}")
    return f"{FILES[file_idx]}{RANKS[rank_idx]}"


@dataclass(frozen=True)
class BoardGeometry:
    """Physical layout of the board, in meters, in the board frame (origin = a1)."""

    square_size_m: float = 0.04  # 4 cm squares — a small travel set that fits the arm's reach

    def __post_init__(self) -> None:
        if self.square_size_m <= 0:
            raise ValueError("square_size_m must be positive")

    def square_center(self, square: str) -> tuple[float, float]:
        """Board-frame (x, y) of a square's center, in meters."""
        f, r = parse_square(square)
        return (f * self.square_size_m, r * self.square_size_m)
