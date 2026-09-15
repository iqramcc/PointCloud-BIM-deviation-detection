"""Phase 2 SRS §7 item 3 / NFR-2.1: the ICP parameter object passed into
refine_icp is the exact same instance for both baselines, and refine_icp is
called exactly once per register() call.

Coarse registration (especially Baseline A's RANSAC) is a real algorithm that
can legitimately fail to converge on hard inputs (see
specs/plan/phase-2-registration.md §4's calibration finding) — that failure
rate is a finding about the *baseline*, not about the *fairness architecture*
this test checks. So coarse_register_A/coarse_register_B are stubbed here with
a fixed instantaneous transform, isolating exactly what NFR-2.1 is about: does
register() route both methods through one shared refine_icp call site with the
same params object, regardless of which coarse stage produced the input."""
import numpy as np
import open3d as o3d

import registration.api as api
from registration.params import load_params

DUMMY_T = np.eye(4)


def test_icp_params_object_identical_instance_across_baselines(monkeypatch):
    seen_ids = []
    call_count = {"n": 0}
    real_refine_icp = api.refine_icp

    def spy(cloud_p, mesh_sample, T_coarse, params):
        seen_ids.append(id(params))
        call_count["n"] += 1
        return real_refine_icp(cloud_p, mesh_sample, T_coarse, params)

    monkeypatch.setattr(api, "refine_icp", spy)
    monkeypatch.setattr(api, "coarse_register_A", lambda cloud_p, mesh_sample, params: (DUMMY_T, {"fitness": 1.0, "inlier_rmse_mm": 0.0, "runtime_s": 0.0}))
    monkeypatch.setattr(api, "coarse_register_B", lambda cloud_p, model_planes, params, seeds=None: (DUMMY_T, {"fitness": None, "inlier_rmse_mm": None, "runtime_s": 0.0, "n_plane_matches": 5}))

    mesh_o3d = o3d.geometry.TriangleMesh.create_box().subdivide_midpoint(1)
    import trimesh

    tmesh = trimesh.Trimesh(vertices=np.asarray(mesh_o3d.vertices), faces=np.asarray(mesh_o3d.triangles), process=False)

    # Sample the cloud directly from the mesh (T_coarse = identity is then
    # trivially a near-perfect starting point) so ICP reliably converges —
    # this test is about the shared call site's object identity, not about
    # registration accuracy on hard inputs.
    rng = np.random.default_rng(0)
    sampled_points, face_idx = trimesh.sample.sample_surface(tmesh, 2000, seed=rng)
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.asarray(sampled_points))
    cloud.normals = o3d.utility.Vector3dVector(tmesh.face_normals[face_idx])

    params = load_params("configs/registration_params.yaml")

    _, metrics_a = api.register(cloud, tmesh, "A", params)
    _, metrics_b = api.register(cloud, tmesh, "B", params)

    assert metrics_a["status"] == "ok" and metrics_b["status"] == "ok"
    assert call_count["n"] == 2
    assert seen_ids[0] == seen_ids[1] == id(params["icp"])
