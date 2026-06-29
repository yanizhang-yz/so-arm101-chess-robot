# Hardware Setup Checklist (the "tomorrow" runbook)

A short, do-it-in-order checklist for connecting the real SO-ARM101 to the
program. The friendly *why* behind each step is on the
[real-arm page](07-step-4-the-real-arm.md); this page is just the steps and
commands. **Run everything from inside the `chess-robot` folder.**

> ⚠️ **Read the [safety rules](07-step-4-the-real-arm.md#safety-first) first:**
> turn-based, slow, hands clear, a power cut within reach, always supervised.

> 💡 **No leader arm needed.** This project only uses the **follower** (the arm
> that acts). Both calibration steps below (C and E) are done by **moving the
> follower by hand** while its motors are switched off — your hand does the job
> the leader arm does in teleoperation projects. The arm goes limp when the motors
> are off, so support its weight.

## A. Physical setup (no computer)

1. Clamp the arm firmly to the desk on **its** side of the board.
2. Place the board so **every square is within easy reach** of the gripper.
3. Once positioned, **don't move the arm or board again** — if either shifts, you
   re-do the board calibration (Step E).

## B. Connect and find the arm

4. One-time install of the hardware tools:
   ```bash
   uv pip install -e ".[hardware]"
   ```
5. Plug in the arm: **USB cable *and* its power supply** (USB alone isn't enough).
6. Find its port:
   ```bash
   python scripts/find_port.py
   ```
   Copy the `/dev/tty.usbmodem…` it prints.
7. Create your settings file and paste the port in:
   ```bash
   cp config/board.example.yaml config/board.local.yaml
   ```
   Open `config/board.local.yaml`, set `arm.follower_port` to that port.

## C. Calibrate the arm's joints (one-time)

8. Run LeRobot's calibration and follow the on-screen prompts. The motors switch
   **off** so you move the follower **by hand** (support its weight — no leader
   arm involved): pose it in the middle of its range, then sweep each joint to its
   limits while it records.
   ```bash
   lerobot-calibrate --robot.type=so101_follower --robot.port=YOUR_PORT --robot.id=chessbot_follower
   ```

## D. Tell the program about the board + arm model

9. In `config/board.local.yaml` set:
   - `square_size_m` — measure one square with a ruler (e.g. `0.04` for 4 cm)
   - `arm.urdf_path` — already set to the bundled `urdf/SO101/so101_new_calib.urdf`
     (the arm's 3-D model the IK needs); no action needed
   - `heights.table_z` — height of the board surface (you'll fine-tune this)

   > The IK runs on **ikpy** (pure Python). If you ever see a `placo` error,
   > you're on an old setup — reinstall with `uv pip install -e ".[hardware]"`.

## E. Calibrate the board position

10. Teach the program where the board sits:
    ```bash
    python scripts/calibrate_board.py
    ```
    It relaxes the arm; gently place the gripper on the **center of each corner
    square** when prompted (a1, h1, a8, h8). It prints a `transform:` block.
11. Paste that `transform:` block into `config/board.local.yaml`.

## F. Tune the grip + test ONE move first

12. Adjust `arm.gripper_open` / `arm.gripper_closed` so it holds a piece without
    crushing or dropping it.
13. **Test a single move slowly before risking a whole game:**
    ```bash
    python stage1_demo.py --from e2 --to e4 --hardware
    ```
    Watch it pick up and place. If it's off, nudge the numbers and repeat.

## G. Play for real

14. ```bash
    python play.py --hardware
    ```
    The same game you already played — now the real arm makes its moves. 🎉

---

**You write no new code for any of this.** `LeRobotArm` already lives in
`src/chessbot/arm.py`, and `--hardware` swaps it in for the MockArm. Tomorrow is
**all configuration + calibration.**
