#!/usr/bin/env python
"""Stage 2: play a full game against the robot (MockArm by default).

    python play.py                      # you are White vs. a gentle robot
    python play.py --color black --skill 5
    python play.py --hardware           # robot physically plays its own moves

Type moves as 'e4', 'Nf3', 'O-O', or 'e2e4'.
Commands: hint | board | takeback | resign | help
"""
from __future__ import annotations

import argparse

import chess

from chessbot.config import load
from chessbot.engine import ChessBrain
from chessbot.game import ChessGame, IllegalMove
from chessbot.runtime import build_motion

HELP = "Move with e4 / Nf3 / O-O / e2e4.  Commands: hint | board | takeback | resign | help"


def render(board: chess.Board, pov: bool) -> str:
    """ASCII board from the human's point of view. UPPER = White, lower = black."""
    ranks = range(7, -1, -1) if pov == chess.WHITE else range(8)
    files = range(8) if pov == chess.WHITE else range(7, -1, -1)
    rows = []
    for r in ranks:
        cells = (board.piece_at(chess.square(f, r)) for f in files)
        rows.append(f"{r + 1} " + " ".join(p.symbol() if p else "." for p in cells))
    labels = "abcdefgh" if pov == chess.WHITE else "hgfedcba"
    rows.append("  " + " ".join(labels))
    return "\n".join(rows)


def show(game: ChessGame, pov: bool) -> None:
    print("\n" + render(game.board, pov))
    if game.board.is_check() and game.status() is None:
        print("  Check!")


def handle_command(cmd: str, game: ChessGame, pov: bool) -> str | None:
    """Returns 'resign', 'handled', or None (meaning: treat cmd as a move)."""
    low = cmd.lower()
    if low in ("resign", "quit", "exit"):
        return "resign"
    if low in ("help", "?"):
        print("  " + HELP)
    elif low == "board":
        print(render(game.board, pov))
    elif low == "hint":
        print(f"  (hint) I'd play {game.hint()}")
    elif low in ("takeback", "undo"):
        print("  took back the last round." if game.takeback() else "  nothing to take back.")
        print(render(game.board, pov))
    else:
        return None
    return "handled"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--color", choices=["white", "black"], default="white", help="the side YOU play")
    p.add_argument("--skill", type=int, default=2, help="Stockfish skill 0..20 (low = beginner-friendly)")
    p.add_argument("--think", type=float, default=0.3, help="robot thinking time per move (s)")
    p.add_argument("--hardware", action="store_true", help="robot physically plays its moves")
    p.add_argument("--config", help="path to a board.local.yaml")
    args = p.parse_args()

    pov = chess.WHITE if args.color == "white" else chess.BLACK
    motion = build_motion(load(args.config), hardware=args.hardware)
    brain = ChessBrain(skill_level=args.skill, think_time_s=args.think)
    game = ChessGame(motion=motion, brain=brain, human_color=pov,
                     narrate=lambda s: print(f"  robot: {s}"))

    print(f"\nYou are {args.color}. {HELP}")
    motion.arm.connect()
    try:
        show(game, pov)
        while True:
            if (status := game.status()) is not None:
                print(f"\n{status}")
                break
            if game.turn_is_human:
                cmd = input("\nyour move > ").strip()
                if not cmd:
                    continue
                outcome = handle_command(cmd, game, pov)
                if outcome == "resign":
                    print("You resigned — good game! Want a rematch?")
                    break
                if outcome == "handled":
                    continue
                try:
                    game.apply_human_move(cmd)
                except IllegalMove as e:
                    print(f"  {e}\n  {HELP}")
                    continue
                show(game, pov)
            else:
                if args.hardware:
                    input("  (keep hands clear — press Enter and I'll move) ")
                game.robot_move()
                show(game, pov)
    finally:
        motion.arm.disconnect()
        brain.close()


if __name__ == "__main__":
    main()
