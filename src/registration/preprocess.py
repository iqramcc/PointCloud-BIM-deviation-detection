"""Shared preprocessing (FR-2.1-2.4): voxel downsample -> outlier removal -> normals.

Called exactly once per register() call, before the method branch (see api.py) —
this is what makes "identical preprocessing for both baselines" true by
construction, not convention (Constitution Art. IV / NFR-2.1).
"""
from __future__ import annotations

import open3d as o3d


def preprocess(cloud: o3d.geometry.PointCloud, params: dict) -> o3d.geometry.PointCloud:
    pcd = cloud.voxel_down_sample(params["voxel_size_m"])
    pcd, _ = pcd.remove_statistical_outlier(
        nb_neighbors=params["sor_neighbors"], std_ratio=params["sor_std_ratio"]
    )
    pcd.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=params["normal_radius_m"], max_nn=params["normal_max_nn"])
    )
    pcd.orient_normals_consistent_tangent_plane(k=params["normal_max_nn"])
    return pcd
