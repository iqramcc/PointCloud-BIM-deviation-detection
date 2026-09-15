"""Element representation: every scene element is a planar rectangular patch.

See specs/plan/phase-1-synthetic-data.md §2 for the rationale (keeps "one outward
normal per element" in ground_truth.json exactly true).
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError(f"cannot normalize near-zero vector {v}")
    return v / n


@dataclass(frozen=True)
class Element:
    """A labelled planar rectangular patch (wall / slab / column face)."""

    id: int
    cls: str
    center: np.ndarray  # (3,) world-space centroid, meters
    normal: np.ndarray  # (3,) unit outward normal
    u_axis: np.ndarray  # (3,) unit in-plane "width" direction, perpendicular to normal
    width: float  # meters, along u_axis
    height: float  # meters, along v_axis = normal x u_axis

    def __post_init__(self) -> None:
        object.__setattr__(self, "center", np.asarray(self.center, dtype=np.float64))
        object.__setattr__(self, "normal", _unit(self.normal))
        u = np.asarray(self.u_axis, dtype=np.float64)
        # Gram-Schmidt: force u_axis perpendicular to normal so callers can pass an
        # approximate in-plane direction without doing the projection themselves.
        u = u - np.dot(u, self.normal) * self.normal
        object.__setattr__(self, "u_axis", _unit(u))
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"element {self.id}: width/height must be positive")

    @property
    def v_axis(self) -> np.ndarray:
        return np.cross(self.normal, self.u_axis)

    def corners(self) -> np.ndarray:
        """Return the 4 world-space corners, CCW as seen from +normal."""
        hw, hh = self.width / 2.0, self.height / 2.0
        u, v = self.u_axis, self.v_axis
        return np.stack(
            [
                self.center - hw * u - hh * v,
                self.center + hw * u - hh * v,
                self.center + hw * u + hh * v,
                self.center - hw * u + hh * v,
            ]
        )

    def quad_mesh(self) -> tuple[np.ndarray, np.ndarray]:
        """Two-triangle quad: (vertices (4,3), faces (2,3)) with outward normal
        matching self.normal (verified by the winding order derivation in the plan)."""
        verts = self.corners()
        faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)
        return verts, faces

    def offset(self, distance_m: float) -> "Element":
        """Return a copy translated along the outward normal by distance_m."""
        return replace(self, center=self.center + distance_m * self.normal)

    def in_plane_shift(self, du_m: float = 0.0, dv_m: float = 0.0) -> "Element":
        return replace(self, center=self.center + du_m * self.u_axis + dv_m * self.v_axis)

    def tilt(self, angle_deg: float, about_axis: str = "u") -> "Element":
        """Rotate the element's normal (and the other in-plane axis) about u_axis or
        v_axis through the element's own center, by angle_deg."""
        axis = self.u_axis if about_axis == "u" else self.v_axis
        theta = np.radians(angle_deg)
        k = _unit(axis)

        def rotate(vec: np.ndarray) -> np.ndarray:
            # Rodrigues' rotation formula.
            return (
                vec * np.cos(theta)
                + np.cross(k, vec) * np.sin(theta)
                + k * np.dot(k, vec) * (1 - np.cos(theta))
            )

        new_normal = rotate(self.normal)
        new_u = rotate(self.u_axis)
        return replace(self, normal=new_normal, u_axis=new_u)
