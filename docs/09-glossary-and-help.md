# 9. Glossary & "help, it broke!"

Bookmark this page. Every new word and every common hiccup is explained here in
plain language.

## Glossary (plain English)

- **Terminal** — the text window where you type commands to your computer.
- **Command** — one instruction you type and run by pressing Enter.
- **Python** — the programming language this project is written in.
- **uv** — a helper tool that installs the right Python and project pieces for you.
- **Virtual environment (venv)** — a clean, private toolbox of software just for
  this project, so it never disturbs the rest of your computer.
- **Library / package** — ready-made code someone else wrote that we borrow (like
  python-chess or Stockfish) instead of writing it ourselves.
- **python-chess** — a library that knows all the rules of chess.
- **Stockfish** — a free, world-class chess "brain" that picks moves. We turn its
  strength down for a child.
- **Mock (pretend arm)** — a stand-in that imitates the real thing (it just
  prints what it would do) so you can build and test without hardware.
- **Gripper** — the "hand" at the end of the robot arm that opens and closes to
  grab a piece.
- **Calibration** — teaching the arm about itself and the board, so its movements
  land in the right place.
- **Port** — the name your computer gives the arm when you plug it into USB
  (something like `/dev/tty.usbmodem…`).
- **Inverse kinematics (IK)** — the math that figures out how to bend the arm's
  joints so the gripper reaches a chosen spot. (A library does this for us.)
- **LeRobot** — the free toolkit for talking to the SO-ARM101 robot arm.
- **Repository (repo) / GitHub** — a repo is your project folder with a saved
  history; GitHub is the website that stores a copy online.
- **Commit / push** — *commit* saves a snapshot of your changes; *push* uploads
  those snapshots to GitHub.
- **FEN / SAN / UCI** — standard ways of writing down a chess position (FEN) or a
  move (SAN like `Nf3`, UCI like `g1f3`). You'll see these in the code.

## Help — common problems and fixes

**`uv: command not found`**
The install didn't finish, or the Terminal hasn't noticed it yet. Close the
Terminal, open a new one, and try again. Still stuck? Re-run the install command
from [Set up your computer](04-set-up-your-computer.md#step-a--install-uv-it-manages-python-for-you).

**`brew: command not found`**
You don't have Homebrew yet. Install it from [brew.sh](https://brew.sh), then run
your command again.

**`No module named chessbot` (or similar import errors)**
You're probably not using the project's toolbox. Two things to check: (1) you ran
`uv pip install -e . pytest` *inside the chess-robot folder*, and (2) you're
running Python as `.venv/bin/python …`, not just `python …`.

**`stockfish not found`**
Install it: `brew install stockfish`. The pretend-arm stages work without it; you
only need Stockfish to play a full game.

**A Python version error (it wants 3.10+)**
Recreate the toolbox with the right version: `uv venv --python 3.12`, then
`uv pip install -e . pytest` again.

**`ModuleNotFoundError: No module named 'scservo_sdk'` (during arm calibration)**
That's the Feetech motor driver LeRobot uses to talk to the arm. Install it into
your project venv: `uv pip install feetech-servo-sdk`. (It's now part of the
`.[hardware]` install, so fresh setups get it automatically.)

**The arm: "could not open port" / it won't connect**
Check the USB cable is in, the arm's **power supply is switched on** (USB alone
isn't enough), and re-run the find-port command to confirm the name. To see which
motors answer: `.venv/bin/python scripts/scan_motor_bus.py <your-port>`.

**`ConnectionError: ... no status packet` / a motor stops responding mid-session**
The bus lost contact with one motor (its id is in the message). Almost always
electrical, not software — a 3-pin cable tugged loose (common right after
hand-moving the arm) or a power blip. Scan to confirm:
`.venv/bin/python scripts/scan_motor_bus.py <your-port>`. If all six answer, it
was transient — just re-run your command. If one is missing, re-seat its 3-pin
cable and check the power supply.

**Something else / a scary red error**
Don't worry — red text is just the computer telling you what went wrong. Copy the
**last line** of the error and search it, or bring it to someone helping you. Most
beginner errors are a missing install or being in the wrong folder.

## Where to look in the project

- The main [README](../README.md) — a quicker, more technical overview.
- The code lives in `src/chessbot/` — small files, each doing one job. Open
  [`board.py`](../src/chessbot/board.py) first; it's the friendliest.

---
Back: [Home](Home.md) · You did it — go play a game! ♟️
