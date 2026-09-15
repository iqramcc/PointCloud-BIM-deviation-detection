"""Run-once calibration helper (Constitution Art. IV.2). NOT part of the test
suite or any reported result. Loads the held-out calibration sample (already
present in data/S1/ from the frozen grid — no new data generated), runs both
baselines with the current configs/registration_params.yaml, and prints the
resulting metrics so a human can eyeball fitness/RMSE and adjust the YAML by
hand between runs. Once satisfied, commit registration_params.yaml verbatim.

    python scripts/calibrate_registration_params.py --params configs/registration_params.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datagen.groundtruth import read_ground_truth  # noqa: E402
from datagen.io import read_cloud_ply, read_mesh_ply  # noqa: E402
from registration.api import register  # noqa: E402
from registration.params import load_params  # noqa: E402

CALIBRATION_SAMPLE_DIR = Path("data/S1/rot1.0_trans25_noise3_moderate/seed0")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", default="configs/registration_params.yaml")
    args = parser.parse_args()

    points, normals = read_cloud_ply(CALIBRATION_SAMPLE_DIR / "cloud.ply")
    mesh = read_mesh_ply(CALIBRATION_SAMPLE_DIR / "scene_mesh.ply")
    gt = read_ground_truth(CALIBRATION_SAMPLE_DIR / "ground_truth.json")
    T_gt = np.array(gt["T_gt"])
    params_base = load_params(args.params)

    for method in ("A", "B"):
        params = {**params_base, "T_gt": T_gt}
        _, metrics = register((points, normals), mesh, method, params)
        print(f"--- method {method} ---")
        print(json.dumps({k: v for k, v in metrics.items() if k != "T_est"}, indent=2))


if __name__ == "__main__":
    main()
