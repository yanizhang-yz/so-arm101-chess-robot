# SO-ARM101 Chess Robot

A tested chess-playing robot stack for the SO-ARM101: board calibration,
coordinate transforms, inverse kinematics, move choreography, Stockfish game
logic, mock hardware, and real-arm bring-up.

## Project Result

The software path works offline and the arm reliably reached poses above the
board. Physical piece grasping across a full-size board was shelved after
measurement showed that the far corners exceed the arm's dependable
position-holding workspace. This repository keeps the working software and the
reachability analysis as an engineering case study rather than claiming a
completed physical game.

## Evidence

- The pure Python robotics suite covers board geometry, transforms, move
  expansion, motion choreography, game rules, and the mock backend.
- `MockArm` runs the same motion plan as the hardware backend without importing
  LeRobot or moving a device.
- The recorded offline IK audit found candidates within 4 mm for all 64 square
  poses when outward wrist tilt was allowed at the workspace edge.
- Hardware bring-up confirmed motion above the board, but measurements placed
  the far physical corners roughly 1 cm beyond dependable reach. Reliable
  full-board grasping was not achieved.

## Architecture

The control path is:

```text
UCI/user move
-> python-chess legal move
-> primitive move sequence
-> board-plane coordinates
-> calibrated board-to-robot transform
-> inverse kinematics
-> ArmBackend
-> MockArm or LeRobotArm
```

See [Architecture](docs/architecture.md) for module ownership and data flow.

## Quickstart with MockArm

Python 3.10 or newer is required. The default path is offline and does not need
the arm or LeRobot.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"

.venv/bin/python stage1_demo.py --from e2 --to e4
.venv/bin/python stage1_demo.py --move e4d5 \
  --fen "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
```

The first command prints the carry sequence recorded by `MockArm`. The second
uses a legal position so capture expansion is included.

## Test command

```bash
.venv/bin/python -m pytest -q
```

All tests are hardware-independent. The public-tree guard also prevents
machine-specific ports, personal paths, and personal relationship wording from
being committed.

## Hardware status

The follower arm, motor bus, joint calibration, board transform, and above-board
motion were brought up. Piece-aware heights, stepped descent, adaptive gripper
closing, and high-clearance carry motion are implemented. These are useful
building blocks, but they did not establish reliable grasp-and-place operation
over the entire physical board.

Follow [Hardware setup](docs/hardware-setup.md) for a controlled bring-up.

## Safety boundary

Physical operation is turn-based and supervised. The operator stays outside the
motion envelope, keeps an accessible power cut, begins with `MockArm`, and
tests bounded targets slowly after calibration. The current system does not
trigger motion autonomously from a camera.

Read [Safety](docs/safety.md) before enabling `--hardware`.

## Measured limitation

Offline IK feasibility and physical repeatability are different claims. The
historical audit recorded calculated error of 4 mm or less across all 64 square
poses using vertical or tilted candidates. On hardware, the far corners of the
full-size board were still about 1 cm beyond the arm's dependable
position-holding workspace. Software retries could not create missing geometric
reach, so the project stopped before making an unsafe or unreliable full-board
grasp claim.

The measurements and next experiments are in
[Reachability analysis](docs/reachability-analysis.md).

## Repository layout

```text
src/chessbot/
  game.py          legal game state and robot turns
  moves.py         chess moves to carry/remove/place operations
  board.py         square centers in board-plane coordinates
  kinematics.py    calibration transform and inverse kinematics
  motion.py        pick, place, capture, and promotion choreography
  arm.py           ArmBackend, MockArm, and LeRobotArm
  runtime.py       selects the offline or physical backend
scripts/           calibration, diagnostics, and hardware bring-up tools
config/            portable example configuration
urdf/SO101/        robot model used by inverse kinematics
tests/             offline robotics and publication regression tests
stage1_demo.py     one-move mock or hardware demonstration
play.py            full game loop
```

## History

The earlier consumer chess interface now lives in the separate
[kid-chess repository](https://github.com/yanizhang-yz/kid-chess). This
repository is focused on the robot-control engineering work.
