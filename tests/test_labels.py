from datagen.build_dataset import make_sample


def test_deviated_element_flagged_others_not(tmp_path):
    """Phase 1 SRS §7.4: element k offset by 14mm at tau=10mm -> flagged;
    undisturbed elements -> not flagged."""
    grid_point = {"rot_deg": 0.0, "trans_mm": 0.0, "noise_sigma_mm": 0.0, "occlusion": "none"}
    gt = make_sample(
        "S1", grid_point, seed=0,
        nominal_deviations={3: {"type": "normal_offset", "value_mm": 14.0}},
        tolerance_mm=10.0, density_per_m2=200, out_dir=tmp_path / "s",
    )
    flagged = {e["id"] for e in gt["elements"] if e["is_out_of_tolerance"]}
    assert flagged == {3}


def test_sub_tolerance_offset_not_flagged(tmp_path):
    grid_point = {"rot_deg": 0.0, "trans_mm": 0.0, "noise_sigma_mm": 0.0, "occlusion": "none"}
    gt = make_sample(
        "S1", grid_point, seed=0,
        nominal_deviations={3: {"type": "normal_offset", "value_mm": 6.0}},
        tolerance_mm=10.0, density_per_m2=200, out_dir=tmp_path / "s",
    )
    flagged = {e["id"] for e in gt["elements"] if e["is_out_of_tolerance"]}
    assert flagged == set()


def test_no_deviation_none_flagged(tmp_path):
    grid_point = {"rot_deg": 0.0, "trans_mm": 0.0, "noise_sigma_mm": 0.0, "occlusion": "none"}
    gt = make_sample(
        "S1", grid_point, seed=0, nominal_deviations={},
        tolerance_mm=10.0, density_per_m2=200, out_dir=tmp_path / "s",
    )
    assert all(not e["is_out_of_tolerance"] for e in gt["elements"])
