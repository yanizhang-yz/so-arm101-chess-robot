# Contributing

## Development setup

Use Python 3.10 or newer and install the development dependencies:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Keep changes focused and include tests for behavior changes.

## Offline coverage

Logic, planning, calibration math, and motion changes must have offline coverage
using `MockArm` or pure functions. Tests must not require a connected robot,
motor bus, Stockfish process, or machine-local configuration.

## Hardware and safety changes

For a physical-hardware change, describe in the pull request:

- which arm, motion, calibration, or gripper boundary changes;
- the `MockArm` or offline checks run first;
- the supervised hardware procedure used, if any;
- relevant reach, collision, power-cut, and failure-mode considerations; and
- any behavior that remains unverified on physical hardware.

Do not weaken the turn-based, supervised operating boundary without a separate
safety design and review.

## Public-tree hygiene

Never commit local calibration, captured outputs, personal paths, or concrete
device identifiers. Keep measured setup values in ignored local files and use
portable placeholders in examples. Run the full test suite before submitting a
change; it includes the public-tree privacy guard.
