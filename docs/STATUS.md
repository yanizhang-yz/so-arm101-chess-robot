# Where this project is (pickup notes)

Read this first when you come back. (The session-by-session pairing journal is
kept locally, out of the public repo.) The beginner build guide is
[Home.md](Home.md).

## ⚡ THE PIVOT (Session 23–25)

The project is now **Kid Chess** — a colorful chess game for ages 4–5. Open
`webgame/index.html` (double-click works). Four themes, four opponents **with
personalities and a voice** (browser text-to-speech — every message is spoken
for pre-readers), slow watchable animations, talking hints ("Try your horsey —
it can catch their castle!"), and a spoken end-of-game mini-lesson.

**Session 25 — it's now an iPad app.** The same web game is wrapped with
**Capacitor** into a native iOS/iPadOS Xcode project (`ios/`), configured to
clear Apple's **Kids Category (4+)** review: privacy manifest (no data
collected), export-compliance flag, alpha-free 1024 icon (a pink horsey), no
stray permissions, no network. Verified end-to-end: `npm test` (42 py + 18 node
game tests **and** 27 review-readiness checks) passes; `xcodebuild` compiles a
valid `App.app`; it launches and renders in the iPad simulator. Build/submit
guide: [app-store/README.md](app-store/README.md).

Tests now: `npm test` (game + App-Store readiness) and `.venv/bin/python -m
pytest -q` (the robot core, 35 py tests).

The robot-arm piece-grabbing was shelved after hardware measurement showed the
far corners of a full board sit ~1 cm beyond the arm's dependable reach —
everything below this line is the arm chapter, kept intact for the arm's next
job.

**Done in Session 25:**
- ✅ Scrubbed all `Co-Authored-By: Claude` trailers from history (0 remain on
  `main`), force-pushed. Yani is the sole contributor.
- ✅ Repo is **public**.
- ✅ **GitHub Pages** enabled (main / root) → the game is live at
  <https://yanizhang-yz.github.io/chess-robot/>.

**Left to do — iPad App Store (human-only steps, needs Yani's identity):**
1. Enroll in the **Apple Developer Program ($99/yr)**.
2. Follow [app-store/README.md](app-store/README.md) Part 2 (build + try on a
   real iPad — confirm the spoken hints talk in WKWebView) then Part 3 (create
   the App Store Connect record, age rating 4+ / Made for Kids, **Data Not
   Collected**, privacy-policy URL = the GitHub blob link, archive, upload,
   Submit). Only Yani can enroll and click the final Submit.
3. Before every upload: `npm run test:appstore` (must stay green).

## TL;DR

The **software is done and tested** (stages 1–2, 35 tests). The **arm is
calibrated and moving**. The first real pickup attempt failed — the jaws
couldn't hold a piece — and Session 21 rebuilt grasping around the real causes:
the arm now knows **each piece's height** (a pawn and a rook are grabbed at
different heights), closes the jaws **until it feels the piece** (any width
works), descends **straight down in small steps**, and carries pieces **high
enough to clear the ones standing on the board**. Next: put one pawn on a
square and run `scripts/grasp_test.py` to tune the numbers.

## Housekeeping (done — kept for reference)

✅ **The `Co-Authored-By: Claude` trailers were scrubbed** from all history in
Session 25 (`git filter-branch` msg-filter → 0 remain on `main`), then
force-pushed. Yani is the sole contributor. Keep it that way: no commit in this
repo should carry a Claude co-author trailer.

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
- `point_at.py` — hover over a named square ("which one is e2?"; calibration sanity check)
- `joint_watch.py` — live joint angles + gripper xyz (used to find `table_z`)
- `scan_motor_bus.py` — diagnose a flaky motor bus
