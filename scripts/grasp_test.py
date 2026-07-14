#!/usr/bin/env python
"""Tune the grab on a real piece, one square at a time (HARDWARE).

Put ONE piece on a square, clear its neighbors, keep a hand near the power
switch, then:

    python scripts/grasp_test.py --square e2 --piece P

Each try the arm: hovers over the square, descends straight down, closes the
jaws until they feel the piece, lifts, pauses so you can see whether it's held,
then sets it back down and releases. After each try, adjust and go again:

    g          grab again
    u 3        grip 3 mm HIGHER on the piece (jaws hitting the fat base? go up)
    d 3        grip 3 mm LOWER on the piece (slipping off the tip? go down)
    x 2        nudge the target +2 mm in robot x (fix a sideways miss)
    y -2       nudge the target -2 mm in robot y
    o 55       open the jaws only this wide on approach (jaws brushing the
               neighbors on the way down? make this smaller — just wide enough
               to clear the piece you're grabbing)
    q          quit and print the numbers to save in config/board.local.yaml

When a grab looks centered and the piece rides up firmly, you're done — hit q
and copy the printed lines into your config.
"""
from __future__ import annotations

import argparse
import time

from chessbot.config import load
from chessbot.runtime import build_arm

STEP_M = 0.015  # vertical waypoint spacing, same as ChessMotion uses


def vertical(arm, x: float, y: float, z_from: float, z_to: float) -> None:
    z = z_from
    while abs(z - z_to) > 1e-9:
        z = max(z - STEP_M, z_to) if z_to < z else min(z + STEP_M, z_to)
        arm.goto(x, y, z)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--square", required=True, help="square the piece is on, e.g. e2")
    p.add_argument("--piece", default="P", help="what's on it: P N B R Q K (default P)")
    p.add_argument("--config", help="path to a board.local.yaml")
    args = p.parse_args()

    s = load(args.config)
    piece = args.piece.upper()
    bx, by = s.geometry.square_center(args.square)
    dx = dy = dz = 0.0  # session adjustments, meters
    open_changed = False

    print(f"Grasp test: {piece} on {args.square}. Clear the neighboring squares!")
    arm = build_arm(s, hardware=True)
    arm.connect()
    try:
        while True:
            x, y = (float(v) for v in s.transform.xy((bx, by)))
            x, y = x + dx, y + dy
            grasp_z = s.heights.table_z + s.heights.grasp_lift + s.pieces.grasp_z(piece) + dz
            travel_z = grasp_z + s.heights.hover
            print(f"  target: x={x:.4f} y={y:.4f}  grab {1000 * (grasp_z - s.heights.table_z):.0f} mm above the board")

            arm.goto(x, y, travel_z)
            arm.set_gripper(True)
            vertical(arm, x, y, travel_z, grasp_z)
            arm.set_gripper(False)          # adaptive close; prints the width it felt
            vertical(arm, x, y, grasp_z, travel_z)
            print("  look: is the piece up, held straight?")
            time.sleep(2.0)
            vertical(arm, x, y, travel_z, grasp_z)
            arm.set_gripper(True)
            vertical(arm, x, y, grasp_z, travel_z)

            while True:
                raw = input("grasp [g/u/d/x/y/o/q] > ").strip().lower().split()
                if not raw:
                    continue
                cmd, val = raw[0], (float(raw[1]) / 1000.0 if len(raw) > 1 else 0.002)
                if cmd == "g":
                    break
                if cmd == "u":
                    dz += val
                elif cmd == "d":
                    dz -= val
                elif cmd == "x":
                    dx += float(raw[1]) / 1000.0
                elif cmd == "y":
                    dy += float(raw[1]) / 1000.0
                elif cmd == "o":
                    if len(raw) < 2:
                        print("  usage: o 55   (jaw opening, 0-100)")
                        continue
                    arm.gripper_open = max(10.0, min(100.0, float(raw[1])))
                    open_changed = True
                    print(f"  approach opening -> {arm.gripper_open:.0f}")
                elif cmd == "q":
                    print("\nSave in config/board.local.yaml:")
                    print("pieces:\n  heights_m:")
                    print(f"    {piece}: {s.pieces.height_of(piece) + dz:.3f}")
                    if open_changed:
                        print(f"arm:\n  gripper_open: {arm.gripper_open:.0f}")
                    if dx or dy:
                        ox, oy = (float(v) for v in s.transform.offset)
                        print("# only if EVERY square is off the same way (else recalibrate):")
                        print(f"transform:\n  offset: [{ox + dx:.6f}, {oy + dy:.6f}]")
                    return
                else:
                    print("  g=grab  u/d <mm>=grip higher/lower  x/y <mm>=nudge  o <w>=jaw opening  q=quit")
                    continue
                print(f"  adjust: dz={1000 * dz:+.0f}mm dx={1000 * dx:+.0f}mm dy={1000 * dy:+.0f}mm  (g to try)")
    except ConnectionError:
        print("\nThe motor bus stopped answering — usually motor power, not software.")
        print("Power-cycle the arm (motor power off, wait 5 s, back on) and re-run.")
        print("If it always dies mid-move, suspect the power supply: use the kit's")
        print("adapter plugged straight into the wall, and check the barrel plug is snug.")
    finally:
        arm.disconnect()


if __name__ == "__main__":
    main()
