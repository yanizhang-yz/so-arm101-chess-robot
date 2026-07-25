# Architecture

The project keeps chess rules, motion planning, calibration, inverse
kinematics, and hardware I/O behind explicit boundaries. The same move plan can
therefore run against a logging backend or the physical follower arm.

## End-to-end pipeline

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

### 1. Legal game state

[`game.py`](../src/chessbot/game.py) owns `ChessGame`. It parses SAN or UCI
input through `python-chess`, rejects illegal moves, applies the human move, and
asks the engine for the robot move. Rules remain independent of hardware.

### 2. Primitive move sequence

[`moves.py`](../src/chessbot/moves.py) converts a legal `chess.Move` into
`Op` values. A normal move becomes `carry`; captures add `remove`; castling
adds a rook carry; en passant removes the captured pawn from its actual square;
promotion can request an off-board spare.

### 3. Board-plane coordinates

[`board.py`](../src/chessbot/board.py) maps algebraic square names to square
centers in meters. `BoardGeometry` is a pure model with no robot-frame or motor
dependency.

### 4. Calibrated robot coordinates and IK

[`kinematics.py`](../src/chessbot/kinematics.py) owns two separate operations:

- `BoardToRobot` fits and applies the calibrated board-plane transform,
  including mirrored-board orientation and optional measured warp.
- `IKSolver` converts a target robot-frame pose to follower joint targets. It
  tries multiple seeds and, at the workspace edge, progressively tilted
  approaches rather than assuming a single vertical solution.

Calibration data stays in the ignored `config/board.local.yaml`, while
`config/board.example.yaml` documents the portable schema.

### 5. Motion choreography

[`motion.py`](../src/chessbot/motion.py) owns `ChessMotion`. It turns primitive
operations into bounded sequences: move above the square, descend in vertical
steps, close or open the gripper, lift to travel clearance, and continue to the
destination. Piece-aware heights and off-board capture/spare locations are
configuration, not chess-rule concerns.

### 6. Backend boundary

[`arm.py`](../src/chessbot/arm.py) defines the `ArmBackend` protocol:
`connect`, `goto`, `set_gripper`, `home`, and `disconnect`.

- `MockArm` records and prints commands. It is deterministic, fast, and safe for
  tests and dry runs.
- `LeRobotArm` translates target poses through IK and sends joint/gripper
  actions through LeRobot. Hardware dependencies are imported only when this
  backend is selected.

The CLIs use `runtime.py` to choose the backend. That keeps `--hardware` as a
boundary decision instead of spreading hardware conditionals through game and
motion code.

## Failure boundaries

- Illegal chess input fails before motion planning.
- Invalid square or calibration data fails before hardware commands.
- Unreachable IK targets fail with the requested Cartesian target.
- Motor-bus retries are bounded; an operator remains responsible for cutting
  power when motion is unsafe.

The architecture makes offline correctness testable, but it does not treat an
IK solution as proof of repeatable physical grasping. See
[Reachability analysis](reachability-analysis.md).
