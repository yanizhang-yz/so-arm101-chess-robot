# Hardware Setup Checklist

Use this only after reading the full [hardware setup](hardware-setup.md),
[safety boundary](safety.md), and
[reachability analysis](reachability-analysis.md).

- [ ] Install the hardware and development extras.
- [ ] Run all tests and a complete `MockArm` move.
- [ ] Clamp the arm, clear the workspace, and make the power cut accessible.
- [ ] Find the follower port and keep its machine-specific value local.
- [ ] Calibrate follower joints while supporting the relaxed arm.
- [ ] Copy `config/board.example.yaml` to the ignored local configuration.
- [ ] Measure square size, table height, piece heights, and gripper range.
- [ ] Calibrate the board transform without moving the fixture afterward.
- [ ] Verify several empty, above-board poses at low speed.
- [ ] Tune the gripper in free space.
- [ ] Test one isolated central piece.
- [ ] Run one short physical move only after its mock plan is reviewed.
- [ ] Stop on unstable reach, bad orientation, board contact, or bus errors.
- [ ] Do not claim full-board operation until every required pose and grasp is
  repeatable.
