"""Dataset builder CLI (FR-1.10, FR-1.12).

    python -m datagen.build_dataset --config configs/grid.yaml --out data/
    python -m datagen.build_dataset --config configs/grid.yaml --out data/ --clean
"""
from __future__ import annotations

import argparse
import csv
import itertools
from pathlib import Path

import numpy as np
import yaml

from .elements import Element
from .groundtruth import build_ground_truth, write_ground_truth
from .io import write_cloud_ply, write_mesh_ply
from .perturb import add_noise, apply_nominal_deviations, apply_occlusion, sample_registration_transform
from .sampling import sample_cloud
from .scene import build_mesh, generate_scene, load_scene_config, scanner_origins

SCENES_DIR = Path(__file__).resolve().parents[2] / "configs" / "scenes"


def make_sample(
    scene_id: str,
    grid_point: dict,
    seed: int,
    nominal_deviations: dict[int, dict],
    tolerance_mm: float,
    density_per_m2: float,
    out_dir: str | Path,
) -> dict:
    """Generate one fully labelled sample. Deterministic given (scene, grid_point,
    seed, nominal_deviations) — FR-1.9."""
    rng = np.random.default_rng(seed)
    scene_yaml = SCENES_DIR / f"{scene_id}.yaml"
    cfg = load_scene_config(scene_yaml)

    mesh_design, elements_design, _ = generate_scene(cfg)

    deviated_elements, applied = apply_nominal_deviations(elements_design, nominal_deviations)
    mesh_built, face_element_ids = build_mesh(deviated_elements)

    points, normals, element_ids = sample_cloud(mesh_built, face_element_ids, density_per_m2, rng)

    outlier_rate = grid_point.get("outlier_rate", 0.0)
    points = add_noise(points, normals, grid_point["noise_sigma_mm"], rng, outlier_rate=outlier_rate)

    origins = scanner_origins(cfg)
    points, normals, element_ids = apply_occlusion(points, normals, element_ids, origins, grid_point["occlusion"])

    T_gt = sample_registration_transform(grid_point["rot_deg"], grid_point["trans_mm"], rng)
    points_h = np.hstack([points, np.ones((len(points), 1))])
    points = (T_gt @ points_h.T).T[:, :3]
    normals = (T_gt[:3, :3] @ normals.T).T

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_cloud_ply(out / "cloud.ply", points, normals)
    write_mesh_ply(out / "scene_mesh.ply", mesh_design)

    gt = build_ground_truth(
        scene_id=scene_id,
        seed=seed,
        grid_point=grid_point,
        T_gt=T_gt,
        sensor={
            "origins_m": origins.tolist(),
            "noise_sigma_mm": grid_point["noise_sigma_mm"],
            "outlier_rate": outlier_rate,
        },
        point_density_per_m2=density_per_m2,
        elements=deviated_elements,
        nominal_deviations=applied,
        tolerance_mm=tolerance_mm,
    )
    write_ground_truth(gt, out / "ground_truth.json")
    return gt


def _grid_points(grid_cfg: dict, use_fallback: bool = False) -> list[dict]:
    noise_axis = grid_cfg["fallback"]["noise_sigma_mm"] if use_fallback else grid_cfg["noise_sigma_mm"]
    occlusion_axis = grid_cfg["fallback"]["occlusion"] if use_fallback else grid_cfg["occlusion"]
    combos = itertools.product(grid_cfg["rot_deg"], grid_cfg["trans_mm"], noise_axis, occlusion_axis)
    return [
        {"rot_deg": rot, "trans_mm": trans, "noise_sigma_mm": noise, "occlusion": occ}
        for rot, trans, noise, occ in combos
    ]


def build_dataset(config_path: str | Path, out_dir: str | Path, clean: bool = False, fallback: bool = False) -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        grid_cfg = yaml.safe_load(f)

    seeds_path = Path(config_path).parent / "seeds.yaml"
    with open(seeds_path, "r", encoding="utf-8") as f:
        seeds = yaml.safe_load(f)["seeds"]

    for scene_id in grid_cfg["scenes"]:
        scene_out = Path(out_dir) / scene_id
        deviations = {int(k): v for k, v in grid_cfg["nominal_deviations"].get(scene_id, {}).items()}
        rows = []

        if clean:
            points_list = [{"rot_deg": 0.0, "trans_mm": 0.0, "noise_sigma_mm": 0.0, "occlusion": "none"}]
            sample_seeds = [seeds[0]]
            sample_deviations: dict[int, dict] = {}
        else:
            points_list = _grid_points(grid_cfg, use_fallback=fallback)
            sample_seeds = seeds
            sample_deviations = deviations

        for grid_point in points_list:
            for seed in sample_seeds:
                sample_id = (
                    f"rot{grid_point['rot_deg']}_trans{grid_point['trans_mm']}"
                    f"_noise{grid_point['noise_sigma_mm']}_{grid_point['occlusion']}/seed{seed}"
                )
                sample_dir = scene_out / sample_id
                make_sample(
                    scene_id=scene_id,
                    grid_point=grid_point,
                    seed=seed,
                    nominal_deviations=sample_deviations,
                    tolerance_mm=grid_cfg["tolerance_mm"],
                    density_per_m2=grid_cfg["point_density_per_m2"],
                    out_dir=sample_dir,
                )
                rows.append(
                    {
                        "scene_id": scene_id,
                        "sample_id": sample_id,
                        "seed": seed,
                        "rot_deg": grid_point["rot_deg"],
                        "trans_mm": grid_point["trans_mm"],
                        "noise_sigma_mm": grid_point["noise_sigma_mm"],
                        "occlusion": grid_point["occlusion"],
                        "cloud_path": str(sample_dir / "cloud.ply"),
                        "mesh_path": str(sample_dir / "scene_mesh.ply"),
                        "ground_truth_path": str(sample_dir / "ground_truth.json"),
                    }
                )

        manifest_path = scene_out / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the synthetic BIM/point-cloud dataset.")
    parser.add_argument("--config", required=True, help="path to grid.yaml")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--clean", action="store_true", help="FR-1.12 sanity mode: one no-perturbation sample/scene")
    parser.add_argument("--fallback", action="store_true", help="use the reduced grid (risk R2)")
    args = parser.parse_args()
    build_dataset(args.config, args.out, clean=args.clean, fallback=args.fallback)


if __name__ == "__main__":
    main()
