import numpy as np
import pytest

import chessbot.arm as arm_module
from chessbot.arm import MockArm
from chessbot.config import Settings
from chessbot.kinematics import BoardToRobot
from chessbot.runtime import build_arm


def _hardware_settings(transform: BoardToRobot) -> Settings:
    settings = Settings(transform=transform)
    settings.arm.follower_port = "PORT"
    settings.arm.urdf_path = "robot.urdf"
    return settings


def test_hardware_rejects_the_default_transform_before_lazy_backend_import(monkeypatch):
    settings = _hardware_settings(BoardToRobot())
    monkeypatch.delattr(arm_module, "LeRobotArm")

    with pytest.raises(ValueError, match="board transform"):
        build_arm(settings, hardware=True)


@pytest.mark.parametrize(
    "transform",
    [
        BoardToRobot(scale=0.0, offset=[0.3, 0.1]),
        BoardToRobot(scale=-0.9, offset=[0.3, 0.1]),
        BoardToRobot(scale=0.9, theta_rad=np.inf, offset=[0.3, 0.1]),
        BoardToRobot(scale=0.9, offset=[np.nan, 0.1]),
    ],
)
def test_hardware_rejects_invalid_transform_before_lazy_backend_import(
    monkeypatch, transform
):
    settings = _hardware_settings(transform)
    monkeypatch.delattr(arm_module, "LeRobotArm")

    with pytest.raises(ValueError, match="board transform"):
        build_arm(settings, hardware=True)


def test_hardware_accepts_a_seeded_finite_transform(monkeypatch):
    class FakeLeRobotArm:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(arm_module, "LeRobotArm", FakeLeRobotArm)
    settings = _hardware_settings(
        BoardToRobot(scale=0.92, theta_rad=-1.5, offset=[0.3, 0.1], flip=-1)
    )

    arm = build_arm(settings, hardware=True)

    assert arm.kwargs == {
        "port": "PORT",
        "urdf_path": "robot.urdf",
        "robot_id": "chessbot_follower",
        "gripper_open": 60.0,
        "gripper_closed": 10.0,
    }


def test_mock_arm_does_not_require_a_seeded_transform():
    assert isinstance(build_arm(Settings(), hardware=False), MockArm)
