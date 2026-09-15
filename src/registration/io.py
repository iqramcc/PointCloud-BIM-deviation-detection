"""registration_metrics.json schema v1 read/write — see specs/srs/phase-2-registration.md
§5.2 (success case) and specs/plan/phase-2-registration.md §9 (failure-case extension)."""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_VERSION = 1


def write_registration_metrics(metrics: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=False)


def read_registration_metrics(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
