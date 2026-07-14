"""Arm backends. Everything else talks to an ArmBackend; swap the implementation
to go from desk-checking logic to driving the real SO-ARM101.

  MockArm     records every motion to a log and prints it. No hardware, no
              heavy dependencies — what stage1_demo uses by default and what the
              tests exercise.
  LeRobotArm  drives a physical SO-ARM101 follower via LeRobot 0.5.x: a
              robot-frame goto() -> IK -> SOFollower.send_action(). The lerobot
              import is lazy, so importing this module never requires hardware.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class ArmBackend(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def goto(self, x: float, y: float, z: float) -> None: ...
    def set_gripper(self, open_: bool) -> float | None: ...
    def home(self) -> None: ...


@dataclass
class MockArm:
    """Offline stand-in: logs motions so you can verify the choreography by eye."""

    verbose: bool = True
    log: list[tuple] = field(default_factory=list)

    def connect(self) -> None:
        self._emit(("connect",))

    def disconnect(self) -> None:
        self._emit(("disconnect",))

    def goto(self, x: float, y: float, z: float) -> None:
        self._emit(("goto", round(x, 4), round(y, 4), round(z, 4)))

    def set_gripper(self, open_: bool) -> float | None:
        self._emit(("gripper", "open" if open_ else "close"))
        return None

    def home(self) -> None:
        self._emit(("home",))

    def _emit(self, entry: tuple) -> None:
        self.log.append(entry)
        if self.verbose:
            print("   arm:", " ".join(str(p) for p in entry))


@dataclass
class LeRobotArm:
    """Drive a physical SO-ARM101 follower via LeRobot 0.5.x.

    goto() takes a robot-frame (x, y, z) in meters, solves IK to joint degrees,
    and slews there in small joint steps (one big point-to-point jump slams all
    six motors at full speed — jerky, and the current spike can brown out the
    motor bus mid-move). Transient "no status packet" bus glitches are retried.

    NOTE: gripper_open/closed and the home pose are setup-dependent — tune them
    on your arm. Keep movements slow and supervised (see README safety notes).
    """

    port: str
    urdf_path: str
    robot_id: str = "chessbot_follower"
    gripper_open: float = 60.0     # 0..100; tune after calibration
    gripper_closed: float = 10.0   # hard floor — the grip stops earlier on contact
    settle_s: float = 0.6
    max_step_deg: float = 14.0     # largest per-joint jump per slew step
    step_s: float = 0.15           # pause between slew steps
    # Adaptive grip: close in small steps and stop when the jaws meet the piece.
    grip_step: float = 4.0         # gripper units to close per step
    grip_settle_s: float = 0.12    # wait for the jaws to follow each step
    grip_stall: float = 3.5        # measured-vs-commanded lag that means "contact"
    grip_squeeze: float = 2.0      # extra close past contact, for a firm hold

    def __post_init__(self) -> None:
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig  # lazy
        from .kinematics import IKSolver
        self._robot = SO101Follower(
            SO101FollowerConfig(port=self.port, id=self.robot_id, use_degrees=True)
        )
        self._ik = IKSolver(self.urdf_path)
        self._arm_motors = IKSolver.ARM_JOINTS
        self._gripper = self.gripper_open

    def connect(self, attempts: int = 4) -> None:
        # The Feetech bus occasionally drops a motor's reply while energizing all
        # six on connect ("no status packet"). It's transient, so retry a few times
        # before giving up, disconnecting between tries to reset the bus.
        import time
        for attempt in range(1, attempts + 1):
            try:
                self._robot.connect()
                return
            except Exception as exc:
                if attempt == attempts:
                    raise
                print(f"  arm connect attempt {attempt} hit a bus glitch ({exc}); retrying...")
                try:
                    self._robot.disconnect()
                except Exception:
                    pass
                time.sleep(1.5)

    def disconnect(self) -> None:
        try:
            self._robot.disconnect()
        except Exception as exc:
            # Don't let a dead bus at cleanup time bury the real error.
            print(f"  couldn't reach the arm to disconnect cleanly ({exc}) — "
                  "power-cycle it before the next run.")

    def _bus(self, fn, attempts: int = 4, wait_s: float = 0.3):
        """Run a bus read/write, retrying transient Feetech dropouts. The same
        "no status packet" glitch that connect() retries also happens mid-session;
        a couple of retries ride it out. If it KEEPS failing the bus is really
        down — usually motor power (a sagging supply) or a loose cable."""
        import time
        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except ConnectionError as exc:
                if attempt == attempts:
                    print("  arm bus is not answering — check the motor power supply and "
                          "cable, power-cycle the arm, then re-run.")
                    raise
                print(f"  bus glitch ({exc}); retrying ({attempt}/{attempts - 1})...")
                time.sleep(wait_s)

    def _obs(self) -> dict:
        return self._bus(self._robot.get_observation)

    def _send(self, action: dict) -> None:
        self._bus(lambda: self._robot.send_action(action))

    def _current_q(self):
        import numpy as np
        obs = self._obs()
        return np.array([obs[f"{m}.pos"] for m in self._arm_motors], float)

    def goto(self, x: float, y: float, z: float) -> None:
        import time

        import numpy as np
        q_now = self._current_q()
        q = self._ik.joints_for((x, y, z), q_now)
        steps = max(1, int(np.ceil(np.max(np.abs(q - q_now)) / self.max_step_deg)))
        for i in range(1, steps + 1):
            qi = q_now + (q - q_now) * (i / steps)
            action = {f"{m}.pos": float(qi[j]) for j, m in enumerate(self._arm_motors)}
            action["gripper.pos"] = self._gripper
            self._send(action)
            time.sleep(self.step_s if i < steps else self.settle_s)

    def _gripper_pos(self) -> float:
        return float(self._obs()["gripper.pos"])

    def _wait_gripper_still(self, timeout_s: float = 2.5) -> float:
        """Poll until the jaws stop moving; returns where they settled."""
        import time
        last = self._gripper_pos()
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            time.sleep(self.grip_settle_s)
            now = self._gripper_pos()
            if abs(now - last) < 0.5:
                return now
            last = now
        return last

    def set_gripper(self, open_: bool) -> float | None:
        """Open fully, or close adaptively: step the jaws shut and stop when they
        jam against something — that's the piece. Works for any piece width
        (pawn to king) without per-piece tuning; a fixed close width would either
        crush a wide piece or eject it. Returns the width the jaws settled at
        (None on open).

        Contact = the measured width lags the commanded one AND the jaws have
        stopped moving, seen twice in a row. Either test alone false-triggers
        while the jaws are still accelerating or mid-travel."""
        import time
        obs = self._obs()  # hold the arm still, only move the gripper
        hold = {f"{m}.pos": obs[f"{m}.pos"] for m in self._arm_motors}
        if open_:
            self._gripper = self.gripper_open
            self._send({**hold, "gripper.pos": self._gripper})
            self._wait_gripper_still()
            return None
        target = actual = self._wait_gripper_still()  # close from where the jaws truly are
        stalled = 0
        while target > self.gripper_closed:
            target = max(self.gripper_closed, target - self.grip_step)
            self._send({**hold, "gripper.pos": target})
            time.sleep(self.grip_settle_s)
            prev, actual = actual, self._gripper_pos()
            if actual - target >= self.grip_stall and abs(actual - prev) < 1.0:
                stalled += 1
                if stalled >= 2:
                    self._gripper = max(self.gripper_closed, actual - self.grip_squeeze)
                    self._send({**hold, "gripper.pos": self._gripper})
                    time.sleep(self.settle_s)
                    print(f"  grip: contact at width {actual:.1f}, holding at {self._gripper:.1f}")
                    return self._gripper
            else:
                stalled = 0
        self._gripper = self.gripper_closed
        time.sleep(self.settle_s)
        print("  grip: jaws closed all the way — probably didn't catch a piece")
        return self._gripper

    def home(self) -> None:
        # A neutral, tucked pose. These joint angles are a starting guess — tune.
        self._send({
            "shoulder_pan.pos": 0.0, "shoulder_lift.pos": -90.0, "elbow_flex.pos": 90.0,
            "wrist_flex.pos": 0.0, "wrist_roll.pos": 0.0, "gripper.pos": self._gripper,
        })

    # --- calibration helpers ------------------------------------------------
    def relax(self) -> None:
        """Disable torque so the arm can be moved by hand (board calibration)."""
        self._robot.bus.disable_torque()

    def ee_xy(self) -> tuple[float, float]:
        """Current end-effector (x, y) in the robot frame, via forward kinematics."""
        x, y, _ = self._ik.forward_xyz(self._current_q())
        return float(x), float(y)
