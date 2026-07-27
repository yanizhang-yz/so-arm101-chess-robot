# Transition Lessons from the Chess Robot

This case study preserves the distinction between a useful software stack and
an unachieved physical chess goal; the measured boundary is recorded in the
[reachability analysis](reachability-analysis.md).

## Simulation Feasibility Is Not Hardware Reliability

The offline audit found modeled IK candidates within 4 mm for all 64 square
targets, but that result does not establish that the physical arm can hold and
repeat a grasp-ready pose. [Reachability analysis](reachability-analysis.md)

The full-size board's farthest corners measured roughly 1 cm beyond the arm's
dependable position-holding workspace when complete grasp geometry was
considered. [Reachability analysis](reachability-analysis.md)

## Geometry Can Be a Product Requirement

Changing the fixture position can trade one workspace boundary for another, so
board size and arm-to-board placement are product constraints to measure rather
than late software parameters. [Reachability analysis](reachability-analysis.md)

The documented next experiments begin with a smaller board or a systematically
repositioned fixture and require four-corner and full-grid physical checks.
[Reachability analysis](reachability-analysis.md)

## Mock Hardware Is an Interface, Not Proof of Motion

`MockArm` records the same planned backend commands deterministically without
importing hardware dependencies or moving a device; it is a backend-interface
test tool, not proof of physical motion. [Architecture](architecture.md)

The motion tests exercise piece-aware grasp heights, travel clearance, and
stepped descent through `MockArm`, so they demonstrate interface and choreography
behavior rather than real-arm grasp reliability. [Motion tests](../tests/test_motion.py)

## Safety and Stop Conditions Are Engineering Outputs

The operating boundary requires turn-based, supervised physical runs with an
accessible power cut, and it explicitly disallows autonomous camera-triggered
motion in the current system. [Safety](safety.md)

The project stopped before claiming a completed physical game because retries
cannot create missing geometric reach and would add motion and collision
exposure at marginal far-corner poses. [Reachability analysis](reachability-analysis.md)

## How to Present an Incomplete Physical Goal Honestly

Present the repository as a measured case study: it contains calibrated
transforms, motion choreography, and backend separation.
[Architecture](architecture.md)

The documented physical limitation is a reason not to present the repository
as a completed autonomous chess product. [Reachability analysis](reachability-analysis.md)

State the next physical gate precisely: progress from `MockArm` to bounded
above-board poses, then one isolated piece, and only attempt a full move after
repeatable corner holds and safe clearances are measured.
[Reachability analysis](reachability-analysis.md)

## Evidence Links

- [Reachability analysis](reachability-analysis.md) — modeled feasibility,
  physical measurements, stop decision, and next experiments.
- [Safety](safety.md) — supervision, power-cut, and stop-condition boundary.
- [Architecture](architecture.md) — backend separation and the `MockArm`
  interface boundary.
- [Motion tests](../tests/test_motion.py) — deterministic `MockArm` coverage of
  motion choreography; these are not physical-motion tests.
