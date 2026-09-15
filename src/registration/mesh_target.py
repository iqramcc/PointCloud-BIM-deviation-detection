"""The one shared target cloud: FPFH target (Baseline A), ICP target (both
baselines), and the alignment-RMSE reference set (metrics.py) — one function,
three consumers, part of what keeps A and B's fine-registration stage identical.
"""
from __future__ import annotations

import numpy as np
import open3d as o3d
import trimesh

from datagen.sampling import sample_cloud


def mesh_to_point_cloud(mesh: trimesh.Trimesh, params: dict, rng: np.random.Generator) -> o3d.geometry.PointCloud:
    """Deterministic point + analytic-normal sampling of the as-designed mesh."""
    dummy_face_ids = np.zeros(len(mesh.faces), dtype=np.int64)  # sample_cloud's ids output is unused here
    points, normals, _ = sample_cloud(mesh, dummy_face_ids, params["density_per_m2"], rng)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.normals = o3d.utility.Vector3dVector(normals)
    return pcd
