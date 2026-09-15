import numpy as np
import trimesh

from datagen.build_dataset import make_sample
from datagen.io import read_cloud_ply, read_mesh_ply


def test_clean_sample_roundtrip_rms_within_half_mm(tmp_path):
    """Phase 1 SRS §7.3: clean sample (no perturbation/noise/occlusion/deviation),
    apply inverse(T_gt) to cloud.ply, point-to-mesh distance RMS <= 0.5 mm."""
    grid_point = {"rot_deg": 0.0, "trans_mm": 0.0, "noise_sigma_mm": 0.0, "occlusion": "none"}
    out_dir = tmp_path / "clean"
    gt = make_sample(
        "S1", grid_point, seed=0, nominal_deviations={},
        tolerance_mm=10.0, density_per_m2=500, out_dir=out_dir,
    )

    points, _ = read_cloud_ply(out_dir / "cloud.ply")
    mesh = read_mesh_ply(out_dir / "scene_mesh.ply")

    T_gt = np.array(gt["T_gt"])
    T_inv = np.linalg.inv(T_gt)
    points_h = np.hstack([points, np.ones((len(points), 1))])
    aligned = (T_inv @ points_h.T).T[:, :3]

    _, distances, _ = trimesh.proximity.closest_point(mesh, aligned)
    rms_mm = float(np.sqrt(np.mean(distances**2)) * 1000.0)
    assert rms_mm <= 0.5, f"round-trip RMS {rms_mm:.4f} mm exceeds 0.5 mm"
