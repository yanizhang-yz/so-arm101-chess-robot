# Kid Chess 🌈 — a colorful chess game for little kids

A friendly, fully offline chess game for ages **4 and up**: big tap-tap pieces,
animated moves, cheerful music, four gentle opponents, and confetti when your
kid wins. No install, no accounts, no ads — one folder of plain HTML.

## Play it

**Open [`webgame/index.html`](webgame/index.html) in any browser** —
double-clicking the file works, nothing to install. (With GitHub Pages enabled
on this repo, it's playable straight from the Pages link too.)

**On an iPad:** the same game is packaged as a native iPad app (via
[Capacitor](https://capacitorjs.com/)) so it can ship on the App Store for other
kids to download. It's fully offline and collects no data — the easy path
through Apple's Kids Category. Build/submit guide:
**[docs/app-store/README.md](docs/app-store/README.md)**. A review-readiness
test suite (`npm run test:appstore`) checks every objective App Store rejection
cause; run everything with `npm test`.

What's inside:

- 🍭🌊🦁🚀 **Four worlds** (Candy, Ocean, Jungle, Space) — pick your colors
  and your floating friends
- 🐣🐰🦊🦉 **Four opponents**, from "moves at random" to "thinks three moves
  ahead" — a 4-year-old can beat the Chick; the Owl makes parents sit up
- 👆 **Tap-tap moves**: tap a piece, the legal squares light up, tap where to
  go — pieces glide, captured pieces pop into your treasure tray
- 🎵 **Music and sound effects** synthesized by the browser itself (one tap to
  mute), 💡 hints, ↩️ an "Oops" takeback button, 👑 automatic pawn-promotion
  party, 🎉 win confetti
- ♟️ **Real chess** — castling, en passant, checks, mates and draws all
  enforced (rules by the excellent [chess.js](https://github.com/jhlywa/chess.js))

For parents who like to peek under the hood: the four opponents live in
[`webgame/ai.js`](webgame/ai.js) (about 100 readable lines), and
`node webgame/ai.test.js` checks them — always-legal moves, finds mate-in-one,
takes the biggest capture, answers fast enough to feel snappy.

Fork it, reskin it, rename the animals — it's yours.

---

# The robot-arm chapter (how this project started)

This repo began as a **chess-playing SO-ARM101 robot arm**. All the software
below works — board math, move choreography, full Stockfish games, calibration
tooling, 40+ tests — and the arm reliably moved above the board. Physically
grabbing pieces was eventually shelved: careful measurement showed a full-size
board spans more than the arm's dependable reach (the far corners sit about a
centimeter past where the stretched arm can hold position). The debugging story
lives in [docs/STATUS.md](docs/STATUS.md), and the arm code stays here for the
arm's next job.

> **New here, or not a programmer?** The step-by-step beginner's guide in
> **[docs/Home.md](docs/Home.md)** builds the robot project from scratch,
> assuming no coding background.

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
