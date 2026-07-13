# Where this project is (pickup notes)

Read this first when you come back. The full blow-by-blow is in
[pairing-journal.md](pairing-journal.md); the beginner build guide is
[Home.md](Home.md).

## TL;DR

The **software is done and tested** (stages 1–2, 26 tests). The **arm is
calibrated and moving** — it reaches the right squares and now aims straight down.
The **last thing before the first real pickup** is tuning `grasp_lift` with a real
piece.

## Do this FIRST next session (housekeeping)

**Scrub the `Co-Authored-By: Claude` trailers from git history** — Yani is the
sole contributor. Deferred to a fresh session because it rewrites history and
force-pushes. From the repo root:

```bash
git filter-branch --force --msg-filter 'sed "/Co-Authored-By: Claude/d"' -- --all
git push --force-with-lease --all
# verify: git log --format='%b' | grep -c Co-Authored   # should print 0
```

## What works

- **Offline (no arm):** `stage1_demo.py` (pick-and-place) and `play.py` (full game
  vs. Stockfish) run on a MockArm. `.venv/bin/python -m pytest -q` → 26 passing.
- **Hardware, so far:**
  - Motors calibrated (`lerobot-calibrate`); `connect()` auto-retries bus glitches.
  - IK via **ikpy** + bundled SO-101 URDF; gripper now aimed **straight down**.
  - **Board calibrated** — `config/board.local.yaml` has the transform
    (`scale ~0.92`, `flip: -1` — the board is *mirrored* vs. the arm; finding that
    was the big debug). xy positioning is good ("right area").
  - Height set: `table_z = -0.068` (board surface, ~7 cm below the arm base).
  - Jaw widths tuned: `gripper_open: 80`, `gripper_closed: 5`.

## Next steps (in order)

1. **Test the top-down orientation** (added last, not yet run on hardware) —
   board cleared, hand on the power cut:
   `.venv/bin/python stage1_demo.py --from e2 --to e4 --hardware`.
   The gripper should descend *vertically* and touch cleanly. If it jams, raise
   `table_z` a few mm.
2. **First real pickup:** put a piece on e2, tune `heights.grasp_lift` (how far
   above the surface the jaws close) until it grips and lifts.
3. **Play for real:** `.venv/bin/python play.py --hardware`.
4. **Stage 3 — eyes:** a camera reading her move (occupancy diff), as a
   `BoardSensor` with a Mock-then-real impl (same swap pattern as the arm).
5. **Stage 4 — voice:** the Claude coach, grounded in Stockfish's analysis.

## How the pieces fit

Pure tested core (board, moves, kinematics, engine) → `ArmBackend` interface
(MockArm / LeRobotArm) → motion → game → CLI. Only `arm.LeRobotArm` + the IK touch
hardware. Module map: [README](../README.md#how-its-structured).

## Hardware tools (`scripts/`)

- `find_port.py` — find the arm's USB port
- `calibrate_board.py` — board→robot transform (hold each corner, press ENTER)
- `gripper_test.py` — tune jaw open/close widths
- `joint_watch.py` — live joint angles + gripper xyz (used to find `table_z`)
- `scan_motor_bus.py` — diagnose a flaky motor bus
