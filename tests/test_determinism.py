import hashlib

from datagen.build_dataset import make_sample


def _file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_same_seed_produces_identical_files(tmp_path):
    """FR-1.9: deterministic given (scene, config, seed)."""
    grid_point = {"rot_deg": 1.0, "trans_mm": 25, "noise_sigma_mm": 3, "occlusion": "moderate"}
    deviations = {3: {"type": "normal_offset", "value_mm": 14.0}}

    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    make_sample("S1", grid_point, seed=7, nominal_deviations=deviations,
                tolerance_mm=10.0, density_per_m2=200, out_dir=out_a)
    make_sample("S1", grid_point, seed=7, nominal_deviations=deviations,
                tolerance_mm=10.0, density_per_m2=200, out_dir=out_b)

    assert _file_hash(out_a / "cloud.ply") == _file_hash(out_b / "cloud.ply")
    assert _file_hash(out_a / "scene_mesh.ply") == _file_hash(out_b / "scene_mesh.ply")

    # ground_truth.json is not required to be byte-identical if it ever gains a
    # timestamp, but today it is pure function of the inputs, so check content.
    gt_a = (out_a / "ground_truth.json").read_text(encoding="utf-8")
    gt_b = (out_b / "ground_truth.json").read_text(encoding="utf-8")
    assert gt_a == gt_b


def test_different_seed_produces_different_cloud(tmp_path):
    grid_point = {"rot_deg": 1.0, "trans_mm": 25, "noise_sigma_mm": 3, "occlusion": "none"}
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    make_sample("S1", grid_point, seed=1, nominal_deviations={},
                tolerance_mm=10.0, density_per_m2=200, out_dir=out_a)
    make_sample("S1", grid_point, seed=2, nominal_deviations={},
                tolerance_mm=10.0, density_per_m2=200, out_dir=out_b)
    assert _file_hash(out_a / "cloud.ply") != _file_hash(out_b / "cloud.ply")
