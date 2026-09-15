"""registration_error (FR-2.15) — the single place T_gt is consumed (NFR-2.4).

ground_truth.json's T_gt is BIM-frame -> cloud-frame (datagen convention,
confirmed from datagen/build_dataset.py and tests/test_roundtrip.py). T_est is
cloud-frame -> mesh-frame (the natural sense of Open3D's RANSAC/ICP results),
so this is the one place that inverts T_gt before comparing.
"""
from __future__ import annotations

import numpy as np

_DEFAULT_REF_POINTS_M = np.array(
    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 1.0, 1.0]]
)


def registration_error(T_est: np.ndarray, T_gt: np.ndarray, ref_points_m: np.ndarray | None = None) -> dict:
    T_gt_aligned = np.linalg.inv(T_gt)
    R_err = T_est[:3, :3] @ T_gt_aligned[:3, :3].T
    cos_ang = np.clip((np.trace(R_err) - 1.0) / 2.0, -1.0, 1.0)
    rot_deg = float(np.degrees(np.arccos(cos_ang)))
    trans_mm = float(np.linalg.norm(T_est[:3, 3] - T_gt_aligned[:3, 3]) * 1000.0)

    pts = ref_points_m if ref_points_m is not None else _DEFAULT_REF_POINTS_M
    pts_h = np.hstack([pts, np.ones((len(pts), 1))])
    a = (T_est @ pts_h.T).T[:, :3]
    b = (T_gt_aligned @ pts_h.T).T[:, :3]
    rmse_mm = float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))) * 1000.0)
    return {"rot_deg": rot_deg, "trans_mm": trans_mm, "rmse_mm": rmse_mm}
