"""Piece-aware grasping: the jaws must close at a height that matches the piece.

A pawn and a king are very different heights — grabbing both at one fixed z is
exactly the failure mode we saw on hardware. These tests pin down the geometry
with a MockArm (no hardware): taller piece -> jaws close higher, travel height
keeps a carried piece clear of the board, descent happens in small steps.
"""
import chess

from chessbot.arm import MockArm
from chessbot.board import BoardGeometry
from chessbot.kinematics import BoardToRobot
from chessbot.motion import ChessMotion, Heights, PieceGrasp
from chessbot.moves import Op, plan_move


def make_motion() -> ChessMotion:
    return ChessMotion(arm=MockArm(verbose=False), geometry=BoardGeometry(),
                       transform=BoardToRobot(), heights=Heights(table_z=0.0))


def zs(motion) -> list[float]:
    return [entry[3] for entry in motion.arm.log if entry[0] == "goto"]


def grab_z(motion) -> float:
    """The z the arm was at when the gripper closed."""
    last_goto = None
    for entry in motion.arm.log:
        if entry[0] == "goto":
            last_goto = entry
        elif entry == ("gripper", "close"):
            return last_goto[3]
    raise AssertionError("gripper never closed")


def test_taller_piece_is_grabbed_higher():
    pawn, king = make_motion(), make_motion()
    pawn.carry("e2", "e4", piece="P")
    king.carry("e1", "e2", piece="K")
    assert grab_z(king) > grab_z(pawn)


def test_grab_height_comes_from_piece_height():
    m = make_motion()
    m.carry("e2", "e4", piece="P")
    expected = m.pieces.height_of("P") - m.pieces.grip_below_top_m
    assert abs(grab_z(m) - expected) < 1e-9


def test_unknown_piece_defaults_to_pawn_height():
    named, default = make_motion(), make_motion()
    named.carry("e2", "e4", piece="P")
    default.carry("e2", "e4", piece=None)
    assert grab_z(named) == grab_z(default)


def test_never_grabs_below_the_floor():
    g = PieceGrasp(heights_m={"P": 0.010}, grip_below_top_m=0.012, min_z_m=0.008)
    assert g.grasp_z("P") == 0.008


def test_travel_keeps_carried_piece_above_the_board():
    m = make_motion()
    m.carry("e1", "e2", piece="K")
    # bottom of the carried king = gripper z - grasp height above the table
    travel_bottom = max(zs(m)) - m.pieces.grasp_z("K")
    assert travel_bottom >= m.heights.hover - 1e-9
    assert m.heights.hover > m.pieces.height_of("K")  # clears a standing king


def test_descent_is_stepped_not_one_jump():
    m = make_motion()
    m.carry("e2", "e4", piece="P")
    drops = [abs(b - a) for a, b in zip(zs(m), zs(m)[1:])]
    assert max(drops) <= m.descend_step_m + 1e-9


def test_plan_move_names_the_moved_piece():
    ops = plan_move(chess.Board(), chess.Move.from_uci("g1f3"))
    assert ops == [Op("carry", src="g1", dst="f3", piece="N")]


def test_plan_move_names_the_captured_piece():
    fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"  # exd5
    ops = plan_move(chess.Board(fen), chess.Move.from_uci("e4d5"))
    assert ops[0] == Op("remove", src="d5", piece="P")
    assert ops[1] == Op("carry", src="e4", dst="d5", piece="P")


def test_castling_rook_is_a_rook():
    fen = "rnbqk2r/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
    ops = plan_move(chess.Board(fen), chess.Move.from_uci("e1g1"))
    assert ops[0].piece == "K"
    assert ops[1] == Op("carry", src="h1", dst="f1", piece="R")
