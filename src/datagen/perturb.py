"""Nominal deviations, registration perturbation, sensor noise, occlusion.

FR-1.4 (nominal deviation), FR-1.5 (registration perturbation T_gt),
FR-1.6 (noise), FR-1.7 (occlusion).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import open3d as o3d

from .elements import Element

MM = 1.0e-3


def apply_nominal_deviations(
    elements: Sequence[Element], deviations: dict[int, dict]
) -> tuple[list[Element], dict[int, dict]]:
    """Apply per-element nominal deviations before sampling (FR-1.4).

    deviations: {element_id: {"type": "normal_offset"|"in_plane"|"tilt", "value_mm"
    or "value_deg": float}}. Returns (new_elements, applied_records) where
    applied_records is keyed by element id and safe to drop straight into
    ground_truth.json's per-element "nominal_deviation" field.
    """
    by_id = {el.id: el for el in elements}
    applied: dict[int, dict] = {}
    for el_id, spec in deviations.items():
        el = by_id[el_id]
        dtype = spec["type"]
        if dtype == "normal_offset":
            value_mm = float(spec["value_mm"])
            by_id[el_id] = el.offset(value_mm * MM)
            applied[el_id] = {"type": dtype, "value_mm": value_mm}
        elif dtype == "in_plane":
            value_mm = float(spec["value_mm"])
            by_id[el_id] = el.in_plane_shift(du_m=value_mm * MM)
            applied[el_id] = {"type": dtype, "value_mm": value_mm}
        elif dtype == "tilt":
            value_deg = float(spec["value_deg"])
            by_id[el_id] = el.tilt(value_deg)
            applied[el_id] = {"type": dtype, "value_deg": value_deg}
        else:
            raise ValueError(f"unknown deviation type {dtype!r}")
    new_elements = [by_id[el.id] for el in elements]
    return new_elements, applied


def sample_registration_transform(
    rot_deg: float, trans_mm: float, rng: np.random.Generator
) -> np.ndarray:
    """Draw a random-axis/random-direction rigid transform of the given
    magnitude (FR-1.5). Returns a 4x4 matrix T_gt."""
    T = np.eye(4)
    if rot_deg > 0:
        axis = rng.normal(size=3)
        axis /= np.linalg.norm(axis)
        theta = np.radians(rot_deg)
        k = axis
        K = np.array(
            [[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]
        )
        R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)
        T[:3, :3] = R
    if trans_mm > 0:
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        T[:3, 3] = direction * trans_mm * MM
    return T


def add_noise(
    points: np.ndarray,
    normals: np.ndarray,
    sigma_mm: float,
    rng: np.random.Generator,
    isotropic_sigma_mm: float = 0.0,
    outlier_rate: float = 0.0,
) -> np.ndarray:
    """Gaussian noise along local surface normal, optional isotropic jitter
    and sparse outliers (FR-1.6)."""
    pts = points.copy()
    n = len(pts)
    if sigma_mm > 0:
        along_normal = rng.normal(0.0, sigma_mm * MM, size=n)
        pts = pts + along_normal[:, None] * normals
    if isotropic_sigma_mm > 0:
        pts = pts + rng.normal(0.0, isotropic_sigma_mm * MM, size=pts.shape)
    if outlier_rate > 0:
        n_outliers = int(round(outlier_rate * n))
        if n_outliers > 0:
            idx = rng.choice(n, size=n_outliers, replace=False)
            spread = pts.max(axis=0) - pts.min(axis=0)
            spread = np.where(spread < 1e-6, 1.0, spread)
            pts[idx] = pts[idx] + rng.uniform(-1.0, 1.0, size=(n_outliers, 3)) * spread
    return pts


_OCCLUSION_ORIGIN_COUNT = {"none": None, "moderate": 2, "heavy": 1}


def apply_occlusion(
    points: np.ndarray,
    normals: np.ndarray,
    element_ids: np.ndarray,
    scanner_origins: np.ndarray,
    level: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hidden-point-removal visibility filtering from one or more scanner
    origins (FR-1.7). Keeps the union of points visible from any used origin."""
    if level not in _OCCLUSION_ORIGIN_COUNT:
        raise ValueError(f"unknown occlusion level {level!r}")
    if level == "none" or len(scanner_origins) == 0:
        return points, normals, element_ids

    n_origins = min(_OCCLUSION_ORIGIN_COUNT[level], len(scanner_origins))
    use_origins = scanner_origins[:n_origins]

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    diameter = np.linalg.norm(points.max(axis=0) - points.min(axis=0))
    radius = diameter * 100.0  # open3d hidden_point_removal convention

    visible_mask = np.zeros(len(points), dtype=bool)
    for origin in use_origins:
        _, idx_map = pcd.hidden_point_removal(origin.tolist(), radius)
        visible_mask[np.asarray(idx_map)] = True

    return points[visible_mask], normals[visible_mask], element_ids[visible_mask]
