"""Baseline A — point-based coarse registration (FR-2.5-2.7).

FPFH features + seeded RANSAC global registration. Reference: Rusu et al. 2009;
Open3D global-registration tutorial.
"""
from __future__ import annotations

import time

import numpy as np
import open3d as o3d

from .failures import RansacNoConsensusError


def coarse_register_A(
    cloud_p: o3d.geometry.PointCloud,
    mesh_sample: o3d.geometry.PointCloud,
    params: dict,
) -> tuple[np.ndarray, dict]:
    t0 = time.perf_counter()
    radius = params["fpfh"]["radius_m"]
    max_nn = params["fpfh"]["max_nn"]
    fpfh_source = o3d.pipelines.registration.compute_fpfh_feature(
        cloud_p, o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=max_nn)
    )
    fpfh_target = o3d.pipelines.registration.compute_fpfh_feature(
        mesh_sample, o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=max_nn)
    )

    # Open3D's RANSAC has no RNG-object parameter; the only seed hook is this
    # process-global call, made explicitly from the caller-supplied seed right
    # before use — a narrow, documented deviation from Constitution Art. I.3's
    # "no hidden global RNG state" (see specs/plan/phase-2-registration.md §4).
    o3d.utility.random.seed(int(params["seed"]))

    ra = params["ransac_a"]
    criteria = o3d.pipelines.registration.RANSACConvergenceCriteria(
        max_iteration=ra["max_iteration"], confidence=ra["confidence"]
    )
    # Correspondence-pruning checkers from the Open3D global-registration tutorial /
    # Rusu et al. 2009. Calibrated empirically (scripts/calibrate_registration_params.py)
    # against this project's scenes: an edge-length checker alone is a large net win
    # (rejects geometrically-inconsistent correspondence triplets before the expensive
    # transform fit); a distance checker on top of it rejected every candidate within
    # budget on these flat, locally self-similar planar scenes, so it is left out.
    checkers = [o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(ra["edge_length_similarity"])]
    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        cloud_p,
        mesh_sample,
        fpfh_source,
        fpfh_target,
        mutual_filter=ra["mutual_filter"],
        max_correspondence_distance=ra["distance_threshold_m"],
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        ransac_n=ra["ransac_n"],
        checkers=checkers,
        criteria=criteria,
    )
    runtime_s = time.perf_counter() - t0
    if result.fitness < ra["min_fitness"] or len(result.correspondence_set) < 3:
        raise RansacNoConsensusError(
            f"fitness={result.fitness:.4f}, correspondences={len(result.correspondence_set)}"
        )
    info = {"fitness": result.fitness, "inlier_rmse_mm": result.inlier_rmse * 1000.0, "runtime_s": runtime_s}
    return np.asarray(result.transformation), info
