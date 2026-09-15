"""Unit-checks registration_error's math against hand-computed cases, independent
of any registration pipeline (specs/plan/phase-2-registration.md §11 item 7)."""
import numpy as np

from registration.metrics import registration_error


def test_identity_transforms_give_zero_error():
    T = np.eye(4)
    err = registration_error(T, T)
    assert abs(err["rot_deg"]) < 1e-6
    assert abs(err["trans_mm"]) < 1e-6
    assert abs(err["rmse_mm"]) < 1e-6


def test_90_degree_rotation_about_z_reports_90_deg_error():
    T_est = np.eye(4)
    theta = np.pi / 2
    T_gt = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0, 0],
            [np.sin(theta), np.cos(theta), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )
    # registration_error compares T_est against inverse(T_gt); T_gt here is its own
    # inverse's inverse trick avoided by using T_gt = pure rotation (inverse is -theta).
    err = registration_error(T_est, np.linalg.inv(T_gt))
    assert abs(err["rot_deg"] - 90.0) < 1e-3


def test_pure_translation_reports_only_translation_error():
    T_est = np.eye(4)
    T_gt = np.eye(4)
    T_gt[:3, 3] = [-0.01, -0.02, -0.03]  # inverse(T_gt) has translation [0.01,0.02,0.03]
    err = registration_error(T_est, T_gt)
    assert err["rot_deg"] < 1e-6
    expected_mm = np.linalg.norm([10.0, 20.0, 30.0])
    assert abs(err["trans_mm"] - expected_mm) < 1e-6
