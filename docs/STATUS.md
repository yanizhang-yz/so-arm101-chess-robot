# Where this project is (pickup notes)

Read this first when you come back. The full blow-by-blow is in
[pairing-journal.md](pairing-journal.md); the beginner build guide is
[Home.md](Home.md).

## TL;DR

The **software is done and tested** (stages 1–2, 35 tests). The **arm is
calibrated and moving**. The first real pickup attempt failed — the jaws
couldn't hold a piece — and Session 21 rebuilt grasping around the real causes:
the arm now knows **each piece's height** (a pawn and a rook are grabbed at
different heights), closes the jaws **until it feels the piece** (any width
works), descends **straight down in small steps**, and carries pieces **high
enough to clear the ones standing on the board**. Next: put one pawn on a
square and run `scripts/grasp_test.py` to tune the numbers.

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
  vs. Stockfish) run on a MockArm. `.venv/bin/python -m pytest -q` → 35 passing.
- **Hardware, so far:**
  - Motors calibrated (`lerobot-calibrate`); `connect()` auto-retries bus glitches.
  - IK via **ikpy** + bundled SO-101 URDF; gripper aimed **straight down**, with
    multi-start (escapes bad local minima that used to land 5 cm off) and a small
    outward tilt fallback for the far rank at the edge of reach.
  - **Board calibrated** — `config/board.local.yaml` has the transform
    (`scale ~0.92`, `flip: -1` — the board is *mirrored* vs. the arm; finding that
    was the big debug). xy positioning is good ("right area").
  - Height set: `table_z = -0.068` (board surface, ~7 cm below the arm base).
  - Jaw range: `gripper_open: 80`, `gripper_closed: 5` — but the grip now stops
    itself on contact, so `gripper_closed` is just the floor.
  - **Grasping is piece-aware** (Session 21): per-piece heights in config
    (`pieces.heights_m` — measure yours!), adaptive close-until-contact
    (verified on hardware in air: no false contact, detects an empty grab),
    stepped vertical descent, travel height that clears a standing king.
  - **Reach audit (offline, all 64 squares):** every square solves to ≤4 mm with
    the gripper vertical or tilted ≤24° on rank 1; the board placement is
    near-optimal — do NOT move the board closer (the near rank would fall out of
    reach on the other side).

## Next steps (in order)

1. **Tune the grab on a real piece** — put ONE pawn on e2, clear its neighbors,
   hand on the power cut:
   `.venv/bin/python scripts/grasp_test.py --square e2 --piece P`.
   Use `u/d` (grip higher/lower), `x/y` (nudge sideways) until it lifts cleanly,
   then `q` prints the lines to save in `config/board.local.yaml`.
   Measure your pieces base-to-tip with a ruler and put the real heights in
   `pieces.heights_m` (defaults are guesses for a 40 mm-square set).
2. **Full move on hardware:**
   `.venv/bin/python stage1_demo.py --from e2 --to e4 --hardware`
   (add `--piece N` etc. when testing taller pieces).
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
- `grasp_test.py` — tune the grab on a real piece (heights + sideways nudges)
- `joint_watch.py` — live joint angles + gripper xyz (used to find `table_z`)
- `scan_motor_bus.py` — diagnose a flaky motor bus
