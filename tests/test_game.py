"""ChessGame logic, exercised with a MockArm and a stub brain (no Stockfish)."""
import chess
import pytest

from chessbot.arm import MockArm
from chessbot.board import BoardGeometry
from chessbot.config import _default_offboard
from chessbot.game import ChessGame, IllegalMove
from chessbot.kinematics import BoardToRobot
from chessbot.motion import ChessMotion


class StubBrain:
    """A 'brain' that just plays the move we hand it — keeps tests Stockfish-free."""

    def __init__(self, uci: str):
        self.uci = uci

    def best_move(self, board: chess.Board) -> chess.Move:
        return chess.Move.from_uci(self.uci)


def make_game(human_color=chess.WHITE, brain=None) -> ChessGame:
    motion = ChessMotion(arm=MockArm(verbose=False), geometry=BoardGeometry(),
                         transform=BoardToRobot(), offboard=_default_offboard())
    return ChessGame(motion=motion, brain=brain or StubBrain("e2e4"),
                     human_color=human_color, narrate=lambda s: None)


def test_parse_accepts_san_and_uci():
    g = make_game()
    assert g.parse("e4") == chess.Move.from_uci("e2e4")
    assert g.parse("Nf3") == chess.Move.from_uci("g1f3")
    assert g.parse("e2e4") == chess.Move.from_uci("e2e4")


def test_illegal_or_garbled_input_raises():
    g = make_game()
    with pytest.raises(IllegalMove):
        g.parse("e5")        # no pawn can reach e5 on move one
    with pytest.raises(IllegalMove):
        g.parse("banana")


def test_apply_human_move_updates_board():
    g = make_game()
    g.apply_human_move("e4")
    assert g.board.piece_at(chess.E4) is not None
    assert g.board.turn == chess.BLACK


def test_robot_move_executes_on_arm_and_pushes():
    # Human is Black, so White (the robot) is to move from the start.
    g = make_game(human_color=chess.BLACK, brain=StubBrain("e2e4"))
    move = g.robot_move()
    assert move == chess.Move.from_uci("e2e4")
    assert g.board.move_stack[-1] == move
    assert len(g.motion.arm.log) > 0      # the arm actually did something


def test_status_detects_checkmate():
    g = make_game()
    for mv in ["f3", "e5", "g4", "Qh4"]:  # Fool's mate
        g.apply_human_move(mv)
    assert "Checkmate" in (g.status() or "")


def test_takeback_rewinds_a_full_round():
    g = make_game()
    g.apply_human_move("e4")
    g.board.push(chess.Move.from_uci("e7e5"))
    assert g.takeback() is True
    assert len(g.board.move_stack) == 0
