# chessbot — a chess-playing, chess-coaching robot arm

A SO-ARM101 that plays chess against a kid (and, later, talks her through it like
a coach). Built to plug into the LeRobot stack you already run in
`../lerobot-experiments`.

The project is layered so the **brains and logic run with no hardware** — you can
develop and test the whole game on a laptop — and only one module
(`arm.LeRobotArm`) ever touches the physical robot.

> **New here, or not a programmer?** Start with the friendly, step-by-step
> beginner's guide in **[docs/Home.md](docs/Home.md)** — it builds this whole
> project from scratch assuming no coding background.

## Status

**Stages 1–2 done and runnable offline.** `stage1_demo.py` does a single
pick-and-place and `play.py` plays a full game vs. Stockfish — both on a `MockArm`
that prints the choreography (captures, castling, en passant, promotion all
handled). Swap in `--hardware` once the arm is calibrated.

## The plan

| Stage | Goal | State |
|------:|------|-------|
| **1** | Reliable pick-and-place between named squares | ✅ `stage1_demo.py` |
| **2** | Full game vs. Stockfish; you key in her moves | ✅ `play.py` |
| 3 | Camera sees her move automatically (occupancy diff) | — |
| 4 | Voice + Claude coach ("what if I go here?") | — |
| 5 | Kid-level strength (Maia), persona, teaching moments | — |

## Quickstart (offline, no arm needed)

```bash
cd chess-robot
uv venv --python 3.12
uv pip install -e . pytest

# logic tests (board geometry, special-move expansion, calibration math)
.venv/bin/python -m pytest -q

# dry-run a move on the MockArm
.venv/bin/python stage1_demo.py --from e2 --to e4
.venv/bin/python stage1_demo.py --fen "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2" --move e4d5   # a capture
.venv/bin/python stage1_demo.py --fen "rnbqk2r/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1" --move e1g1          # castling
```

### Play a full game (stage 2)

```bash
.venv/bin/python play.py                      # you are White vs. a gentle robot
.venv/bin/python play.py --color black --skill 5
```

Type moves as `e4`, `Nf3`, `O-O`, or `e2e4`; commands: `hint`, `board`,
`takeback`, `resign`. The robot plays on the MockArm (prints its choreography)
until you add `--hardware`.

## How it's structured

```
src/chessbot/
  board.py       square <-> board-plane (x,y) geometry        (pure, tested)
  moves.py       chess move -> primitive ops: carry/remove/    (pure, tested)
                 place_spare, handling captures/castle/EP/promo
  kinematics.py  board->robot transform, incl. mirrored boards (pure, tested)
                 + IKSolver (inverse kinematics via ikpy)
  arm.py         MockArm (offline) | LeRobotArm (SO-ARM101)
  motion.py      pick-and-place choreography over an ArmBackend
  engine.py      Stockfish brain (kid-strength tunable)
  game.py        ChessGame: rules-complete game state + robot_move()
  runtime.py     build the arm/motion stack from Settings (one place)
  config.py      one place for ports, geometry, heights, slots
stage1_demo.py   stage-1 CLI: pick-and-place a single move
play.py          stage-2 CLI: play a full game
scripts/         find_port, calibrate_board, gripper_test,      [hardware]
                 joint_watch, scan_motor_bus
urdf/SO101/      bundled SO-101 URDF (the IK model)            [hardware]
tests/           pure-logic tests — run anywhere
```

## Going to hardware (SO-ARM101 Pro, 12V)

The hardware extra adds `feetech-servo-sdk` (the STS3215 motor driver) and `ikpy`
(pure-Python inverse kinematics) on top of `lerobot`:

```bash
uv pip install -e ".[hardware]"
```

Then follow the step-by-step **[Hardware Setup Checklist](docs/hardware-setup-checklist.md)**:
find the port (`scripts/find_port.py`) → calibrate the joints
(`lerobot-calibrate --robot.type=so101_follower`) → calibrate the board
(`scripts/calibrate_board.py`, which auto-detects a mirrored board via a `flip`)
→ tune the gripper (`scripts/gripper_test.py`) → `stage1_demo.py --from e2 --to e4
--hardware`, then `play.py --hardware`.

The SO-101 URDF the IK reads is bundled at `urdf/SO101/` (already the config
default). If the motor bus glitches ("no status packet"),
`scripts/scan_motor_bus.py <port>` diagnoses it, and `LeRobotArm.connect()` also
auto-retries. Measure your `square_size_m` and `heights` in `board.local.yaml`.

## Safety (it moves near a 5-year-old)

- Strictly **turn-based**: the arm only moves on its own turn, slowly, and she
  keeps hands clear while it does. The 12V kit has real torque — keep `settle_s`
  generous and movements slow while bringing it up.
- Keep a **power cut / e-stop** within reach, mount the arm on the robot's side of
  the board, and **always supervise**.
- `max_relative_target` in the SO-follower config can cap per-step motion — set it
  once you know your ranges.

## Next

- **Stage 3:** a camera that reads her move (occupancy diff) — a `BoardSensor`
  with a Mock-then-real implementation, the same swap pattern as the arm.
- **Stage 4:** the Claude voice coach ("what if I go here?"), grounded in
  Stockfish's analysis.
