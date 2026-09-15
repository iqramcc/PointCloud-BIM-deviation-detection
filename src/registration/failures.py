"""Structured, catchable registration failures — never a bare crash (NFR-2.3).

Open3D's RANSAC/ICP calls never raise on their own; they return a low-fitness
`RegistrationResult` instead. Each stage explicitly checks fitness/correspondence
counts against a threshold in the frozen params and raises one of these.
"""
from __future__ import annotations

from dataclasses import dataclass


class RegistrationStageError(RuntimeError):
    """Base class; .stage and .reason feed a RegistrationFailure record."""

    stage: str = "unknown"
    reason: str = "unknown"


class RansacNoConsensusError(RegistrationStageError):
    stage, reason = "coarse_a", "ransac_no_consensus"


class InsufficientPlaneMatchesError(RegistrationStageError):
    stage, reason = "coarse_b", "insufficient_plane_matches"


class ICPDivergenceError(RegistrationStageError):
    stage, reason = "icp", "icp_divergence"


@dataclass(frozen=True)
class RegistrationFailure:
    stage: str
    reason: str
    detail: str

    def as_dict(self) -> dict:
        return {"stage": self.stage, "reason": self.reason, "detail": self.detail}
