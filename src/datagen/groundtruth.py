"""ground_truth.json schema v1 (FR-1.8) — see specs/srs/phase-1-synthetic-data.md §5.2."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

from .elements import Element

SCHEMA_VERSION = 1


def _is_out_of_tolerance(deviation: dict | None, tolerance_mm: float) -> bool:
    if deviation is None:
        return False
    if "value_mm" in deviation:
        return abs(deviation["value_mm"]) > tolerance_mm
    # Angular deviations (tilt) aren't directly comparable to a linear
    # tolerance; documented simplification for Phase 1 (see plan §2).
    return False


def build_ground_truth(
    scene_id: str,
    seed: int,
    grid_point: dict,
    T_gt: np.ndarray,
    sensor: dict,
    point_density_per_m2: float,
    elements: Sequence[Element],
    nominal_deviations: dict[int, dict],
    tolerance_mm: float,
) -> dict:
    element_records = []
    for el in elements:
        deviation = nominal_deviations.get(el.id)
        element_records.append(
            {
                "id": el.id,
                "class": el.cls,
                "normal": el.normal.tolist(),
                "nominal_deviation": deviation,
                "is_out_of_tolerance": _is_out_of_tolerance(deviation, tolerance_mm),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "scene_id": scene_id,
        "seed": seed,
        "grid_point": grid_point,
        "T_gt": T_gt.tolist(),
        "sensor": sensor,
        "point_density_per_m2": point_density_per_m2,
        "elements": element_records,
        "tolerance_mm": tolerance_mm,
        "notes": "",
    }


def write_ground_truth(gt: dict, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gt, f, indent=2, sort_keys=False)


def read_ground_truth(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
