"""Shared fine-registration stage (FR-2.13-2.14) — the fairness mechanism.

Called from exactly one site in api.py::register(), after the coarse-method
branch, with the same `params["icp"]` object regardless of method — this IS
the fairness gate (NFR-2.1), not a convention about it.

FR-2.13 calls for a "configurable max-distance schedule": a single fixed
correspondence-distance threshold leaves a several-mm residual bias on this
project's synthetic clouds (empirically observed during calibration — see
specs/plan/phase-2-registration.md §6), so this runs point-to-plane ICP as a
sequence of progressively-tightening stages, chaining each stage's result into
the next, matching FR-2.13's language directly.
"""
from __future__ import annotations

import time

import numpy as np
import open3d as o3d

from .failures import ICPDivergenceError


def refine_icp(
    cloud_p: o3d.geometry.PointCloud,
    mesh_sample: o3d.geometry.PointCloud,
    T_coarse: np.ndarray,
    params: dict,
) -> tuple[np.ndarray, dict]:
    t0 = time.perf_counter()
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(
        relative_fitness=params["relative_fitness"],
        relative_rmse=params["relative_rmse"],
        max_iteration=params["max_iteration"],
    )
    estimation = o3d.pipelines.registration.TransformationEstimationPointToPlane()

    T_current = T_coarse
    result = None
    for max_corr_dist in params["max_correspondence_distance_schedule_m"]:
        result = o3d.pipelines.registration.registration_icp(
            cloud_p, mesh_sample, max_corr_dist, T_current, estimation, criteria
        )
        T_current = np.asarray(result.transformation)

    runtime_s = time.perf_counter() - t0
    if result.fitness < params["min_fitness"]:
        raise ICPDivergenceError(f"icp fitness={result.fitness:.4f} below {params['min_fitness']}")
    info = {"fitness": result.fitness, "inlier_rmse_mm": result.inlier_rmse * 1000.0, "runtime_s": runtime_s}
    return T_current, info
