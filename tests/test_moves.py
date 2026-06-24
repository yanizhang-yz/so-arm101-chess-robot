"""The special-move logic is the easy-to-get-wrong part, so test it hard."""
import chess

from chessbot.moves import plan_move


def ops_as_str(board_fen, uci):
    board = chess.Board(board_fen) if board_fen else chess.Board()
    return [str(op) for op in plan_move(board, chess.Move.from_uci(uci))]


def test_quiet_move_is_one_carry():
    assert ops_as_str(None, "e2e4") == ["carry e2 -> e4"]


def test_capture_removes_target_first():
    fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"  # exd5 available
    assert ops_as_str(fen, "e4d5") == ["remove d5 (to off-board graveyard)", "carry e4 -> d5"]


def test_en_passant_removes_the_right_pawn():
    fen = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"  # e5xd6 e.p.
    # The captured pawn is on d5, not on the destination d6.
    assert ops_as_str(fen, "e5d6") == ["remove d5 (to off-board graveyard)", "carry e5 -> d6"]


def test_kingside_castle_moves_king_then_rook():
    fen = "rnbqk2r/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
    assert ops_as_str(fen, "e1g1") == ["carry e1 -> g1", "carry h1 -> f1"]


def test_queenside_castle_moves_correct_rook():
    fen = "r3kbnr/pppppppp/8/8/8/8/PPPPPPPP/R3KBNR w KQkq - 0 1"
    assert ops_as_str(fen, "e1c1") == ["carry e1 -> c1", "carry a1 -> d1"]


def test_promotion_retires_pawn_and_drops_a_spare():
    fen = "k7/4P3/8/8/8/8/8/4K3 w - - 0 1"  # black king on a8, so e8 is free to promote into
    assert ops_as_str(fen, "e7e8q") == [
        "remove e7 (to off-board graveyard)",
        "place spare Q on e8",
    ]


def test_capture_promotion_clears_target_then_promotes():
    fen = "3rk3/4P3/8/8/8/8/8/4K3 w - - 0 1"  # exd8=Q, capturing the rook on d8
    assert ops_as_str(fen, "e7d8q") == [
        "remove d8 (to off-board graveyard)",
        "remove e7 (to off-board graveyard)",
        "place spare Q on d8",
    ]
