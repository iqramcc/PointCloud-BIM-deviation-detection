"""register() — the single entry point (FR-2.16-2.18) and the fairness architecture.

preprocess() is called exactly once, before the method branch; icp_params is
extracted once, also before the branch; refine_icp() is called from exactly one
site, after the branch, with that same object regardless of method. Neither
coarse_register_A nor coarse_register_B may call refine_icp themselves. This is
what makes NFR-2.1 (fairness) true by construction — see
tests/test_registration_fairness.py.
"""
from __future__ import annotations

import time

import numpy as np
import open3d as o3d

from .coarse_a import coarse_register_A
from .coarse_b import coarse_register_B
from .failures import RegistrationFailure, RegistrationStageError
from .icp import refine_icp
from .mesh_target import mesh_to_point_cloud
from .metrics import registration_error
from .planes import model_planes_from_mesh
from .preprocess import preprocess

SCHEMA_VERSION = 1


def _as_o3d_cloud(points: np.ndarray, normals: np.ndarray | None) -> o3d.geometry.PointCloud:
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    if normals is not None and len(normals) == len(points):
        pcd.normals = o3d.utility.Vector3dVector(normals)
    return pcd


def _failed_metrics(method: str, runtime_total_s: float, failure: RegistrationFailure) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "method": method,
        "status": "failed",
        "T_est": None,
        "coarse": None,
        "icp": None,
        "error_vs_gt": None,
        "failure": failure.as_dict(),
        "runtime_total_s": runtime_total_s,
    }


def register(cloud, mesh, method: str, params: dict) -> tuple[np.ndarray | None, dict]:
    """cloud: o3d.geometry.PointCloud or (points, normals) tuple.
    mesh: trimesh.Trimesh (the as-designed geometry).
    method: one of {"A", "B", "B_seeded"}.
    params: the frozen parameter dict, optionally carrying a per-call "T_gt"
        (4x4 array) and "seed" (int) — see specs/plan/phase-2-registration.md §2.3.
    """
    t0 = time.perf_counter()
    if not isinstance(cloud, o3d.geometry.PointCloud):
        points, normals = cloud
        cloud = _as_o3d_cloud(points, normals)

    seed = int(params.get("seed", 0))
    rng = np.random.default_rng(seed)

    try:
        cloud_p = preprocess(cloud, params["preprocess"])  # ONE call, before the branch (FR-2.4)
        mesh_sample = mesh_to_point_cloud(mesh, params["mesh_sample"], rng)  # shared target
        icp_params = params["icp"]  # extracted ONCE; same object either branch

        if method == "A":
            T_coarse, coarse_info = coarse_register_A(cloud_p, mesh_sample, {**params, "seed": seed})
        elif method in ("B", "B_seeded"):
            model_planes = model_planes_from_mesh(mesh, params["model_planes"])
            seeds = params.get("b_seeded_correspondences") if method == "B_seeded" else None
            T_coarse, coarse_info = coarse_register_B(cloud_p, model_planes, {**params, "seed": seed}, seeds=seeds)
        else:
            raise ValueError(f"unknown method {method!r}")

        T_est, icp_info = refine_icp(cloud_p, mesh_sample, T_coarse, icp_params)  # SAME call site for A and B
    except RegistrationStageError as exc:
        failure = RegistrationFailure(stage=exc.stage, reason=exc.reason, detail=str(exc))
        return None, _failed_metrics(method, time.perf_counter() - t0, failure)
    except Exception as exc:  # NFR-2.3: never abort a grid run
        failure = RegistrationFailure(stage="unknown", reason="unexpected_exception", detail=str(exc))
        return None, _failed_metrics(method, time.perf_counter() - t0, failure)

    error_vs_gt = None
    if params.get("T_gt") is not None:  # only place T_gt is consumed (NFR-2.4)
        error_vs_gt = registration_error(T_est, np.asarray(params["T_gt"]), np.asarray(mesh_sample.points))

    runtime_total_s = time.perf_counter() - t0
    metrics = {
        "schema_version": SCHEMA_VERSION,
        "method": method,
        "status": "ok",
        "T_est": T_est.tolist(),
        "coarse": coarse_info,
        "icp": icp_info,
        "error_vs_gt": error_vs_gt,
        "runtime_total_s": runtime_total_s,
    }
    return T_est, metrics
