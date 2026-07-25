# Safety

The SO-ARM101 is a powered mechanism with enough torque to pinch fingers, strike
pieces, or pull against its mounting. Software checks supplement physical
controls; they do not replace supervision or an accessible power cut.

## Operating boundary

- Use turn-based operation only. The arm moves during an explicit robot turn;
  the human operator stays outside the motion envelope until it stops.
- Keep the power cut or e-stop accessible to the operator throughout every
  physical run.
- Clamp the arm and secure the board before calibration. Stop and recalibrate if
  either moves.
- Supervise every physical run. Do not leave a powered motion sequence
  unattended.
- The current version has no autonomous camera-triggered motion. A camera or
  other sensor must not directly command the arm without a separate reviewed
  safety design.

## Bring-up order

1. Run the test suite.
2. Run the complete move with `MockArm`.
3. Calibrate follower joints with the motors relaxed, supporting the arm.
4. With the board empty, use the relaxed joint watcher to record three labeled
   square centers and fit a sanity-checked rough transform.
5. Run board calibration only after that seed is saved. Board calibration is a
   powered, driven workflow: stay clear and center each pose with software
   nudges rather than touching the arm.
6. Verify bounded above-board targets at low speed with no pieces present.
7. Tune the gripper in free space.
8. Test one isolated piece and one short move.
9. Stop if reach, orientation, clearance, or motor communication is unstable.

Do not jump from offline IK output to a full physical game.

## Motion limits

- Set bounded per-step targets after joint calibration; use the follower
  configuration's relative-target limit where available.
- Keep approach and descent incremental. `ChessMotion` uses stepped vertical
  movement so a bad height does not become one large downward command.
- Maintain travel height above the tallest configured piece plus margin.
- Hardware startup fails closed on an unseeded, non-finite, or non-positive
  board transform. Treat that failure as a calibration stop condition.
- An IK target that misses its tolerance raises an error instead of returning
  the closest joint pose. Stop and revise the target or physical setup.
- Do not use repeated commands to force a marginal far-corner pose.

## Preflight

Before each physical run, confirm:

- mount and board are fixed;
- the local calibration file matches the current setup;
- cables cannot enter the arm's sweep;
- no hands, tools, or loose pieces are in the planned path;
- the operator can cut power without reaching through the motion envelope;
- the next action has already been reviewed with `MockArm`.

See [Hardware setup](hardware-setup.md) for the bring-up sequence and
[Reachability analysis](reachability-analysis.md) for the measured workspace
limit.
