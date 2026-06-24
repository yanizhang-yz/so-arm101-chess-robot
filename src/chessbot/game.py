"""Stage 2: a full, rules-complete game.

The human moves their own physical pieces and keys the move in; the robot picks
a kid-strength reply with Stockfish and physically plays it (only the robot's
own pieces — captures of the human's pieces are cleared by motion).

I/O (input()/print()) lives in play.py. This class is pure game state plus the
two operations — apply a human move, make the robot's move — so it stays
testable with a MockArm and a stub brain (no Stockfish needed in tests).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import chess

from .engine import ChessBrain
from .motion import ChessMotion
from .moves import plan_move


class IllegalMove(ValueError):
    """The human's typed move wasn't understood or isn't legal right now."""


@dataclass
class ChessGame:
    motion: ChessMotion
    brain: ChessBrain
    human_color: bool = chess.WHITE
    narrate: Callable[[str], None] = print
    board: chess.Board = field(default_factory=chess.Board)

    @property
    def robot_color(self) -> bool:
        return not self.human_color

    @property
    def turn_is_human(self) -> bool:
        return self.board.turn == self.human_color

    def parse(self, text: str) -> chess.Move:
        """Accept SAN ('Nf3', 'e4', 'O-O') or UCI ('e2e4', 'e7e8q').

        python-chess's parsers only return *legal* moves (else they raise a
        ValueError subclass), so a returned move is always safe to push.
        """
        text = text.strip()
        for parser in (self.board.parse_san, self.board.parse_uci):
            try:
                return parser(text)
            except ValueError:
                continue
        raise IllegalMove(f"didn't understand or not legal: {text!r}")

    def apply_human_move(self, text: str) -> chess.Move:
        move = self.parse(text)
        self.board.push(move)
        return move

    def robot_move(self) -> chess.Move:
        """Pick a kid-strength move, physically play it, then update the board."""
        move = self.brain.best_move(self.board)
        san = self.board.san(move)                 # SAN must be read BEFORE pushing
        ops = plan_move(self.board, move)          # plan needs the pre-move position
        self.narrate(f"My move: {san}.")
        self.motion.execute(ops)
        self.board.push(move)
        return move

    def hint(self) -> str:
        """A coach-y suggestion for the side to move (seeds the stage-4 coach)."""
        return self.board.san(self.brain.best_move(self.board))

    def takeback(self) -> bool:
        """Rewind the last full round (robot ply + human ply) in game state.

        Note: on hardware this only rewinds the *game*, not the physical pieces —
        reset those by hand. Fine for the MockArm / learning phase.
        """
        undone = 0
        while self.board.move_stack and undone < 2:
            self.board.pop()
            undone += 1
        return undone > 0

    def status(self) -> str | None:
        """A friendly end-of-game message, or None while the game continues."""
        if self.board.is_checkmate():
            who = "I" if self.board.turn == self.human_color else "You"
            return f"Checkmate — {who} won! Good game."
        if self.board.is_stalemate():
            return "Stalemate — it's a draw."
        if self.board.is_insufficient_material():
            return "Draw — not enough pieces left to checkmate."
        if self.board.is_fifty_moves():
            return "Draw by the fifty-move rule."
        if self.board.can_claim_threefold_repetition():
            return "Draw by repetition."
        return None
