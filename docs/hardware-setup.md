# Hardware Setup

This guide brings up one SO-ARM101 follower arm. Read [Safety](safety.md) and
[Reachability analysis](reachability-analysis.md) first. The full-size-board
result in this repository did not achieve reliable grasping at every square.

## 1. Install

Use Python 3.10 or newer:

```bash
uv venv --python 3.12
uv pip install -e ".[hardware,dev]"
```

Run the offline suite before connecting motion hardware:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python stage1_demo.py --from e2 --to e4
```

## 2. Mount and connect

Clamp the follower arm securely. Keep its power cut accessible and leave the
board empty during bring-up. Connect both USB and the correct power supply.

Find the local serial port:

```bash
.venv/bin/python scripts/find_port.py
export FOLLOWER_PORT="/dev/tty.usbmodemFOLLOWER"
```

Replace the placeholder in the shell with the port printed on the local
machine. Never commit that machine-specific value. For bus diagnostics:

```bash
.venv/bin/python scripts/scan_motor_bus.py "$FOLLOWER_PORT"
```

## 3. Calibrate follower joints

Run LeRobot calibration and follow its prompts:

```bash
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id=chessbot_follower
```

When the motors relax, support the arm's weight while moving each joint through
the requested range. This project does not require a leader arm.

## 4. Create local configuration

```bash
cp config/board.example.yaml config/board.local.yaml
```

`config/board.local.yaml` is ignored. Set `arm.follower_port` to the local port
and verify the bundled URDF path. Measure the actual square size, board surface
height, piece heights, and gripper values; do not assume the example dimensions
match the physical setup.

## 5. Calibrate the board transform

With the board fixed and empty:

```bash
.venv/bin/python scripts/calibrate_board.py
```

Touch the requested square centers carefully. The tool fits the board-to-robot
transform, detects mirrored orientation, reports the measured span, and can
write local calibration data. Reject clustered points, implausible scale, or a
corner the arm cannot hold safely.

After calibration, use the point and joint tools to verify above-board poses:

```bash
.venv/bin/python scripts/point_at.py e2
.venv/bin/python scripts/joint_watch.py
```

Do not add pieces until several above-board targets are repeatable.

## 6. Tune height and gripper

Tune open and closed gripper positions in free space:

```bash
.venv/bin/python scripts/gripper_test.py
```

Record measured table height and piece heights in the local configuration.
Then place one isolated piece on a central square and run the grasp tuner:

```bash
.venv/bin/python scripts/grasp_test.py --square e2 --piece P
```

Keep a hand on the power cut. Stop on board contact, unstable joints, bad
orientation, or loss of motor communication.

## 7. Test one physical move

Only after the mock move and isolated grasp are repeatable:

```bash
.venv/bin/python stage1_demo.py --from e2 --to e4 --piece P --hardware
```

Review the complete planned path before running it. A successful central move
does not establish full-board reliability; evaluate corners and clearances
separately before expanding scope.

## 8. Full game boundary

`play.py --hardware` uses the same `LeRobotArm` backend, but it should remain
disabled until every required square, grasp height, capture location, and carry
path is measured as repeatable. The recorded full-size-board setup did not meet
that bar.
