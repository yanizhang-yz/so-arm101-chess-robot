"""The chess brain: legal moves + a Stockfish opponent, kid-strength tunable.

Used from stage 2 onward. Needs the `stockfish` binary on PATH
(`brew install stockfish`) only for best_move()/evaluate(); the rest of the
project works with python-chess alone.

For an even more kid-friendly, human-like opponent later, swap Stockfish for a
Maia weights file (Maia plays like a human at a chosen rating) — same interface.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass

import chess
import chess.engine


@dataclass
class ChessBrain:
    stockfish_path: str | None = None
    skill_level: int = 3        # Stockfish "Skill Level" 0..20 (0 ≈ absolute beginner)
    think_time_s: float = 0.3

    def __post_init__(self) -> None:
        self.path = self.stockfish_path or shutil.which("stockfish")
        self._engine = None

    def _engine_lazy(self):
        if self._engine is None:
            if not self.path:
                raise RuntimeError("stockfish not found — `brew install stockfish` or set stockfish_path")
            self._engine = chess.engine.SimpleEngine.popen_uci(self.path)
        return self._engine

    def best_move(self, board: chess.Board) -> chess.Move:
        eng = self._engine_lazy()
        eng.configure({"Skill Level": int(self.skill_level)})
        return eng.play(board, chess.engine.Limit(time=self.think_time_s)).move

    def evaluate(self, board: chess.Board) -> int:
        """Centipawns from White's point of view (mate scored as +/-100000)."""
        eng = self._engine_lazy()
        info = eng.analyse(board, chess.engine.Limit(time=self.think_time_s))
        return info["score"].white().score(mate_score=100000)

    def close(self) -> None:
        if self._engine is not None:
            self._engine.quit()
            self._engine = None
