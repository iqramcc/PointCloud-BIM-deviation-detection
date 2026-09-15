"""cloud.ply / scene_mesh.ply read-write via Open3D (deterministic byte output)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh


def write_cloud_ply(path: str | Path, points: np.ndarray, normals: np.ndarray | None = None) -> None:
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    if normals is not None:
        pcd.normals = o3d.utility.Vector3dVector(normals)
    o3d.io.write_point_cloud(str(path), pcd, write_ascii=False, compressed=False)


def read_cloud_ply(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    pcd = o3d.io.read_point_cloud(str(path))
    return np.asarray(pcd.points), np.asarray(pcd.normals)


def write_mesh_ply(path: str | Path, mesh: trimesh.Trimesh) -> None:
    mesh.export(str(path), file_type="ply", encoding="binary")


def read_mesh_ply(path: str | Path) -> trimesh.Trimesh:
    return trimesh.load(str(path), file_type="ply", process=False)
