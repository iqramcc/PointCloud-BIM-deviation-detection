"""Phase 2 demonstrable artifact (SRS §7 item 6): error/runtime table for A and
B across the clean registration-error axis on S1, plus one before/after
alignment render per method. Mirrors scripts/render_phase1_figure.py's role.

    python scripts/render_phase2_figure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datagen.groundtruth import read_ground_truth  # noqa: E402
from datagen.io import read_cloud_ply, read_mesh_ply  # noqa: E402
from registration.api import register  # noqa: E402
from registration.params import load_params  # noqa: E402
from registration.run_batch import run_batch  # noqa: E402

TABLE_OUT = Path("reports/tables/phase2_registration_errors.csv")
FIGURE_DIR = Path("reports/figures")
ALIGNMENT_SAMPLE = "rot2.0_trans50_noise1_none/seed0"


def _plot_alignment(ax, title, mesh_points, cloud_before, cloud_after):
    step_m = max(1, len(mesh_points) // 3000)
    ax.scatter(*mesh_points[::step_m].T, s=1, color="0.4", alpha=0.4, label="as-designed (sampled)")
    step_c = max(1, len(cloud_before) // 3000)
    ax.scatter(*cloud_before[::step_c].T, s=1, color="crimson", alpha=0.3, label="as-built (before)")
    ax.scatter(*cloud_after[::step_c].T, s=1, color="steelblue", alpha=0.5, label="as-built (after T_est)")
    ax.set_title(title)
    ax.legend(markerscale=8, fontsize=7)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")


def main() -> None:
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    tables = {}
    for method in ("A", "B"):
        summary = run_batch(
            "data/S1/manifest.csv",
            method,
            "configs/registration_params.yaml",
            f"results/registration/S1_{method}",
            # seed==0 only (25 samples/method): the full noise1_none slice is 250/method,
            # and Baseline A's RANSAC alone runs ~2-12s/call (see the calibration finding
            # in specs/tasks/phase-2-registration.md) — this subset is enough to populate
            # the gate-6 table without a 40+ minute render.
            query="noise_sigma_mm==1 and occlusion=='none' and seed==0",
        )
        tables[method] = summary

    import pandas as pd
    combined = pd.concat([tables["A"].assign(method="A"), tables["B"].assign(method="B")], ignore_index=True)
    combined.to_csv(TABLE_OUT, index=False)
    print(f"wrote {TABLE_OUT}")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    pivot = combined.groupby(["method", "status"]).size().unstack(fill_value=0)
    ax.table(cellText=pivot.values, rowLabels=pivot.index, colLabels=pivot.columns, loc="center")
    fig.savefig(FIGURE_DIR / "phase2_status_table.png", dpi=160)

    sample_dir = Path("data/S1") / ALIGNMENT_SAMPLE
    points, normals = read_cloud_ply(sample_dir / "cloud.ply")
    mesh = read_mesh_ply(sample_dir / "scene_mesh.ply")
    gt = read_ground_truth(sample_dir / "ground_truth.json")
    T_gt = np.array(gt["T_gt"])
    params_base = load_params("configs/registration_params.yaml")
    mesh_points = mesh.sample(3000)

    for method in ("A", "B"):
        params = {**params_base, "T_gt": T_gt}
        T_est, metrics = register((points, normals), mesh, method, params)
        fig = plt.figure(figsize=(7, 6))
        ax = fig.add_subplot(projection="3d")
        if metrics["status"] == "ok":
            pts_h = np.hstack([points, np.ones((len(points), 1))])
            after = (T_est @ pts_h.T).T[:, :3]
        else:
            after = points
        _plot_alignment(ax, f"Baseline {method} — before/after alignment\nstatus={metrics['status']}", mesh_points, points, after)
        fig.tight_layout()
        out = FIGURE_DIR / f"phase2_alignment_{method}.png"
        fig.savefig(out, dpi=160)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
