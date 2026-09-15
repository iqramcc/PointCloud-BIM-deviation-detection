# Plan — Phase 2: Registration Pipelines

**Status:** Draft v0.1 · Implements `specs/srs/phase-2-registration.md` (FR-2.1–2.18).
Technical design ("HOW"); requirements live in the SRS ("WHAT").

---

## 1. Module layout (Constitution Art. IX)

```
src/registration/
├── __init__.py
├── failures.py       # RegistrationStageError hierarchy + RegistrationFailure record
├── preprocess.py      # preprocess(cloud, params) -> cloud'
├── mesh_target.py       # mesh_to_point_cloud(mesh, params, rng) -> o3d.PointCloud
├── coarse_a.py            # coarse_register_A(...)
├── planes.py                # Plane, extract_cloud_planes, model_planes_from_mesh,
│                              match_planes, solve_rigid_from_planes
├── coarse_b.py                 # coarse_register_B(...)
├── icp.py                        # refine_icp(...) — the one shared fine stage
├── metrics.py                      # registration_error(...)
├── params.py                          # load_params, params_hash
├── io.py                                # registration_metrics.json read/write (schema v1)
├── api.py                                 # register(...) — single entry point
└── run_batch.py                             # CLI: manifest slice -> metrics jsons + summary csv

configs/
└── registration_params.yaml   # frozen parameter table (Art. IV)

scripts/
├── calibrate_registration_params.py   # one-time calibration helper, not in the test suite
└── render_phase2_figure.py             # Phase 2 demonstrable artifact

tests/
├── test_registration_identity.py
├── test_registration_recovery.py
├── test_registration_fairness.py
└── test_registration_failure.py
```

`registration` imports `numpy`, `scipy`, `open3d`, `trimesh`, `pyyaml`, plus `datagen.io`,
`datagen.sampling`, `datagen.groundtruth` (reused Phase-1 utilities — see §2 for why this
doesn't violate NFR-2.4). Nothing from `deviation` or `experiment`.

---

## 2. Interface convention decisions (resolving three SRS ambiguities)

### 2.1 T_est / T_gt convention
`ground_truth.json`'s `T_gt` is BIM-frame → cloud-frame (confirmed from
`datagen/build_dataset.py` and `tests/test_roundtrip.py`, which apply `inverse(T_gt)` to go
cloud → mesh). Open3D's RANSAC/ICP results are natively source → target, i.e. cloud → mesh,
in the opposite sense. `register()` returns `T_est` in the natural cloud → mesh sense — no
inversion inside any estimator stage. `registration_error(T_est, T_gt)` is the sole place
that inverts `T_gt` before comparing. This *is* the "evaluation helper" of NFR-2.4.

### 2.2 Model planes come from the mesh, not from ground_truth.json or the scene YAML
`ground_truth.json.elements[*]` has no centroid; `scene_mesh.ply` carries no face→element-id
metadata after export. `planes.model_planes_from_mesh(mesh)` recovers each element as a
cluster of mesh faces sharing a (normal, plane-offset) key — generic to any mesh, and keeps
`registration` from depending on Phase-1-specific scene config, which is *stronger*
modularity (Art. IX) than reading the YAML would have been.

### 2.3 `T_gt` inside `register()`'s fixed 4-argument signature
`T_gt` travels as an optional, non-tunable key, `params["T_gt"]`, added per-call by the
caller (tests, `run_batch.py`, the calibration script) — never present in
`configs/registration_params.yaml`. If absent, `metrics["error_vs_gt"] = None` (this is what
lets `register()` run on real, ground-truth-free data in Phase 5). `register()` only reads
`params["T_gt"]` as its last step, after `T_est` is already fixed by the coarse+ICP stages —
satisfying NFR-2.4's "never inside the estimator" literally.

---

## 3. Preprocessing (shared, FR-2.1–2.4)

`preprocess(cloud, params)`: `voxel_down_sample` → `remove_statistical_outlier` →
`estimate_normals` (`KDTreeSearchParamHybrid`) → `orient_normals_consistent_tangent_plane`.
One function; called exactly once in `register()`, before the method branch — this is what
makes "identical preprocessing for both baselines" true by construction, not convention.

---

## 4. Baseline A (FR-2.5–2.7)

`compute_fpfh_feature` on the preprocessed cloud and on a shared mesh-sampled target cloud
(`mesh_target.mesh_to_point_cloud`, reusing `datagen.sampling.sample_cloud` with an analytic
per-face normal, deterministic given an explicit `rng`). Seeded RANSAC via
`registration_ransac_based_on_feature_matching`; Open3D 0.19 has no RNG-object parameter for
this call, so the only seed hook is the process-global `o3d.utility.random.seed(seed)`,
called explicitly with the caller-supplied seed immediately before use — a documented,
narrow deviation from Constitution Art. I.3's "no hidden global RNG state," not a silent one.
A result with `fitness < min_fitness` or `< 3` correspondences raises
`RansacNoConsensusError` (NFR-2.3).

---

## 5. Baseline B (FR-2.8–2.12) — the plane-based pipeline

1. **Cloud planes** (`planes.extract_cloud_planes`): iterative single-plane RANSAC
   (`PointCloud.segment_plane` — Open3D 0.19 has no multi-plane API) + inlier removal,
   repeated until remaining points fall below `min_support_points` or `max_planes` planes are
   found.
2. **Model planes** (`planes.model_planes_from_mesh`): cluster mesh faces sharing a
   (normal-direction, plane-offset) key within tight tolerances (`coplanarity_angle_deg`≈1°,
   `coplanarity_dist_m`≈1mm — appropriate for an exact synthetic/BIM mesh). Recovers each
   original element as one `Plane(normal, centroid, area, face_count)`.
3. **Matching** (`planes.match_planes`): the grid's registration-error axis is a *residual*
   error (≤4° rotation, ≤100mm translation on a 5–12m scene), so cloud- and model-plane
   centroids are already close under an identity-ish alignment. Cost = normal-angle +
   weighted centroid-distance + weighted area-mismatch; solved as a linear assignment problem
   (`scipy.optimize.linear_sum_assignment`) — this is the concrete, documented
   interpretation of FR-2.10's "adjacency" criterion (spatial proximity under a bounded-offset
   assumption, not a literal adjacency graph). Requires ≥3 matches whose model normals have
   SVD rank 3 (`min_normal_rank_singular_value`), else `InsufficientPlaneMatchesError`. Since
   a RANSAC-fitted plane's normal sign is arbitrary, matching costs use `abs(cos angle)`, and
   the closed-form solver flips each matched cloud normal to agree in sign with its model
   normal before the rotation solve.
4. **Closed-form transform** (`planes.solve_rigid_from_planes`): rotation via Kabsch/SVD on
   the matched (sign-aligned) normal pairs (`R = argmin sum||R n_cloud - n_model||^2`);
   translation via least-squares over the matched planes' offset equations
   (`n_model . (R p_cloud + t) = n_model . p_model`).
5. **`B_seeded` fallback** (FR-2.12/R1): same closed-form solver, fed 2–3 correspondences
   supplied by the caller (`{"cloud_plane_id", "model_plane_id"}` pairs) instead of
   `match_planes`'s output — bypasses automatic matching only, not the transform math.

---

## 6. Fine registration (shared, FR-2.13–2.14) — the fairness mechanism

`refine_icp(cloud', mesh_sample, T_coarse, params)`: point-to-plane `registration_icp` from
`T_coarse`. `register()` extracts `icp_params = params["icp"]` **once**, before branching on
`method`, and both branches converge on a **single** call to `refine_icp(..., icp_params)`
after the branch — neither `coarse_register_A` nor `coarse_register_B` is permitted to call
`refine_icp` itself. Two consequences, both directly testable:
- the object reaching `refine_icp` has the same `id()` regardless of `method`
  (`tests/test_registration_fairness.py`);
- there is only one call site after coarse registration, so "diff the two code paths"
  (NFR-2.1) is true by inspection, not by convention.

A result with `fitness < min_fitness` raises `ICPDivergenceError`.

---

## 7. Metrics & orchestration (FR-2.15–2.18)

`metrics.registration_error(T_est, T_gt, ref_points_m=None)` — geodesic SO(3) angle in
degrees, translation norm in mm (both against `inverse(T_gt)`, §2.1), and an alignment RMSE
comparing where `T_est` vs. `inverse(T_gt)` place the shared mesh-sampled reference points
(`ref_points_m` defaults to a small canonical set so the SRS's 2-positional-argument call
still works standalone).

`api.register(cloud, mesh, method, params) -> T_est, metrics`: preprocess once → build the
shared mesh-sample target → branch on `method` for coarse registration → one shared
`refine_icp` call → optional `registration_error` if `params["T_gt"]` was supplied →
`{schema_version, method, status, T_est, coarse, icp, error_vs_gt, runtime_total_s}`.
Wrapped in `try/except RegistrationStageError` (→ structured `RegistrationFailure`) and a
final catch-all `except Exception` (→ `reason="unexpected_exception"`), so a `register()` call
never raises out to a grid run (NFR-2.3).

---

## 8. Failure representation (NFR-2.3)

`failures.RegistrationStageError` subclasses (`RansacNoConsensusError`,
`InsufficientPlaneMatchesError`, `ICPDivergenceError`) are raised by the stage that detects
the problem — Open3D's RANSAC/ICP calls never raise on their own (they return a
low-fitness `RegistrationResult`), so each stage explicitly checks `result.fitness` /
correspondence counts against a `min_fitness`/`min_correspondences` threshold in the frozen
params and raises. `register()` is the single catch site, converting any
`RegistrationStageError` (or unexpected exception) into a `RegistrationFailure(stage, reason,
detail)` record folded into the returned `metrics` dict as `{"status": "failed", "failure":
{...}}`, `T_est = None` — an additive extension of schema v1 (§9), not a shape break.

---

## 9. `registration_metrics.json` schema v1 — failure-case extension

Success case matches SRS §5.2 verbatim, plus `"status": "ok"`. Failure case:

```jsonc
{
  "schema_version": 1, "method": "B", "status": "failed",
  "T_est": null, "coarse": null, "icp": null, "error_vs_gt": null,
  "failure": {"stage": "coarse_b", "reason": "insufficient_plane_matches",
              "detail": "only 2 plane matches (need >= 3)"},
  "runtime_total_s": 0.31
}
```

---

## 10. Frozen parameter table & calibration (Art. IV)

`configs/registration_params.yaml` is tuned once on the held-out calibration condition
already present in the frozen grid (`data/S1/rot1.0_trans25_noise3_moderate/seed0/` — no new
data generated) via `scripts/calibrate_registration_params.py`, a manual, non-test,
non-reported script (Art. I.2 permits manual steps for *tuning*, not for *reported results*).
Once frozen, this file is committed verbatim and the excluded condition documented at its top.

---

## 11. Test-first order (mirrors Phase 1 plan §6)

1. `preprocess.py` + `mesh_target.py` — smoke-checked manually, no dedicated gate test.
2. `icp.py` alone, hand-verified with `T_coarse = I` on the identity sample — both baselines
   depend on this being correct first (Art. II: build the shared/trusted piece before the
   methods that use it).
3. `coarse_a.py` + `api.py` method="A" path → `test_registration_identity.py` (A half) green.
4. `planes.py` — sanity-checked in isolation on S1 before wiring into ICP.
5. `coarse_b.py` + `api.py` method="B"/"B_seeded" path → `test_registration_identity.py`
   (B half) green.
6. `metrics.py::registration_error` — unit-checked against hand-computed cases.
7. `test_registration_fairness.py` — passes given `api.py`'s structure; confirms the
   architecture rather than driving new code.
8. `test_registration_recovery.py` over the `noise1_none` slice — the real gate; iterate on
   `configs/registration_params.yaml` here if needed (still only via the calibration
   condition, per Art. IV.3).
9. `test_registration_failure.py` — S2 heavy-occlusion degenerate case.
10. Freeze `configs/registration_params.yaml` for real (commit).
11. `run_batch.py` + `scripts/render_phase2_figure.py` — demonstrable artifact, last.

These four tests are the Phase 2 gate (SRS §7 items 1–4) and are written alongside the code
that makes each one pass, not after.

---

## 12. Dependencies added this phase

None beyond the Art. VI stack already installed. `scipy.optimize.linear_sum_assignment` (plane
matching) and everything Open3D-side (`compute_fpfh_feature`,
`registration_ransac_based_on_feature_matching`, `segment_plane`, `registration_icp`,
`remove_statistical_outlier`, `orient_normals_consistent_tangent_plane`) were verified present
in the installed Open3D 0.19.0 before this plan was written.
