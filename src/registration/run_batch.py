"""Batch CLI: run register() over a filtered slice of a manifest.csv, writing one
registration_metrics.json per sample plus a flat summary.csv.

    python -m registration.run_batch --manifest data/S1/manifest.csv --method A \
        --filter "noise_sigma_mm==1 and occlusion=='none'" \
        --params configs/registration_params.yaml --out results/registration/S1_A
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import pandas as pd

from datagen.groundtruth import read_ground_truth
from datagen.io import read_cloud_ply, read_mesh_ply
from .api import register
from .io import write_registration_metrics
from .params import load_params


def run_batch(manifest_path: str | Path, method: str, params_path: str | Path, out_dir: str | Path, query: str | None = None) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_path)
    if query:
        manifest = manifest.query(query)

    params_base = load_params(params_path)
    out_dir = Path(out_dir)
    rows = []
    for _, row in manifest.iterrows():
        sample_dir = Path(row["cloud_path"]).parent
        points, normals = read_cloud_ply(row["cloud_path"])
        mesh = read_mesh_ply(row["mesh_path"])
        gt = read_ground_truth(row["ground_truth_path"])
        params = {**params_base, "T_gt": np.array(gt["T_gt"]), "seed": int(row["seed"])}

        try:
            _, metrics = register((points, normals), mesh, method, params)
        except Exception as exc:  # defense-in-depth: one bad sample can't kill the batch
            metrics = {
                "schema_version": 1, "method": method, "status": "failed", "T_est": None,
                "coarse": None, "icp": None, "error_vs_gt": None,
                "failure": {"stage": "unknown", "reason": "unexpected_exception", "detail": str(exc)},
                "runtime_total_s": None,
            }

        metrics_path = out_dir / row["sample_id"] / "registration_metrics.json"
        write_registration_metrics(metrics, metrics_path)

        err = metrics.get("error_vs_gt") or {}
        coarse = metrics.get("coarse") or {}
        icp = metrics.get("icp") or {}
        rows.append(
            {
                "sample_id": row["sample_id"],
                "rot_deg": row["rot_deg"],
                "trans_mm": row["trans_mm"],
                "status": metrics["status"],
                "rot_err_deg": err.get("rot_deg"),
                "trans_err_mm": err.get("trans_mm"),
                "rmse_mm": err.get("rmse_mm"),
                "coarse_runtime_s": coarse.get("runtime_s"),
                "icp_runtime_s": icp.get("runtime_s"),
                "runtime_total_s": metrics.get("runtime_total_s"),
            }
        )

    summary = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "summary.csv", index=False)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-run registration over a manifest slice.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--method", required=True, choices=["A", "B", "B_seeded"])
    parser.add_argument("--params", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--filter", default=None, help="pandas .query() expression over the manifest")
    args = parser.parse_args()
    summary = run_batch(args.manifest, args.method, args.params, args.out, query=args.filter)
    print(f"wrote {len(summary)} rows to {Path(args.out) / 'summary.csv'}")


if __name__ == "__main__":
    main()
