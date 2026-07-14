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


def test_fit_handles_a_mirrored_board():
    # A mirrored board (left/right flip) must still fit — the scale must NOT collapse.
    truth = BoardToRobot(scale=0.9, theta_rad=0.7, offset=[0.3, 0.1], flip=-1)
    board_pts = [(0.0, 0.0), (0.28, 0.0), (0.0, 0.28), (0.28, 0.28)]
    robot_pts = [tuple(truth.xy(p)) for p in board_pts]

    fit = BoardToRobot.from_correspondences(board_pts, robot_pts)
    assert fit.flip == -1
    assert fit.scale == pytest.approx(0.9, abs=1e-6)
    for p in board_pts:
        assert np.allclose(fit.xy(p), truth.xy(p), atol=1e-6)


# The 9 squares the driven calibration touches, as board coordinates.
NINE = [(x * 0.04, y * 0.04) for x, y in
        [(0, 0), (3, 0), (7, 0), (7, 3), (7, 7), (4, 7), (0, 7), (0, 3), (3, 3)]]


def _bulge(p):
    # A smooth distortion like an arm's model error: grows quadratically outward.
    x, y = p
    return np.array([0.02 * x * x + 0.01 * x * y, -0.015 * y * y + 0.01 * x])


def test_warp_absorbs_smooth_distortion():
    truth = BoardToRobot(scale=0.92, theta_rad=-1.54, offset=[0.34, 0.14], flip=-1)
    robot_pts = [tuple(truth.xy(p) + _bulge(p)) for p in NINE]

    plain = BoardToRobot.from_correspondences(NINE, robot_pts)
    warped = BoardToRobot.with_warp(NINE, robot_pts)

    held_out = (0.08, 0.20)  # a square the fit never saw
    target = truth.xy(held_out) + _bulge(held_out)
    plain_err = np.linalg.norm(plain.xy(held_out) - target)
    warp_err = np.linalg.norm(warped.xy(held_out) - target)
    assert warp_err < 0.002          # the warp nails a quadratic field
    assert warp_err < plain_err / 2  # and clearly beats the rigid fit


def test_warp_needs_enough_points():
    truth = BoardToRobot(scale=1.0, offset=[0.3, 0.0])
    pts = NINE[:6]
    fit = BoardToRobot.with_warp(pts, [tuple(truth.xy(p)) for p in pts])
    assert fit.warp_x is None  # too few points: falls back to the rigid fit


def test_warp_is_clamped_outside_the_board():
    truth = BoardToRobot(scale=0.92, theta_rad=-1.54, offset=[0.34, 0.14], flip=-1)
    warped = BoardToRobot.with_warp(NINE, [tuple(truth.xy(p) + _bulge(p)) for p in NINE])
    bare = BoardToRobot(scale=warped.scale, theta_rad=warped.theta_rad,
                        offset=warped.offset.copy(), flip=warped.flip)

    def warp_term(p):
        return warped.xy(p) - bare.xy(p)

    # Off-board graveyard slots sit outside the calibrated box; the quadratic
    # correction must be held at the box edge there, not extrapolated. (-0.13, 0)
    # clamps to the (0, 0) corner of the box.
    assert np.allclose(warp_term((-0.13, 0.0)), warp_term((0.0, 0.0)), atol=1e-12)
    assert np.linalg.norm(warp_term((-0.13, 0.0))) < 0.02  # stays a small correction


def test_warp_survives_the_yaml_round_trip():
    from chessbot.config import Settings, _overlay
    warped = BoardToRobot.with_warp(
        NINE, [tuple(BoardToRobot(offset=[0.3, 0.1]).xy(p) + _bulge(p)) for p in NINE])
    s = Settings()
    _overlay(s, {"transform": {
        "scale": warped.scale, "theta_rad": warped.theta_rad, "flip": warped.flip,
        "offset": [float(v) for v in warped.offset],
        "warp_x": [float(v) for v in warped.warp_x],
        "warp_y": [float(v) for v in warped.warp_y],
        "warp_box": [float(v) for v in warped.warp_box],
    }})
    for p in [(0.0, 0.0), (0.12, 0.2), (-0.05, 0.0)]:
        assert np.allclose(s.transform.xy(p), warped.xy(p), atol=1e-9)
