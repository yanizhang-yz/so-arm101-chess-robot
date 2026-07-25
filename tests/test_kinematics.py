import math

import numpy as np
import pytest

from chessbot.kinematics import BoardToRobot, IKSolver


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


def _mislabeled_seed(truth, sym_name):
    """A transform whose labeling is `sym_name` away from the truth — i.e. it
    sends square s to where the TRUE sym(s) is (a wrongly-oriented calibration)."""
    from chessbot.board import BoardGeometry
    from chessbot.kinematics import BOARD_SYMMETRIES, _sq_idx, _sq_name
    geo = BoardGeometry()
    sym = BOARD_SYMMETRIES[sym_name]
    ref = ["a1", "h1", "a8", "h8", "d4", "e6"]
    board = [geo.square_center(s) for s in ref]
    robot = [tuple(truth.xy(geo.square_center(_sq_name(*sym(*_sq_idx(s)))))) for s in ref]
    return BoardToRobot.from_correspondences(board, robot), geo


def test_reorient_fixes_the_h4_over_d8_case():
    # h4 -> d8 is the diagonal mirror ("transpose"): the exact case seen live.
    from chessbot.kinematics import reorient_transform
    truth = BoardToRobot(scale=0.92, theta_rad=-1.54, offset=[0.34, 0.14], flip=-1)
    seed, geo = _mislabeled_seed(truth, "transpose")
    # sanity: driving the seed's h4 really does land on the true d8
    assert np.allclose(seed.xy(geo.square_center("h4")), truth.xy(geo.square_center("d8")), atol=1e-9)
    fixed = reorient_transform(seed, "h4", "d8", geo)
    for s in ["a1", "h4", "e2", "h8", "b7"]:
        assert np.allclose(fixed.xy(geo.square_center(s)), truth.xy(geo.square_center(s)), atol=1e-9)


def test_reorient_handles_rotations_too():
    # rot90 is NOT its own inverse — this catches a backwards composition.
    from chessbot.kinematics import reorient_transform
    truth = BoardToRobot(scale=1.1, theta_rad=0.4, offset=[0.2, -0.1])
    seed, geo = _mislabeled_seed(truth, "rot90")
    fixed = reorient_transform(seed, "h4", "d1", geo)  # rot90(h4) = d1
    for s in ["a1", "g5", "h8"]:
        assert np.allclose(fixed.xy(geo.square_center(s)), truth.xy(geo.square_center(s)), atol=1e-9)


def test_reorient_rejects_an_impossible_square():
    from chessbot.kinematics import orientation_candidates, reorient_transform
    truth = BoardToRobot(offset=[0.3, 0.0])
    seed, geo = _mislabeled_seed(truth, "as-is")
    assert reorient_transform(seed, "h4", "b3", geo) is None  # no orientation does h4->b3
    assert set(orientation_candidates("h4")) == {"h4", "d1", "a5", "e8", "a4", "h5", "d8", "e1"}


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


class _FixedIKChain:
    def __init__(self, candidate_deg, end_xyz):
        self.links = [object() for _ in candidate_deg]
        self._candidate = np.deg2rad(np.asarray(candidate_deg, float))
        self._end_xyz = np.asarray(end_xyz, float)

    def inverse_kinematics(self, **_kwargs):
        return self._candidate.copy()

    def forward_kinematics(self, _full):
        transform = np.eye(4)
        transform[:3, 3] = self._end_xyz
        return transform


def _fixed_solver(candidate_deg, end_xyz):
    solver = object.__new__(IKSolver)
    solver.chain = _FixedIKChain(candidate_deg, end_xyz)
    solver._active = list(range(len(candidate_deg)))
    solver._true_lo = {}
    solver._true_hi = {}
    solver._lower = np.full(len(candidate_deg), -np.inf)
    solver._upper = np.full(len(candidate_deg), np.inf)
    solver._approaches = lambda _target: [np.array([0.0, 0.0, -1.0])]
    return solver


def test_ik_rejects_the_best_candidate_when_it_misses_tolerance():
    solver = _fixed_solver(
        candidate_deg=[10.0, 20.0, 30.0, 40.0, 50.0],
        end_xyz=[0.1, -0.2, 0.4],
    )

    with pytest.raises(RuntimeError) as caught:
        solver.joints_for(
            xyz=[0.1, -0.2, 0.3],
            current_q_deg=[0.0, 0.0, 0.0, 0.0, 0.0],
            tol_mm=3.0,
        )

    error = caught.value
    assert type(error).__name__ == "UnreachableTargetError"
    assert error.target_xyz == pytest.approx((0.1, -0.2, 0.3))
    assert error.best_error_mm == pytest.approx(100.0)
    assert error.tolerance_mm == pytest.approx(3.0)


def test_ik_returns_a_candidate_that_meets_tolerance():
    solver = _fixed_solver(
        candidate_deg=[10.0, 20.0, 30.0, 40.0, 50.0],
        end_xyz=[0.1, -0.2, 0.302],
    )

    result = solver.joints_for(
        xyz=[0.1, -0.2, 0.3],
        current_q_deg=[0.0, 0.0, 0.0, 0.0, 0.0],
        tol_mm=3.0,
    )

    assert result == pytest.approx([10.0, 20.0, 30.0, 40.0, 50.0])
