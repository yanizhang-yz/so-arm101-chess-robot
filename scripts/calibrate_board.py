#!/usr/bin/env python
"""Calibrate the board -> robot transform (HARDWARE; run once after setup).

Disables the arm's torque so you can move the gripper by hand. For each corner
square: rest the gripper tip on the CENTER of that square, then press ENTER to
record. You control the timing — take as long as you need. The script shows the
live position and how far it is from the previous corner, and refuses to record a
point that's too close to the last one (which would mean the arm hadn't moved).

    python scripts/calibrate_board.py

Touch six squares — the four corners plus two mid-board (extra points average
out hand-placement noise). It then fits a transform, shows how far off each
recorded square is from the fit (in mm — your calibration quality, square by
square), and prints YAML for config/board.local.yaml (raw points go to
outputs/).

Touching well matters more than touching fast: rest the very TIP of the closed
jaws on the center of the square, let go so the arm isn't being pushed
sideways, and only then press ENTER.
"""
from __future__ import annotations

import select
import sys

import numpy as np

from chessbot.arm import LeRobotArm
from chessbot.config import ROOT, load
from chessbot.kinematics import BoardToRobot

# Four corners span the board; two mid-board squares let the least-squares fit
# average out per-touch noise instead of trusting each corner completely.
# Ordered as a walk around the rim, then into the middle.
REFERENCE_SQUARES = ["a1", "h1", "h8", "a8", "d4", "e5"]
MIN_GAP_M = 0.05  # refuse a point within 5 cm of the previous one (arm hadn't moved)

# Where each square is, physically — stand on WHITE's side (the side whose
# pieces start on ranks 1 and 2; mark a1 with a sticker so every calibration
# agrees with the last one).
WHERE = {
    "a1": "NEAR-LEFT corner square (your sticker)",
    "h1": "NEAR-RIGHT corner square (same edge as a1)",
    "h8": "FAR-RIGHT corner square (diagonal from a1)",
    "a8": "FAR-LEFT corner square",
    "d4": "middle, a bit LEFT and NEAR of center",
    "e5": "middle, a bit RIGHT and FAR of center",
}


def show_map(target: str) -> None:
    """A little map of the board from White's side, # marking the square to touch."""
    print("        (far side)")
    for rank in range(8, 0, -1):
        row = "".join(
            " #" if f + str(rank) == target else " ."
            for f in "abcdefgh"
        )
        print(f"   {rank} |{row}")
    print("      " + " ".join("abcdefgh"))
    print("        (your side = White's side)")


def _dist(a, b) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def capture(arm: LeRobotArm, square: str, prev: tuple[float, float] | None) -> tuple[float, float]:
    """Show live position; record on ENTER. Rejects points too close to `prev`."""
    print(f"\n=== {square}: {WHERE.get(square, '')} ===")
    show_map(square)
    print(f"Rest the gripper tip on the CENTER of {square}, then press ENTER.")
    while True:
        x, y = arm.ee_xy()
        note = f"  ({_dist((x, y), prev) * 100:.0f} cm from last)" if prev else ""
        print(f"   {square}: ({x:+.3f}, {y:+.3f}){note}      ", end="\r", flush=True)
        if select.select([sys.stdin], [], [], 0.2)[0]:
            sys.stdin.readline()
            if prev and _dist((x, y), prev) < MIN_GAP_M:
                print(f"\n   only {_dist((x, y), prev) * 100:.0f} cm from the last corner — "
                      "move to the real corner and press ENTER again.")
                continue
            print(f"\n   recorded {square}: ({x:+.3f}, {y:+.3f})")
            return (float(x), float(y))


def main() -> None:
    settings = load()
    geo = settings.geometry
    a = settings.arm
    if a.follower_port == "TODO" or a.urdf_path == "TODO":
        raise SystemExit("Set arm.follower_port and arm.urdf_path in config/board.local.yaml first.")

    arm = LeRobotArm(port=a.follower_port, urdf_path=a.urdf_path, robot_id=a.robot_id)
    arm.connect()
    arm.relax()
    print("Torque off — move the arm by hand. Take your time; press ENTER at each square.")
    print("Tip: rest the jaw TIP on the square center, take your hand away, THEN press ENTER.")
    print("\nOrientation: stand on WHITE's side (pieces on ranks 1-2 in front of you).")
    print("a1 = near-left, h1 = near-right, a8 = far-left, h8 = far-right.")
    print("Mark a1 with a sticker so every calibration uses the same corner!")

    board_pts, robot_pts = [], []
    prev: tuple[float, float] | None = None
    try:
        for sq in REFERENCE_SQUARES:
            pt = capture(arm, sq, prev)
            board_pts.append(geo.square_center(sq))
            robot_pts.append(pt)
            prev = pt
    finally:
        arm.disconnect()

    pts = np.array(robot_pts)
    span = max(_dist(p, q) for p in pts for q in pts)
    t = BoardToRobot.from_correspondences(board_pts, robot_pts)

    # How far each recorded square sits from the fitted transform — the honest
    # quality report. Big residual on ONE square = that touch was off; big
    # residuals everywhere = re-run and touch more carefully.
    residuals_mm = [1000.0 * _dist(t.xy(b), r) for b, r in zip(board_pts, robot_pts)]

    import json
    import os
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/last_calibration.json", "w") as f:
        json.dump({
            "squares": REFERENCE_SQUARES,
            "board_pts": [list(p) for p in board_pts],
            "robot_pts": [list(p) for p in robot_pts],
            "residuals_mm": [round(r, 1) for r in residuals_mm],
            "span_cm": round(span * 100, 2),
            "scale": round(t.scale, 6),
            "theta_rad": round(t.theta_rad, 6),
            "flip": int(t.flip),
            "offset": [round(float(t.offset[0]), 6), round(float(t.offset[1]), 6)],
        }, f, indent=2)

    print(f"\nRecorded-point spread: {span * 100:.1f} cm  (expect ~40 cm corner-to-corner).")
    print("(raw points saved to outputs/last_calibration.json)")
    if span < 0.10 or not (0.5 <= t.scale <= 2.0):
        print(f"\n⚠️  These look WRONG (scale {t.scale:.3f}, spread {span * 100:.1f} cm).")
        print("    The points came out clustered — re-run, touching distinct squares.")
        return

    print("\nFit quality (distance between each touch and the fitted grid):")
    for sq, r in zip(REFERENCE_SQUARES, residuals_mm):
        flag = "  <-- this touch looks off, consider re-running" if r > 15 else ""
        print(f"   {sq}: {r:5.1f} mm{flag}")
    rms = float(np.sqrt(np.mean(np.square(residuals_mm))))
    print(f"   rms: {rms:5.1f} mm  (under ~8 mm is a good hand calibration;")
    print("        the jaws forgive a few mm — grasp_test.py x/y trims the rest)")
    if rms > 12:
        print("\n⚠️  This fit is TOO SLOPPY to use — do NOT paste it. Usual causes:")
        print("    a square touched out of order (follow the map!), or the touch")
        print("    point pushed off-center. Run the script again.")
        return

    print("\n--- the new transform ---\n")
    print("transform:")
    print(f"  scale: {t.scale:.6f}")
    print(f"  theta_rad: {t.theta_rad:.6f}")
    print(f"  flip: {int(t.flip)}")
    print(f"  offset: [{t.offset[0]:.6f}, {t.offset[1]:.6f}]")

    if input("\nSave into config/board.local.yaml now? [y/N] ").strip().lower() == "y":
        import yaml
        path = ROOT / "config" / "board.local.yaml"
        data = yaml.safe_load(path.read_text()) if path.exists() else {}
        data["transform"] = {
            "scale": float(f"{t.scale:.6f}"), "theta_rad": float(f"{t.theta_rad:.6f}"),
            "flip": int(t.flip),
            "offset": [float(f"{t.offset[0]:.6f}"), float(f"{t.offset[1]:.6f}")],
        }
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        print(f"saved -> {path}")
    else:
        print("NOT saved — paste the transform block above into config/board.local.yaml yourself.")


if __name__ == "__main__":
    main()
