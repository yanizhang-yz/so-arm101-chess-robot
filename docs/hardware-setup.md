# Hardware Setup

This guide brings up one SO-ARM101 follower arm. Read [Safety](safety.md) and
[Reachability analysis](reachability-analysis.md) first. The full-size-board
result in this repository did not achieve reliable grasping at every square.

## 1. Install

Use Python 3.10 or newer:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[hardware,dev]"
```

Keep this environment active for the remaining commands. In particular,
`scripts/find_port.py` calls `lerobot-find-port`, and joint calibration calls
`lerobot-calibrate`; activation places both installed wrappers on `PATH`.

Run the offline suite before connecting motion hardware:

```bash
python -m pytest -q
python stage1_demo.py --from e2 --to e4
```

## 2. Mount and connect

Clamp the follower arm securely. Keep its power cut accessible and leave the
board empty during bring-up. Connect both USB and the correct power supply.

Find the local serial port:

```bash
python scripts/find_port.py
export FOLLOWER_PORT="/dev/tty.usbmodemFOLLOWER"
```

Replace the placeholder in the shell with the port printed on the local
machine. Never commit that machine-specific value. For bus diagnostics:

```bash
python scripts/scan_motor_bus.py "$FOLLOWER_PORT"
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

## 5. Seed a rough board transform safely

The identity transform in the example file is a schema example, not a safe
motion target. Do not run powered board calibration from those defaults.

With the board empty and the power cut accessible, start the joint watcher:

```bash
python scripts/joint_watch.py
```

The script connects, relaxes the motors, and prints live robot-frame XYZ.
Support the limp arm while placing the gripper tip over the labeled centers
`a1`, `h1`, and `a8`; record the displayed robot-frame X and Y for each point.
Stop the watcher before continuing.

Fit a rough transform interactively:

```bash
python
```

```python
from chessbot.board import BoardGeometry
from chessbot.kinematics import BoardToRobot

squares = ("a1", "h1", "a8")
square_size_m = float(input("measured square size in meters: "))
geometry = BoardGeometry(square_size_m=square_size_m)
robot_points = [
    tuple(map(float, input(f"{square} robot x y: ").split()))
    for square in squares
]
board_points = [geometry.square_center(square) for square in squares]
transform = BoardToRobot.from_correspondences(board_points, robot_points)

print("transform:")
print(f"  scale: {transform.scale:.6f}")
print(f"  theta_rad: {transform.theta_rad:.6f}")
print(f"  flip: {int(transform.flip)}")
print(
    "  offset: "
    f"[{float(transform.offset[0]):.6f}, {float(transform.offset[1]):.6f}]"
)
for square, board_xy, measured in zip(squares, board_points, robot_points):
    predicted = transform.xy(board_xy)
    error_mm = 1000 * (
        (float(predicted[0]) - measured[0]) ** 2
        + (float(predicted[1]) - measured[1]) ** 2
    ) ** 0.5
    print(square, "predicted", predicted, f"residual={error_mm:.1f} mm")
```

Paste the printed `scale`, `theta_rad`, `flip`, and `offset` under `transform`
in the ignored `config/board.local.yaml`. Before applying power, confirm the
square size is measured, the three residuals are small, the scale is plausible,
and the predicted points follow the labeled board orientation. Re-measure
instead of driving the arm if any value or label looks wrong.

## 6. Run driven board calibration

Clear the board again and keep the power cut accessible:

```bash
python scripts/calibrate_board.py
```

This routine keeps the motors powered. It drives the arm to nine poses guessed
from the rough transform; do not touch or hold the arm. At each pose, look
straight down and use the script's `x` or `y` millimeter nudge commands until
the tip is centered, then press Enter to record it. Skip any pose that is
unstable or beyond safe reach.

The tool checks orientation, fits the rigid transform plus a measured warp,
reports residuals, and offers to save the result. Reject an inconsistent fit or
implausible scale.

After calibration, use the point and joint tools to verify above-board poses:

```bash
python scripts/point_at.py --square e2
python scripts/joint_watch.py
```

Do not add pieces until several above-board targets are repeatable.

## 7. Tune height and gripper

Tune open and closed gripper positions in free space:

```bash
python scripts/gripper_test.py
```

Record measured table height and piece heights in the local configuration.
Then place one isolated piece on a central square and run the grasp tuner:

```bash
python scripts/grasp_test.py --square e2 --piece P
```

Keep a hand on the power cut. Stop on board contact, unstable joints, bad
orientation, or loss of motor communication.

## 8. Test one physical move

Only after the mock move and isolated grasp are repeatable:

```bash
python stage1_demo.py --from e2 --to e4 --piece P --hardware
```

Review the complete planned path before running it. A successful central move
does not establish full-board reliability; evaluate corners and clearances
separately before expanding scope.

## 9. Full game boundary

`play.py --hardware` uses the same `LeRobotArm` backend, but it should remain
disabled until every required square, grasp height, capture location, and carry
path is measured as repeatable. The recorded full-size-board setup did not meet
that bar.
