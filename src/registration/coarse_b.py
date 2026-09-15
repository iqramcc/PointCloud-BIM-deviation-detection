"""Baseline B — plane-based coarse registration (FR-2.8-2.12).

Segments planes from the cloud and the as-designed mesh, matches them, and
solves a closed-form rigid transform. `seeds` (FR-2.12/R1 fallback) bypasses
automatic matching only — the same closed-form solver is used either way.
"""
from __future__ import annotations

import time

import numpy as np
import open3d as o3d

from .planes import PlaneMatch, extract_cloud_planes, match_planes, solve_rigid_from_planes


def coarse_register_B(
    cloud_p: o3d.geometry.PointCloud,
    model_planes: list,
    params: dict,
    seeds: list[dict] | None = None,
) -> tuple[np.ndarray, dict]:
    t0 = time.perf_counter()
    cloud_planes = extract_cloud_planes(cloud_p, params)

    if seeds is not None:
        by_cid = {p.id: p for p in cloud_planes}
        by_mid = {p.id: p for p in model_planes}
        matches = [
            PlaneMatch(
                cloud_plane=by_cid[s["cloud_plane_id"]],
                model_plane=by_mid[s["model_plane_id"]],
                normal_angle_deg=0.0,
                centroid_dist_m=0.0,
            )
            for s in seeds
        ]
    else:
        matches = match_planes(cloud_planes, model_planes, params)

    T_coarse = solve_rigid_from_planes(matches, params)
    runtime_s = time.perf_counter() - t0
    info = {"fitness": None, "inlier_rmse_mm": None, "runtime_s": runtime_s, "n_plane_matches": len(matches)}
    return T_coarse, info
