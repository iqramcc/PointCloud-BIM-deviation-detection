"""Phase 1 demonstrable artifact (SRS §7.6): S1 and S2, each as as-designed
mesh (wireframe) + as-built cloud (scatter), one deviated element highlighted.

    python scripts/render_phase1_figure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datagen.build_dataset import make_sample  # noqa: E402
from datagen.io import read_cloud_ply, read_mesh_ply  # noqa: E402
from datagen.scene import generate_scene  # noqa: E402

DEVIATED_ELEMENT = {"S1": 3, "S2": 2}
OUT_PATH = Path(__file__).resolve().parents[1] / "reports" / "figures" / "phase1_scenes.png"


def _plot_scene(ax, scene_id: str, mesh, elements, points, deviated_id: int) -> None:
    for tri in mesh.triangles:
        pts = np.vstack([tri, tri[0]])
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="0.3", linewidth=0.6, alpha=0.7)

    by_id = {e.id: e for e in elements}
    if deviated_id in by_id:
        el = by_id[deviated_id]
        corners = np.vstack([el.corners(), el.corners()[0]])
        ax.plot(corners[:, 0], corners[:, 1], corners[:, 2], color="crimson", linewidth=2.5)

    step = max(1, len(points) // 4000)
    sub = points[::step]
    ax.scatter(sub[:, 0], sub[:, 1], sub[:, 2], s=1, color="steelblue", alpha=0.5)

    ax.set_title(f"{scene_id} — as-designed mesh + as-built cloud\n(deviated element {deviated_id} in red)")
    ax.set_box_aspect([np.ptp(mesh.vertices[:, i]) or 1 for i in range(3)])
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")


def main() -> None:
    fig = plt.figure(figsize=(13, 6))
    for i, scene_id in enumerate(["S1", "S2"]):
        deviated_id = DEVIATED_ELEMENT[scene_id]
        out_dir = Path("data") / "_figure_tmp" / scene_id
        gt = make_sample(
            scene_id,
            grid_point={"rot_deg": 0.0, "trans_mm": 0.0, "noise_sigma_mm": 2.0, "occlusion": "moderate"},
            seed=0,
            nominal_deviations={deviated_id: {"type": "normal_offset", "value_mm": 14.0}},
            tolerance_mm=10.0,
            density_per_m2=300,
            out_dir=out_dir,
        )
        points, _ = read_cloud_ply(out_dir / "cloud.ply")
        mesh = read_mesh_ply(out_dir / "scene_mesh.ply")
        _, elements, _ = generate_scene(f"configs/scenes/{scene_id}.yaml")

        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        _plot_scene(ax, scene_id, mesh, elements, points, deviated_id)

    fig.suptitle("Phase 1 demonstrable artifact — synthetic as-designed / as-built pairs", fontsize=13)
    fig.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=160)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
