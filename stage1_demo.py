#!/usr/bin/env python
"""Stage 1: pick a piece up from one square and set it down on another.

Runs offline by default with a MockArm (prints the choreography) so you can
verify the logic with no hardware. Add --hardware to drive a real SO-ARM101.

Examples:
    python stage1_demo.py --from e2 --to e4
    python stage1_demo.py --move e7e5                       # plan from the start position
    python stage1_demo.py --fen "<FEN>" --move e4d5         # a capture
    python stage1_demo.py --move e1g1 --fen "<FEN>"         # castling -> two carries
    python stage1_demo.py --from e2 --to e4 --hardware      # real arm (needs lerobot)
"""
from __future__ import annotations

import argparse

import chess

from chessbot.config import load
from chessbot.moves import Op, plan_move
from chessbot.runtime import build_motion


def build_ops(args) -> list[Op]:
    if args.move:
        board = chess.Board(args.fen) if args.fen else chess.Board()
        return plan_move(board, chess.Move.from_uci(args.move))
    if args.from_sq and args.to_sq:
        return [Op("carry", src=args.from_sq, dst=args.to_sq)]
    raise SystemExit("give --from/--to or --move (see --help)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--from", dest="from_sq", help="source square, e.g. e2")
    p.add_argument("--to", dest="to_sq", help="destination square, e.g. e4")
    p.add_argument("--move", help="UCI move, e.g. e2e4 (handles captures/castling/promotion)")
    p.add_argument("--fen", help="position the --move applies to (default: start position)")
    p.add_argument("--hardware", action="store_true", help="drive a real SO-ARM101 (needs lerobot)")
    p.add_argument("--config", help="path to a board.local.yaml")
    args = p.parse_args()

    settings = load(args.config)
    ops = build_ops(args)

    print("Plan:")
    for op in ops:
        print(f"  - {op}")
    print("\nExecuting:")

    motion = build_motion(settings, hardware=args.hardware)
    motion.arm.connect()
    try:
        motion.execute(ops)
    finally:
        motion.arm.disconnect()
    print("\nDone.")


if __name__ == "__main__":
    main()
