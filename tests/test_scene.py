import numpy as np
import pytest

from datagen.scene import generate_scene

SCENES = ["S1", "S2"]
EXPECTED_ELEMENT_COUNT = {"S1": 9, "S2": 7}


@pytest.mark.parametrize("scene_id", SCENES)
def test_element_count(scene_id):
    _, elements, _ = generate_scene(f"configs/scenes/{scene_id}.yaml")
    assert len(elements) == EXPECTED_ELEMENT_COUNT[scene_id]


@pytest.mark.parametrize("scene_id", SCENES)
def test_element_ids_unique_and_stable(scene_id):
    _, elements, _ = generate_scene(f"configs/scenes/{scene_id}.yaml")
    ids = [e.id for e in elements]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)


@pytest.mark.parametrize("scene_id", SCENES)
def test_normals_are_unit_length(scene_id):
    _, elements, _ = generate_scene(f"configs/scenes/{scene_id}.yaml")
    for el in elements:
        assert abs(np.linalg.norm(el.normal) - 1.0) < 1e-9


@pytest.mark.parametrize("scene_id", SCENES)
def test_face_normals_match_owning_element(scene_id):
    """Winding order must produce mesh face normals equal to the declared
    element outward normal (Plan §2)."""
    mesh, elements, face_ids = generate_scene(f"configs/scenes/{scene_id}.yaml")
    by_id = {e.id: e for e in elements}
    for i, fid in enumerate(face_ids):
        assert np.dot(mesh.face_normals[i], by_id[fid].normal) > 0.99


@pytest.mark.parametrize("scene_id", SCENES)
def test_face_element_ids_cover_all_faces(scene_id):
    mesh, elements, face_ids = generate_scene(f"configs/scenes/{scene_id}.yaml")
    assert len(face_ids) == len(mesh.faces)
    assert set(face_ids) == {e.id for e in elements}
