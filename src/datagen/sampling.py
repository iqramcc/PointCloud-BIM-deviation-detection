"""Area-weighted point sampling from a labelled mesh (FR-1.3)."""
from __future__ import annotations

import numpy as np
import trimesh


def sample_cloud(
    mesh: trimesh.Trimesh,
    face_element_ids: np.ndarray,
    density_per_m2: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample points ~uniformly over surface area.

    Returns (points (N,3), normals (N,3) — the owning face's normal, element_ids (N,)).
    trimesh.sample.sample_surface is already area-weighted, so this satisfies
    FR-1.3's "approximately uniform over area" directly.
    """
    n_points = max(1, round(density_per_m2 * mesh.area))
    points, face_indices = trimesh.sample.sample_surface(mesh, n_points, seed=rng)
    normals = mesh.face_normals[face_indices]
    element_ids = face_element_ids[face_indices]
    return np.asarray(points), np.asarray(normals), element_ids
