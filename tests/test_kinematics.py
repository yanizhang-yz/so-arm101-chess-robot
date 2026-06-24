import math

import numpy as np
import pytest

from chessbot.kinematics import BoardToRobot


def test_identity_transform_passes_through():
    t = BoardToRobot()
    assert np.allclose(t.xy((0.1, 0.2)), [0.1, 0.2])


def test_fit_recovers_a_known_similarity():
    truth = BoardToRobot(scale=2.0, theta_rad=math.radians(30), offset=[0.1, -0.2])
    board_pts = [(0.0, 0.0), (0.04, 0.0), (0.0, 0.04), (0.28, 0.28)]
    robot_pts = [tuple(truth.xy(p)) for p in board_pts]

    fit = BoardToRobot.from_correspondences(board_pts, robot_pts)
    assert fit.scale == pytest.approx(2.0, abs=1e-6)
    assert fit.theta_rad == pytest.approx(math.radians(30), abs=1e-6)
    assert np.allclose(fit.offset, [0.1, -0.2], atol=1e-6)
    # And it reproduces the mapping on a held-out point.
    assert np.allclose(fit.xy((0.12, 0.16)), truth.xy((0.12, 0.16)), atol=1e-6)
