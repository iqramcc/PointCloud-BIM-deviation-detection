# Tasks — Phase 2: Registration Pipelines

Ordered, checkable. Implements the plan in `specs/plan/phase-2-registration.md`.
Check off in commits, not in this file's prose — keep `[ ]`/`[x]` as the only edits.

## Scaffold
- [x] `src/registration/__init__.py` package skeleton.
- [ ] `results/` output directory convention (parallel to `data/`, `reports/`) — not
      committed until it has real content.

## Shared preprocessing & target (FR-2.1–2.4)
- [x] `failures.py`: `RegistrationStageError` hierarchy + `RegistrationFailure` dataclass.
- [x] `preprocess.py::preprocess` — voxel downsample, SOR, oriented normal estimation.
- [x] `mesh_target.py::mesh_to_point_cloud` — reuses `datagen.sampling.sample_cloud` for a
      deterministic, analytically-normalled target cloud.

## Fine registration first (Art. II — shared piece before either method)
- [x] `icp.py::refine_icp` — point-to-plane ICP; hand-verified with `T_coarse = I` on the
      identity sample before either baseline is wired to it.

## Baseline A (FR-2.5–2.7)
- [x] `coarse_a.py::coarse_register_A` — FPFH features, seeded RANSAC
      (`o3d.utility.random.seed`, documented Art. I.3 deviation), fitness/correspondence
      check -> `RansacNoConsensusError`.
- [x] `api.py::register` method="A" path wired through preprocess -> coarse_a -> icp.
- [x] `tests/test_registration_identity.py` (A half): clean sample, `T_gt=I` ->
      `rot_deg<0.05`, `trans_mm<1.0`.

## Baseline B (FR-2.8–2.12)
- [x] `planes.py`: `Plane`, `PlaneMatch` dataclasses.
- [x] `planes.py::extract_cloud_planes` — iterative `segment_plane` + inlier removal.
- [x] `planes.py::model_planes_from_mesh` — cluster mesh faces by (normal, offset); recovers
      elements without depending on `ground_truth.json` or the scene YAML.
- [x] `planes.py::match_planes` — normal-angle + centroid-distance + area cost, solved via
      `scipy.optimize.linear_sum_assignment`; rejects < 3 / rank-deficient matches.
- [x] `planes.py::solve_rigid_from_planes` — sign-aligns matched normals, then Kabsch/SVD
      rotation, least-squares translation from plane-offset equations.
- [x] `coarse_b.py::coarse_register_B` — auto-match path + `B_seeded` path (FR-2.12) sharing
      the same closed-form solver.
- [x] `api.py::register` method="B"/"B_seeded" path wired through preprocess -> coarse_b ->
      icp (same `refine_icp` call site as A).
- [x] `tests/test_registration_identity.py` (B half).

## Metrics & orchestration (FR-2.15–2.18)
- [x] `metrics.py::registration_error` — geodesic SO(3) angle, translation norm, mesh-sampled
      alignment RMSE.
- [x] `api.py::register` — `params["T_gt"]` optional hook, `error_vs_gt` population, runtime
      timing per stage, structured failure catch (`RegistrationStageError` + catch-all).
- [x] `params.py::load_params`, `params_hash` (sha256 of canonical JSON, mirrors
      `groundtruth.py`'s style).
- [x] `io.py`: `registration_metrics.json` schema v1 writer/reader, including the additive
      failure-case shape (plan §9).

## Fairness (NFR-2.1 / gate item 3)
- [x] `tests/test_registration_fairness.py`: `refine_icp` receives the identical `id()` object
      for both `method="A"` and `method="B"` calls; `refine_icp` called exactly once per
      `register()` call.

## Failure handling (NFR-2.3 / gate item 4)
- [x] `tests/test_registration_failure.py`: S2, heavy occlusion, constructed via
      `datagen.build_dataset.make_sample` (same pattern as `test_roundtrip.py`) -> structured
      `RegistrationFailure`, `T_est is None`, no exception escapes `register()`.

## Recovery test (gate item 2 — noise=1mm documented interpretation)
- [x] `tests/test_registration_recovery.py`: `data/S1/rot*_trans*_noise1_none/seed{0,1}` (50
      samples, >= 20 required) for both A and B; median `rot_deg<0.2`, `trans_mm<5.0`.
      Docstring states the noise=1mm-as-clean interpretation explicitly (no grid/decision-log
      change). Marked `@pytest.mark.slow`.

## Calibration & frozen params (Art. IV / gate item 5)
- [x] `scripts/calibrate_registration_params.py` — manual, non-test helper against the
      existing `data/S1/rot1.0_trans25_noise3_moderate/seed0/` sample.
- [ ] `configs/registration_params.yaml` frozen values confirmed against the test suite
      results (§ Gate below) and committed; calibration condition documented at the top of
      the file.

## Demonstrable artifact (gate item 6)
- [x] `src/registration/run_batch.py` — CLI: manifest slice x method -> per-sample
      `registration_metrics.json` + `summary.csv`.
- [x] `scripts/render_phase2_figure.py` — error/runtime table (A vs B, clean registration-error
      axis, S1) + one before/after alignment render per method.
- [x] `reports/tables/phase2_registration_errors.csv`, `reports/figures/phase2_alignment_A.png`,
      `reports/figures/phase2_alignment_B.png` generated (25 samples/method, S1
      `noise1_none/seed0` slice). Median rot/trans error: **A = 179.996 deg / 5820.9mm**
      (21/25 "ok"-but-wrong, 4/25 caught `RansacNoConsensusError`), **B = 0.0026 deg /
      0.230mm** (25/25 ok) — the table itself is the clearest statement of the calibration
      finding above.

## Gate (Phase 2 SRS §7 / roadmap Weeks 3–4)
- [x] `test_registration_fairness`, `test_registration_failure` — pass, deterministically.
- [x] `test_registration_identity`/`test_registration_recovery`, **Baseline B half** — pass.
      Recovery test measured (50 samples): median well inside bounds.
- [ ] `test_registration_identity`/`test_registration_recovery`, **Baseline A half** — do
      NOT reliably pass; see the calibration finding below. Recovery test measured (50
      samples, real run 2026-09-16): median rot_deg well under 0.2, but median
      **trans_mm = 428.1mm** (bound: <5.0mm) — driven by a subset of samples converging to
      a wrong symmetric optimum with 1-8m translation error. All samples returned
      `status: "ok"` (no crashes — NFR-2.3 holds; the failures are wrong-but-confident
      results, not caught errors) — Identity test flakiness independently confirmed: 1/5
      manual re-runs passed, 4/5 failed, for the same single sample and seed (also flags
      FR-2.18 "deterministic given seed" as not fully true for Open3D's RANSAC).
- [x] Frozen `configs/registration_params.yaml` committed — calibrated defaults documented
      inline, including the Baseline A finding.
- [ ] Demonstrable artifact reviewed by owner.
- [ ] Owner approves proceeding to Phase 3 (which can start in parallel per the roadmap's
      Week 4 overlap, against a perfectly-aligned cloud) **and** rules on the Baseline A
      finding below.

## Deferred / documented gaps (not silent)
- [ ] `B_seeded`'s correspondences are supplied ad hoc per call today (no config-driven
      per-sample seed file) — sufficient for the R1 fallback and the failure test, but if
      `B_seeded` becomes the *reported* Baseline B (R1 triggers for real), a small
      `configs/b_seeded_correspondences.yaml` keyed by sample_id should be added — not done
      unless R1 actually triggers.

## CALIBRATION FINDING — Baseline A is unreliable on scene S1 (owner decision needed)

During calibration (`scripts/calibrate_registration_params.py` iteration, see
`configs/registration_params.yaml`'s header comment on `ransac_a`), Baseline A
(FPFH+RANSAC) was found to **not** reliably converge to the correct global optimum on
scene S1, at any parameter combination tried (FPFH radius in {0.15, 0.5, 0.75, 0.8, 1.0,
1.2} m, `ransac_n` in {3, 4}, with/without `CorrespondenceCheckerBasedOnDistance` /
`CorrespondenceCheckerBasedOnNormal`, `edge_length_similarity` in {0.7-0.9}, up to 100000
RANSAC iterations). Root cause, verified by hand: S1's walls are large, flat, and locally
self-similar (zero curvature away from corners), so FPFH descriptors carry almost no
distinguishing signal over most of the cloud; mutual-nearest-neighbour feature matching
finds only a handful of correspondences (2-16, out of ~9000 points) at this project's
frozen 100 pts/m^2 density (`configs/grid.yaml`, cut from 2500 in Phase 1 for the compute
budget — see `specs/tasks/phase-1-synthetic-data.md`). RANSAC then converges to a
plausible-but-wrong symmetric alignment (commonly a ~180 deg flip, once ~9 deg/832mm,
once ~14-22 deg/1.0-1.3m) about as often as the correct one — confirmed **not** a code
defect: an idealized noise-free, densely-resampled test of the same scene recovers the
identity transform to 0.13mm via the identical code path, and `registration_error`'s math
is independently unit-tested (`tests/test_registration_metrics_math.py`).
Consequence: `tests/test_registration_identity.py::test_baseline_a_...` and
`tests/test_registration_recovery.py::test_baseline_a_...` are **flaky** — they pass when
RANSAC happens to land near the correct optimum and fail when it lands on a symmetric
false one (Open3D's RANSAC is not fully deterministic under `o3d.utility.random.seed`
either, likely due to internal OpenMP parallelism — a second finding against FR-2.18).
This is a genuine, literature-consistent baseline-vs-scene limitation (FPFH needs local
curvature to discriminate; an empty rectangular room has almost none), not something
further parameter tuning is expected to fix.
- [ ] **Owner decision needed** on how to treat this for the report/gate — options noted,
      not chosen unilaterally: (a) report it as a finding (Baseline A's fragility on
      symmetric architecture vs. Baseline B's robustness *is* a result, and arguably
      supports the project's own Insight I2); (b) add a small amount of non-planar detail
      to S1 (e.g. a furniture proxy) so FPFH has curvature to key on, if a fair A-vs-B
      comparison requires both to have a real chance of converging; (c) raise the frozen
      point density back up for future runs, since the mutual-match starvation is partly a
      density artifact. Not resolved here — flagged in the same turn it was found.
