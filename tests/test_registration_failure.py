"""Phase 2 SRS §7 item 4 / NFR-2.3: an unsolvable case (S2, <3 usable planes,
heavy occlusion) yields a structured RegistrationFailure, not a crash.
Constructs the sample directly via datagen.build_dataset.make_sample (same
pattern as tests/test_roundtrip.py) rather than depending on a specific
pre-generated grid file, so the scenario is reproducible and self-contained."""
import numpy as np

from datagen.build_dataset import make_sample
from datagen.io import read_cloud_ply, read_mesh_ply
from registration.api import register
from registration.params import load_params


def test_heavy_occlusion_s2_yields_structured_failure_not_crash(tmp_path):
    gt = make_sample(
        "S2",
        grid_point={"rot_deg": 2.0, "trans_mm": 50, "noise_sigma_mm": 3, "occlusion": "heavy"},
        seed=0,
        nominal_deviations={},
        tolerance_mm=10.0,
        density_per_m2=100,
        out_dir=tmp_path / "s2_heavy",
    )
    points, normals = read_cloud_ply(tmp_path / "s2_heavy" / "cloud.ply")
    mesh = read_mesh_ply(tmp_path / "s2_heavy" / "scene_mesh.ply")

    params = load_params("configs/registration_params.yaml")
    # Force the degenerate <3-plane-match condition deterministically for this
    # test only (heavy occlusion alone doesn't reliably guarantee it) — never
    # touches the frozen configs/registration_params.yaml.
    params = {
        **params,
        "T_gt": np.array(gt["T_gt"]),
        "plane_seg": {**params["plane_seg"], "min_support_points": 100000},
    }

    T_est, metrics = register((points, normals), mesh, "B", params)

    assert T_est is None
    assert metrics["status"] == "failed"
    assert metrics["failure"]["reason"] in {"insufficient_plane_matches", "unexpected_exception"}
