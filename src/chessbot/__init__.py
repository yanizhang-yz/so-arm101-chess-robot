"""chessbot — a chess-playing, chess-coaching robot arm on the SO-ARM101.

Layered so the brains/logic run with no hardware, and only `arm.LeRobotArm`
(plus the IK path) ever touches the physical robot:

    board       square <-> board-plane geometry (pure math, tested)
    moves       expand a chess move into primitive arm ops: captures,
                castling, en passant, promotion (pure, tested)
    kinematics  board-plane -> robot-frame transform (pure) + IK (hardware)
    arm         MockArm (offline) / LeRobotArm (SO-ARM101 via LeRobot 0.5.x)
    motion      pick-and-place choreography that executes ops on an arm
    engine      Stockfish / python-chess brain (used from stage 2 on)
    config      one place for ports, board geometry, heights, off-board slots
"""
from __future__ import annotations

__version__ = "0.1.0"
