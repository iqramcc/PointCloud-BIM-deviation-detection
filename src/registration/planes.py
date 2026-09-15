"""Baseline B's custom component (FR-2.8-2.11): plane extraction, model-plane
recovery, correspondence matching, and the closed-form rigid solve.

Two interface-convention decisions (see specs/plan/phase-2-registration.md §2):
- Model planes come from clustering mesh faces by (normal, offset), not from
  ground_truth.json (no centroids) or scene_mesh.ply (no face->element-id after
  export) — generic to any mesh, keeps this module independent of `datagen`.
- Matching assumes the grid's injected error is a *residual* (<=4 deg / <=100mm
  on a 5-12m scene), so cloud/model centroids are already close under an
  identity-ish alignment — nearest-centroid-under-normal-similarity is a sound
  stand-in for FR-2.10's "adjacency" language (documented interpretation, not a
  literal adjacency graph).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import open3d as o3d
import trimesh
from scipy.optimize import linear_sum_assignment

from .failures import InsufficientPlaneMatchesError


@dataclass(frozen=True)
class Plane:
    id: int
    normal: np.ndarray  # (3,) unit
    point: np.ndarray  # (3,) a point on the plane (centroid of support)
    area: float | None  # m^2; known for model planes, None for raw cloud planes
    support: int  # inlier point count (cloud) or face count (model)


@dataclass(frozen=True)
class PlaneMatch:
    cloud_plane: Plane
    model_plane: Plane
    normal_angle_deg: float
    centroid_dist_m: float


def extract_cloud_planes(cloud_p: o3d.geometry.PointCloud, params: dict) -> list[Plane]:
    """Iterative single-plane RANSAC + inlier removal — Open3D has no multi-plane API."""
    seg = params["plane_seg"]
    o3d.utility.random.seed(int(params["seed"]))

    remaining = o3d.geometry.PointCloud(cloud_p)
    planes: list[Plane] = []
    while len(remaining.points) >= seg["min_support_points"] and len(planes) < seg["max_planes"]:
        if len(remaining.points) < seg["ransac_n"]:
            break
        (a, b, c, d), inliers = remaining.segment_plane(
            distance_threshold=seg["distance_threshold_m"],
            ransac_n=seg["ransac_n"],
            num_iterations=seg["num_iterations"],
        )
        if len(inliers) < seg["min_support_points"]:
            break
        pts = np.asarray(remaining.points)[inliers]
        normal = np.array([a, b, c], dtype=np.float64)
        normal = normal / np.linalg.norm(normal)
        planes.append(Plane(id=len(planes), normal=normal, point=pts.mean(axis=0), area=None, support=len(inliers)))
        remaining = remaining.select_by_index(inliers, invert=True)
    return planes


def model_planes_from_mesh(mesh: trimesh.Trimesh, params: dict) -> list[Plane]:
    """Recover each original element as a cluster of mesh faces sharing a
    (normal direction, plane offset) key — works on any mesh, not just
    Phase-1 output."""
    normals = mesh.face_normals
    centers = mesh.triangles_center
    areas = mesh.area_faces
    offsets = np.einsum("ij,ij->i", normals, centers)

    n = len(mesh.faces)
    assigned = -np.ones(n, dtype=int)
    clusters: list[list[int]] = []
    ang_tol = params["coplanarity_angle_deg"]
    off_tol = params["coplanarity_dist_m"]

    for i in range(n):
        if assigned[i] != -1:
            continue
        cid = len(clusters)
        assigned[i] = cid
        members = [i]
        for j in range(i + 1, n):
            if assigned[j] != -1:
                continue
            cos_ang = np.clip(np.dot(normals[i], normals[j]), -1.0, 1.0)
            if np.degrees(np.arccos(cos_ang)) < ang_tol and abs(offsets[i] - offsets[j]) < off_tol:
                assigned[j] = cid
                members.append(j)
        clusters.append(members)

    planes = []
    for cid, members in enumerate(clusters):
        w = areas[members]
        planes.append(
            Plane(
                id=cid,
                normal=normals[members[0]],
                point=np.average(centers[members], axis=0, weights=w),
                area=float(w.sum()),
                support=len(members),
            )
        )
    return planes


def match_planes(cloud_planes: list[Plane], model_planes: list[Plane], params: dict) -> list[PlaneMatch]:
    mp = params["plane_match"]
    BIG = 1e6
    if not cloud_planes or not model_planes:
        return []
    cost = np.full((len(cloud_planes), len(model_planes)), BIG)
    for i, cp in enumerate(cloud_planes):
        for j, mpl in enumerate(model_planes):
            cos_ang = np.clip(np.dot(cp.normal, mpl.normal), -1.0, 1.0)
            # abs(): a RANSAC-fitted plane's normal sign is arbitrary.
            ang = np.degrees(np.arccos(abs(cos_ang)))
            if ang > mp["max_normal_angle_deg"]:
                continue
            dist = float(np.linalg.norm(cp.point - mpl.point))
            if dist > mp["max_centroid_dist_m"]:
                continue
            area_term = 0.0
            if mpl.area:
                approx_cloud_area = cp.support / mp["cloud_point_density_per_m2"]
                area_term = abs(approx_cloud_area - mpl.area) / mpl.area
            cost[i, j] = ang + mp["centroid_weight"] * dist + mp["area_weight"] * area_term

    row, col = linear_sum_assignment(cost)
    matches = []
    for i, j in zip(row, col):
        if cost[i, j] >= BIG:
            continue
        cp, mpl = cloud_planes[i], model_planes[j]
        cos_ang = np.clip(np.dot(cp.normal, mpl.normal), -1.0, 1.0)
        matches.append(
            PlaneMatch(
                cloud_plane=cp,
                model_plane=mpl,
                normal_angle_deg=float(np.degrees(np.arccos(abs(cos_ang)))),
                centroid_dist_m=float(np.linalg.norm(cp.point - mpl.point)),
            )
        )
    return matches


def _solve_once(matches: list[PlaneMatch]) -> np.ndarray:
    Nc = np.stack([m.cloud_plane.normal for m in matches])  # (k,3)
    Nm = np.stack([m.model_plane.normal for m in matches])  # (k,3)
    # Each RANSAC plane's normal sign is arbitrary; align cloud normals to
    # point the same way as their matched model normal before solving.
    flip = np.sign(np.einsum("ij,ij->i", Nc, Nm))
    flip[flip == 0] = 1.0
    Nc = Nc * flip[:, None]

    U, S, Vt = np.linalg.svd(Nc.T @ Nm)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T

    # n_model . (R p_cloud + t) = n_model . p_model  =>  n_model . t = n_model.p_model - n_model.(R p_cloud)
    A = Nm
    b = np.array(
        [
            np.dot(m.model_plane.normal, m.model_plane.point) - np.dot(m.model_plane.normal, R @ m.cloud_plane.point)
            for m in matches
        ]
    )
    t, *_ = np.linalg.lstsq(A, b, rcond=None)

    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def solve_rigid_from_planes(matches: list[PlaneMatch], params: dict) -> np.ndarray:
    """Rotation from matched normal pairs (Kabsch/SVD); translation from the
    matched planes' offset equations (least-squares).

    Robust to a minority of genuinely-deviated elements (expected by this
    project's whole premise: some as-built elements really are out of
    tolerance, per Phase 1's ground_truth.json nominal_deviation) — an
    ordinary unweighted least-squares over ALL matched planes lets one
    deviated plane's offset equation bias the shared rigid transform, and
    every OTHER (non-deviated) plane absorbs part of that bias too. One
    outlier-rejection pass drops the highest-residual match(es) and refits,
    provided enough matches remain — see specs/plan/phase-2-registration.md §5.
    """
    mp = params["plane_match"]
    if len(matches) < mp["min_correspondences"]:
        raise InsufficientPlaneMatchesError(
            f"only {len(matches)} plane matches (need >= {mp['min_correspondences']})"
        )

    Nc = np.stack([m.cloud_plane.normal for m in matches])
    Nm = np.stack([m.model_plane.normal for m in matches])
    flip = np.sign(np.einsum("ij,ij->i", Nc, Nm))
    flip[flip == 0] = 1.0
    Nc_aligned = Nc * flip[:, None]
    S = np.linalg.svd(Nc_aligned.T @ Nm, compute_uv=False)
    if S[-1] < mp["min_normal_rank_singular_value"]:
        raise InsufficientPlaneMatchesError("matched normals span < 3 independent directions")

    T = _solve_once(matches)
    threshold = mp.get("robust_residual_threshold_m")
    if threshold is not None:
        R, t = T[:3, :3], T[:3, 3]
        residuals = np.array(
            [
                abs(np.dot(m.model_plane.normal, R @ m.cloud_plane.point + t) - np.dot(m.model_plane.normal, m.model_plane.point))
                for m in matches
            ]
        )
        keep = [m for m, r in zip(matches, residuals) if r <= threshold]
        if len(keep) >= mp["min_correspondences"] and len(keep) < len(matches):
            T = _solve_once(keep)

    return T
