"""Build a labelled as-designed mesh from a scene YAML (FR-1.1, FR-1.2)."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import trimesh
import yaml

from .elements import Element


def load_scene_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _elements_from_config(cfg: dict) -> list[Element]:
    elements = []
    for e in cfg["elements"]:
        elements.append(
            Element(
                id=int(e["id"]),
                cls=str(e["cls"]),
                center=np.array(e["center"], dtype=np.float64),
                normal=np.array(e["normal"], dtype=np.float64),
                u_axis=np.array(e["u_axis"], dtype=np.float64),
                width=float(e["width"]),
                height=float(e["height"]),
            )
        )
    ids = [el.id for el in elements]
    if len(ids) != len(set(ids)):
        raise ValueError(f"scene {cfg.get('scene_id')}: duplicate element ids in {ids}")
    return elements


def build_mesh(elements: Sequence[Element]) -> tuple[trimesh.Trimesh, np.ndarray]:
    """Assemble one trimesh from per-element quads.

    Returns (mesh, face_element_ids) where face_element_ids[i] is the owning
    Element.id of mesh.faces[i] (FR-1.1: "each element carries a stable
    integer ID").
    """
    all_verts = []
    all_faces = []
    face_element_ids = []
    vertex_offset = 0
    for el in elements:
        verts, faces = el.quad_mesh()
        all_verts.append(verts)
        all_faces.append(faces + vertex_offset)
        face_element_ids.extend([el.id] * len(faces))
        vertex_offset += len(verts)

    vertices = np.concatenate(all_verts, axis=0)
    faces = np.concatenate(all_faces, axis=0)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    return mesh, np.array(face_element_ids, dtype=np.int64)


def generate_scene(scene_cfg: str | Path | dict) -> tuple[trimesh.Trimesh, list[Element], np.ndarray]:
    """Load a scene YAML (or an already-loaded dict) and build its mesh.

    Returns (mesh, elements, face_element_ids).
    """
    cfg = scene_cfg if isinstance(scene_cfg, dict) else load_scene_config(scene_cfg)
    elements = _elements_from_config(cfg)
    mesh, face_element_ids = build_mesh(elements)
    return mesh, elements, face_element_ids


def scanner_origins(scene_cfg: dict) -> np.ndarray:
    return np.array(scene_cfg.get("scanner_origins_m", []), dtype=np.float64)
