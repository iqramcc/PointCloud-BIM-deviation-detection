"""Phase 2 SRS §7 item 2: recovery across the registration-error axis on
clean-enough data.

Documented interpretation (agreed with the project owner, not a change to the
frozen configs/grid.yaml): the frozen grid's noise axis is {1, 3, 5} mm with no
literal 0 level. We use noise_sigma_mm=1, occlusion=none as the "clean enough"
set — 1 mm is negligible against this test's tolerance (5.0 mm trans / 0.2 deg
rot) and against the >=10mm registration-error grid points. This affects test
sample selection only; configs/grid.yaml is untouched.
"""
from pathlib import Path

import numpy as np
import pytest

from datagen.groundtruth import read_ground_truth
from datagen.io import read_cloud_ply, read_mesh_ply
from registration.api import register
from registration.params import load_params

# 5x5 rot/trans grid x seeds {0,1} = 50 samples/method, well over the >=20 minimum.
SAMPLE_DIRS = sorted(Path("data/S1").glob("rot*_trans*_noise1_none/seed[01]"))


def _errors_for(method: str) -> tuple[list[float], list[float]]:
    params_base = load_params("configs/registration_params.yaml")
    rot_errs, trans_errs = [], []
    for d in SAMPLE_DIRS:
        points, normals = read_cloud_ply(d / "cloud.ply")
        mesh = read_mesh_ply(d / "scene_mesh.ply")
        gt = read_ground_truth(d / "ground_truth.json")
        params = {**params_base, "T_gt": np.array(gt["T_gt"])}
        T_est, metrics = register((points, normals), mesh, method, params)
        if metrics["status"] != "ok":
            continue
        rot_errs.append(metrics["error_vs_gt"]["rot_deg"])
        trans_errs.append(metrics["error_vs_gt"]["trans_mm"])
    return rot_errs, trans_errs


@pytest.mark.slow
def test_baseline_a_median_error_within_bounds_on_clean_registration_axis():
    assert len(SAMPLE_DIRS) >= 20
    rot_errs, trans_errs = _errors_for("A")
    assert len(rot_errs) >= 20, f"only {len(rot_errs)} of {len(SAMPLE_DIRS)} samples succeeded"
    assert np.median(rot_errs) < 0.2
    assert np.median(trans_errs) < 5.0


@pytest.mark.slow
def test_baseline_b_median_error_within_bounds_on_clean_registration_axis():
    assert len(SAMPLE_DIRS) >= 20
    rot_errs, trans_errs = _errors_for("B")
    assert len(rot_errs) >= 20, f"only {len(rot_errs)} of {len(SAMPLE_DIRS)} samples succeeded"
    assert np.median(rot_errs) < 0.2
    assert np.median(trans_errs) < 5.0
