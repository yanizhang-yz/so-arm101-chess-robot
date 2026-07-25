# Reachability Analysis

## Question

Can one fixed SO-ARM101 placement reach, hold position over, and grasp pieces on
every square of a full-size chessboard?

The project separated this into two questions:

1. Can the URDF-based inverse-kinematics model find a candidate pose?
2. Can the physical arm hold and repeat that pose accurately enough to grasp a
   piece?

Those are related measurements, not interchangeable claims.

## What was measured

The offline audit generated a target above the center of each of the 64 squares
using the calibrated board-to-robot transform. The solver tried multiple joint
seeds with a vertical tool approach first, followed by outward tilt near the
workspace edge. Candidate error was checked in Cartesian space.

Hardware bring-up then checked live board calibration, motor motion, end-effector
placement above the board, table height, gripper range, and the distance to the
farthest physical board poses.

## Offline result

The historical session audit recorded an IK candidate with calculated position
error of 4 mm or less for all 64 square targets. In that audit, the gripper was
vertical or tilted no more than 24 degrees on rank 1. This result describes that
calibration and solver run; it is not a timeless guarantee for every board
placement.

The current solver keeps vertical, 8-, 16-, and 24-degree approaches and also
includes a 32-degree fallback for far-corner candidates. That wider search can
produce another modeled candidate, but it does not establish dependable
physical reach or grasp orientation.

Moving the board closer was not an unconditional fix. It improved one edge
while pushing the opposite, near edge toward a different workspace boundary.

## Physical result

The arm reliably moved to poses above the working portion of the board, and the
calibrated XY placement reached the expected area. The farthest corner poses of
the full-size board were different: measurement put them roughly 1 cm beyond
the arm's dependable position-holding reach when the complete grasp geometry
was considered.

Piece grasping also requires more than hovering:

- the jaws must descend vertically without contacting neighboring pieces;
- the wrist must maintain a usable gripper orientation;
- the gripper must close at a piece-specific height;
- the arm must lift and carry the piece with clearance;
- the destination pose must be repeatable, not merely solvable once.

The software implements stepped descent, piece-aware grasp heights, adaptive
closing, and travel clearance. Full-board physical grasp reliability was not
achieved.

## Why retries were not the answer

Multi-start IK and tilted approaches help escape numerical local minima. They
cannot extend link lengths or create position-holding authority outside the
physical workspace. Repeating a marginal far-corner command would add motion
and collision exposure without removing the geometric limit.

The project therefore stopped before claiming a completed physical chess game.
That boundary preserves the useful software while keeping the hardware result
honest.

## Next experiments

Two experiments would test the limitation directly:

1. **Smaller board:** reduce square size and board diagonal, repeat the 64-pose
   audit, then measure physical repeatability at all four corners before adding
   pieces.
2. **Repositioned fixture:** systematically vary arm-to-board translation and
   rotation, rejecting placements that recover the far edge by losing the near
   edge. A raised or angled fixture should be evaluated with the same four-corner
   and full-grid protocol.

Either experiment should proceed from `MockArm` to above-board poses, then to a
single isolated piece. A full move is warranted only after repeatable corner
holds and safe clearances are measured.
