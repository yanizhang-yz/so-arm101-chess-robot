#!/usr/bin/env python
"""Calibrate the board -> robot transform by DRIVING, not holding (HARDWARE).

CLEAR THE BOARD FIRST — the arm dips low over each reference square.

For each of 9 squares, the arm moves to where it currently *believes* the
square center is and hovers just above the board. You look straight down at it
and nudge with millimeter commands until the jaw tip is over the center:

    x 3    move +3 mm in robot x        x -2   move the other way
    y 2    move +2 mm in robot y
    ENTER  looks centered — record it and move on

Why driving beats holding: the arm calibrates in exactly the pose it plays in
(gripper pointing down, motors on), so its internal quirks — model error,
servo sag, where the "tip" really is — are baked into the recorded points and
cancel out at play time. Hand-held calibration graded your touches against the
arm's imperfect self-model and blamed you for the difference (~2 cm that never
went away, no matter how carefully you touched).

It then fits the rigid transform PLUS a smooth quadratic warp over the 9
points (the leftover distortion), reports per-square quality in mm, and offers
to save into config/board.local.yaml. Raw points go to outputs/.

Needs an existing rough transform in config (yours points "roughly right" —
that's plenty; the nudges do the rest).
"""
from __future__ import annotations

import numpy as np

from chessbot.config import ROOT, load
from chessbot.kinematics import BoardToRobot
from chessbot.runtime import build_arm

# Nine squares: the rim (walked in order) plus the center. Nine well-spread
# anchors are what the quadratic warp needs to pin down the arm's distortion.
REFERENCE_SQUARES = ["a1", "d1", "h1", "h4", "h8", "e8", "a8", "a4", "d4"]

# Where each square is, physically — stand on WHITE's side (the side whose
# pieces start on ranks 1 and 2; mark a1 with a sticker so every calibration
# agrees with the last one).
WHERE = {
    "a1": "NEAR-LEFT corner square (your sticker)",
    "d1": "near edge, 4th square from the left",
    "h1": "NEAR-RIGHT corner square",
    "h4": "right edge, 4th square from the near side",
    "h8": "FAR-RIGHT corner square (diagonal from a1)",
    "e8": "far edge, 5th square from the left",
    "a8": "FAR-LEFT corner square",
    "a4": "left edge, 4th square from the near side",
    "d4": "middle of the board, a bit left and near of center",
}

TOUCH_ABOVE_M = 0.015  # nudge height: low enough to judge centering by eye


def show_map(target: str) -> None:
    """A little map of the board from White's side, # marking the square."""
    print("        (far side)")
    for rank in range(8, 0, -1):
        row = "".join(" #" if f + str(rank) == target else " ." for f in "abcdefgh")
        print(f"   {rank} |{row}")
    print("      " + " ".join("abcdefgh"))
    print("        (your side = White's side)")


def nudge_loop(arm, x: float, y: float, z: float) -> tuple[float, float]:
    """Let the user walk the tip onto the square center; returns the final xy."""
    while True:
        raw = input("   nudge [x/y <mm>, ENTER=centered] > ").strip().lower().split()
        if not raw:
            return x, y
        try:
            axis, mm = raw[0], float(raw[1])
        except (IndexError, ValueError):
            print("   like this:  x 3   or   y -2   (mm); plain ENTER when centered")
            continue
        if axis == "x":
            x += mm / 1000.0
        elif axis == "y":
            y += mm / 1000.0
        else:
            print("   x or y only")
            continue
        arm.goto(x, y, z)


def main() -> None:
    settings = load()
    geo = settings.geometry
    if settings.arm.follower_port == "TODO":
        raise SystemExit("Set arm.follower_port in config/board.local.yaml first.")

    z_touch = settings.heights.table_z + TOUCH_ABOVE_M
    z_travel = settings.heights.table_z + settings.heights.hover + 0.03

    print("Driving calibration. CLEAR THE BOARD — the arm dips low over each square.")
    print("Stand on WHITE's side: a1 = near-left (sticker!), h1 = near-right,")
    print("a8 = far-left, h8 = far-right.\n")

    arm = build_arm(settings, hardware=True)
    arm.connect()
    board_pts, robot_pts = [], []
    try:
        for sq in REFERENCE_SQUARES:
            print(f"\n=== {sq}: {WHERE[sq]} ===")
            show_map(sq)
            gx, gy = (float(v) for v in settings.transform.xy(geo.square_center(sq)))
            arm.goto(gx, gy, z_travel)
            arm.goto(gx, gy, z_touch)
            print("   arm is low over its GUESS of the center — nudge it onto the center.")
            fx, fy = nudge_loop(arm, gx, gy, z_touch)
            board_pts.append(geo.square_center(sq))
            robot_pts.append((fx, fy))
            arm.goto(fx, fy, z_travel)
        arm.home()
    except ConnectionError:
        print("\nThe motor bus stopped answering — power-cycle the arm and re-run.")
        return
    finally:
        arm.disconnect()

    t = BoardToRobot.with_warp(board_pts, robot_pts)
    residuals_mm = [1000.0 * float(np.hypot(*(t.xy(b) - r))) for b, r in zip(board_pts, robot_pts)]
    rms = float(np.sqrt(np.mean(np.square(residuals_mm))))

    import json
    import os
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/last_calibration.json", "w") as f:
        json.dump({
            "method": "driven",
            "squares": REFERENCE_SQUARES,
            "board_pts": [list(p) for p in board_pts],
            "robot_pts": [list(p) for p in robot_pts],
            "residuals_mm": [round(r, 1) for r in residuals_mm],
            "scale": round(t.scale, 6), "theta_rad": round(t.theta_rad, 6),
            "flip": int(t.flip),
            "offset": [round(float(t.offset[0]), 6), round(float(t.offset[1]), 6)],
            "warp_x": [float(v) for v in t.warp_x], "warp_y": [float(v) for v in t.warp_y],
            "warp_box": [float(v) for v in t.warp_box],
        }, f, indent=2)
    print("\n(raw points saved to outputs/last_calibration.json)")

    print("\nFit quality (how far each recorded square is from the fitted map):")
    for sq, r in zip(REFERENCE_SQUARES, residuals_mm):
        print(f"   {sq}: {r:5.1f} mm")
    print(f"   rms: {rms:5.1f} mm  (driven capture should come out under ~5 mm)")
    if rms > 15:
        print("\n⚠️  Too inconsistent to save — one square was probably nudged onto the")
        print("    wrong center (follow the maps). Run it again; it goes fast.")
        return

    if input("\nSave into config/board.local.yaml now? [y/N] ").strip().lower() == "y":
        import yaml
        path = ROOT / "config" / "board.local.yaml"
        data = yaml.safe_load(path.read_text()) if path.exists() else {}
        data["transform"] = {
            "scale": float(f"{t.scale:.6f}"), "theta_rad": float(f"{t.theta_rad:.6f}"),
            "flip": int(t.flip),
            "offset": [float(f"{t.offset[0]:.6f}"), float(f"{t.offset[1]:.6f}")],
            "warp_x": [float(v) for v in t.warp_x],
            "warp_y": [float(v) for v in t.warp_y],
            "warp_box": [float(v) for v in t.warp_box],
        }
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        print(f"saved -> {path}")
    else:
        print("NOT saved — re-run and answer y when you're happy with the fit.")


if __name__ == "__main__":
    main()
