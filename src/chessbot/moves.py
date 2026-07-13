"""Turn a chess move into an ordered list of primitive arm operations.

This is where the fiddly rules live: a capture removes the target piece first,
castling moves two pieces, en passant removes a pawn that is *not* on the
destination square, and promotion retires the pawn for a spare queen. Keeping
it here (pure, given a python-chess Board + Move) means motion.py only ever has
to deal with three primitives: carry, remove, place_spare.
"""
from __future__ import annotations

from dataclasses import dataclass

import chess


@dataclass(frozen=True)
class Op:
    kind: str                  # "carry" | "remove" | "place_spare"
    src: str | None = None     # source square (carry, remove)
    dst: str | None = None     # destination square (carry, place_spare)
    piece: str | None = None   # symbol of the piece being handled, e.g. "P", "Q"
                               # (motion uses it to pick the right grab height)

    def __str__(self) -> str:
        if self.kind == "carry":
            return f"carry {self.src} -> {self.dst}"
        if self.kind == "remove":
            return f"remove {self.src} (to off-board graveyard)"
        return f"place spare {self.piece} on {self.dst}"


def plan_move(board: chess.Board, move: chess.Move) -> list[Op]:
    """Expand `move` (must be legal in `board`) into primitive ops, in order."""
    if move not in board.legal_moves:
        raise ValueError(f"illegal move {move.uci()} in position {board.fen()}")

    src = chess.square_name(move.from_square)
    dst = chess.square_name(move.to_square)
    mover = board.piece_at(move.from_square).symbol().upper()  # legal move => never None
    ops: list[Op] = []

    # 1. Clear any captured piece first, so the destination square is empty.
    if board.is_en_passant(move):
        # Captured pawn sits on the destination file but the *source* rank.
        cap_sq = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
        ops.append(Op("remove", src=chess.square_name(cap_sq), piece="P"))
    elif board.is_capture(move):
        captured = board.piece_at(move.to_square)
        ops.append(Op("remove", src=dst, piece=captured.symbol().upper() if captured else None))

    # 2. Move the piece (or, for promotion, retire the pawn + drop in a spare).
    if move.promotion:
        ops.append(Op("remove", src=src, piece="P"))  # retire the pawn off-board
        ops.append(Op("place_spare", dst=dst, piece=chess.piece_symbol(move.promotion).upper()))
    else:
        ops.append(Op("carry", src=src, dst=dst, piece=mover))

    # 3. Castling also moves the rook (the king move is handled in step 2).
    if board.is_castling(move):
        rank = chess.square_rank(move.from_square)
        if chess.square_file(move.to_square) > chess.square_file(move.from_square):
            rook_from, rook_to = chess.square(7, rank), chess.square(5, rank)  # h -> f (kingside)
        else:
            rook_from, rook_to = chess.square(0, rank), chess.square(3, rank)  # a -> d (queenside)
        ops.append(Op("carry", src=chess.square_name(rook_from), dst=chess.square_name(rook_to), piece="R"))

    return ops
