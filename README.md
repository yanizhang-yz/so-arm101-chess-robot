# chessbot — a chess-playing, chess-coaching robot arm

A SO-ARM101 that plays chess against a kid (and, later, talks her through it like
a coach). Built to plug into the LeRobot stack you already run in
`../lerobot-experiments`.

The project is layered so the **brains and logic run with no hardware** — you can
develop and test the whole game on a laptop — and only one module
(`arm.LeRobotArm`) ever touches the physical robot.

## Status

**Stage 1 scaffolded and runnable offline.** `stage1_demo.py` plans and "executes"
piece moves (including captures, castling, en passant, promotion) on a `MockArm`
that prints the choreography. Swap in `--hardware` once the arm is calibrated.

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
  kinematics.py  board->robot similarity transform (pure,      (transform tested)
                 tested) + IKSolver wrapping LeRobot's RobotKinematics
  arm.py         MockArm (offline) | LeRobotArm (SO-ARM101)
  motion.py      pick-and-place choreography over an ArmBackend
  engine.py      Stockfish brain (kid-strength tunable)
  game.py        ChessGame: rules-complete game state + robot_move()
  runtime.py     build the arm/motion stack from Settings (one place)
  config.py      one place for ports, geometry, heights, slots
stage1_demo.py   stage-1 CLI: pick-and-place a single move
play.py          stage-2 CLI: play a full game
scripts/         find_port.py, calibrate_board.py             [hardware]
tests/           pure-logic tests — run anywhere
```

## Going to hardware (SO-ARM101 Pro, 12V)

The hardware path needs `lerobot` + `placo`. Two options:

- **Reuse your existing env:** run the hardware scripts with
  `../lerobot-experiments/.venv/bin/python` (lerobot 0.5.1 is already there; just
  `uv pip install chess` into it), **or**
- install here: `uv pip install -e ".[hardware]"` (pulls torch — slower).

Then:

1. **Find the port:** `python scripts/find_port.py` → put the `/dev/tty.usbmodem…`
   into `config/board.local.yaml` (copy from `config/board.example.yaml`).
2. **Motors + calibration:** follow LeRobot's SO-101 guide
   (`lerobot-setup-motors` / `lerobot-calibrate --robot.type=so101_follower`).
   If the bus misbehaves, `../lerobot-experiments/m0-bringup/scan_motor_bus.py`
   diagnoses it.
3. **Point at a URDF:** set `arm.urdf_path` (try `chessbot.kinematics.find_urdf()`;
   otherwise grab the SO-101 URDF from the SO-ARM100 repo / your lerobot-repo).
4. **Calibrate the board frame:** `python scripts/calibrate_board.py`, place the
   gripper on the four corner squares when prompted, paste the printed `transform:`
   block into `config/board.local.yaml`.
5. **Run for real:** `python stage1_demo.py --from e2 --to e4 --hardware`.

Measure your board's `square_size_m` and the `heights` (table surface, hover) and
put them in `board.local.yaml` too. The `gripper_open/closed` values and the
`home()` pose in `arm.py` are starting guesses — tune them on your arm.

## Safety (it moves near a 5-year-old)

- Strictly **turn-based**: the arm only moves on its own turn, slowly, and she
  keeps hands clear while it does. The 12V kit has real torque — keep `settle_s`
  generous and movements slow while bringing it up.
- Keep a **power cut / e-stop** within reach, mount the arm on the robot's side of
  the board, and **always supervise**.
- `max_relative_target` in the SO-follower config can cap per-step motion — set it
  once you know your ranges.

## Next

- Wire `engine.ChessBrain` into a game loop (stage 2): she moves → you key it in →
  robot replies. No camera yet.
- Then occupancy-diff vision (stage 3) and the Claude voice coach (stage 4).
