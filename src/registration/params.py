"""Frozen parameter table loading (Constitution Art. IV).

See configs/registration_params.yaml and specs/plan/phase-2-registration.md §10.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


def load_params(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def params_hash(params: dict) -> str:
    """sha256 of a canonical JSON encoding, excluding per-call keys (T_gt, seed)
    that aren't part of the frozen table itself."""
    stable = {k: v for k, v in params.items() if k not in ("T_gt", "seed")}
    canonical = json.dumps(stable, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
