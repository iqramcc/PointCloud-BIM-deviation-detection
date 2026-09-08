# SRS — Phase 2: Registration Pipelines

**Status:** Draft v0.1 · **Time-box:** Weeks 3–4 (2026-09-22 – 2026-10-05) · **Gate:** both
baselines recover known transforms on clean data within stated bounds; a frozen parameter
table exists.

Governed by `specs/constitution.md` (esp. Art. IV — fair comparison). Cites
`literature-review.md` §2, Insight I2.

---

## 1. Introduction

### 1.1 Purpose
Build the `registration` module: preprocess an as-built cloud, then align it to the
as-designed geometry using **two interchangeable coarse strategies** sharing one fine-
refinement stage, and report standardised registration-error metrics.

### 1.2 Phase context
Third phase. Depends on Phase 1 outputs (`cloud.ply`, `scene_mesh.ply`, `ground_truth.json`
for evaluation only — the transform is *not* revealed to the registration code).

### 1.3 Definitions
- **Baseline A (point-based)** — FPFH feature + RANSAC global registration → point-to-plane
  ICP. Reference: Rusu et al. 2009; Open3D global-registration tutorial.
- **Baseline B (plane-based)** — plane segmentation on cloud and model, plane
  correspondence, closed-form transform from matched planes → point-to-plane ICP. Reference:
  Bosché; Bueno et al. 2018 (4-plane congruent sets).
- **Residual registration error** — the difference between the estimated transform and
  `T_gt` after the full coarse+fine pipeline; the independent variable for Phase 4.

---

## 2. Research context

- Both baselines are established; the project implements neither's *concept* from scratch.
- Baseline B's **plane matcher** is the only substantial custom component; a semi-automatic
  seeded variant is a documented precedent (Bosché) and the R1 fallback.
- Insight I2: plane-based registration constrains normal-direction DOF tightly and in-plane
  DOF loosely; this is expected to matter for downstream deviation detection and is the
  falsifiable core of the RQ.

---

## 3. Overall description

- **Inputs:** `cloud.ply`, `scene_mesh.ply` (+ optionally planes extracted from the mesh),
  a frozen parameter set.
- **Outputs per run:** `T_est` (4×4), `registration_metrics.json` (schema §5.2), optional
  alignment render.
- **Consumers:** `deviation` (Phase 3) applies `T_est` to the cloud; `experiment` (Phase 4)
  reads `registration_metrics.json` and computes residual error against `T_gt`.
- **Constraint:** identical preprocessing, ICP code, ICP parameters, and evaluation for both
  baselines (Constitution Art. IV).

---

## 4. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| **Preprocessing (shared)** | | |
| FR-2.1 | Voxel downsampling with configurable voxel size. | M |
| FR-2.2 | Statistical outlier removal (configurable neighbours / std ratio). | M |
| FR-2.3 | Normal estimation (configurable radius / k), consistently oriented. | M |
| FR-2.4 | Preprocessing is applied identically before both baselines and logged. | M |
| **Baseline A** | | |
| FR-2.5 | Compute FPFH features on the downsampled cloud and on a point sampling of the mesh. | M |
| FR-2.6 | RANSAC global registration (feature matching) with configurable, seeded budget; return a coarse transform. | M |
| FR-2.7 | Report RANSAC fitness and inlier RMSE. | S |
| **Baseline B** | | |
| FR-2.8 | Segment planes from the cloud (RANSAC plane fitting + clustering, or region growing); return planes with normal, centroid, extent, support count. | M |
| FR-2.9 | Obtain planes from the as-designed mesh (per-element; already labelled from Phase 1). | M |
| FR-2.10 | Match cloud planes to model planes by normal similarity, area, and adjacency; produce ≥ 3 non-degenerate correspondences (spanning 3 independent normal directions where the scene allows). | M |
| FR-2.11 | Estimate the rigid transform in closed form from matched planes (rotation from normal pairs, translation from plane offsets, least-squares). | M |
| FR-2.12 | Semi-automatic mode: accept 2–3 user-seeded plane correspondences from config, then solve as FR-2.11 (R1 fallback). | M |
| **Fine registration (shared)** | | |
| FR-2.13 | Point-to-plane ICP refinement from the coarse transform, configurable max-distance schedule and iteration cap; same implementation and parameters for A and B. | M |
| FR-2.14 | Return final `T_est`, ICP fitness, and inlier RMSE. | M |
| **Metrics & orchestration** | | |
| FR-2.15 | Given `T_est` and `T_gt`, compute rotation error (geodesic angle on SO(3), degrees), translation error (‖·‖, mm), and an alignment RMSE on mesh-sampled correspondences. | M |
| FR-2.16 | A single entry point `register(cloud, mesh, method, params) -> T_est, metrics` with `method ∈ {A, B, B_seeded}`. | M |
| FR-2.17 | Measure and record wall-clock runtime per stage. | M |
| FR-2.18 | Deterministic given seed and params. | M |

---

## 5. Data & interface requirements

### 5.1 Module interface
- `preprocess(cloud, params) -> cloud'`
- `coarse_register_A(cloud', mesh_sample, params) -> T_coarse, info`
- `coarse_register_B(cloud', model_planes, params, seeds=None) -> T_coarse, info`
- `refine_icp(cloud', mesh, T_coarse, params) -> T_est, info`
- `register(cloud, mesh, method, params) -> T_est, metrics`
- `registration_error(T_est, T_gt) -> {rot_deg, trans_mm, rmse_mm}`

### 5.2 `registration_metrics.json` schema (v1)

```jsonc
{
  "schema_version": 1,
  "sample_id": "S1/rot1.0_trans25_noise3_moderate/seed42",
  "method": "B",
  "params_hash": "sha256:...",
  "T_est": [[...4x4...]],
  "coarse": { "fitness": 0.71, "inlier_rmse_mm": 6.2, "runtime_s": 0.4,
              "n_plane_matches": 4 },
  "icp":    { "fitness": 0.93, "inlier_rmse_mm": 2.1, "runtime_s": 0.2 },
  "error_vs_gt": { "rot_deg": 0.18, "trans_mm": 3.4, "rmse_mm": 2.0 },
  "runtime_total_s": 0.7
}
```

### 5.3 Parameter table (Constitution Art. IV)
A `configs/registration_params.yaml`, tuned **once** on a held-out calibration condition
(e.g. S1, rot 1°, trans 25 mm, noise 3 mm, moderate occlusion, seed 0 — *excluded from all
reported results*), then frozen. Published verbatim in the final report.

---

## 6. Non-functional requirements

- **NFR-2.1 Fairness:** a diff of the two baseline code paths shows identical preprocessing
  and identical ICP calls/params.
- **NFR-2.2 Performance:** a single `register()` call completes in ≤ 10 s on a laptop CPU
  for the default cloud size.
- **NFR-2.3 Robustness logging:** failures (RANSAC no-consensus, < 3 plane matches, ICP
  divergence) are caught and recorded as a structured failure, not an exception that aborts
  a grid run.
- **NFR-2.4 Independence:** `registration` imports nothing from `deviation` / `experiment`;
  it reads `T_gt` only through the evaluation helper, never inside the estimator.

---

## 7. Acceptance criteria & verification

Phase 2 is **done** when:

1. **Identity test:** on a clean sample with `T_gt = I`, both baselines return `rot_deg <
   0.05`, `trans_mm < 1.0` — *automated test*.
2. **Recovery test:** on clean samples across the grid's registration-error axis (no noise,
   no occlusion), both baselines recover `T_gt` with median `rot_deg < 0.2`, `trans_mm <
   5.0` — *automated test over ≥ 20 samples*.
3. **Fairness check:** NFR-2.1 confirmed by inspection + a test asserting the ICP parameter
   object is the same instance for both paths — *automated test*.
4. **Failure handling:** a deliberately unsolvable case (S2 with < 3 usable planes, heavy
   occlusion) yields a recorded failure, not a crash — *automated test*.
5. Frozen `configs/registration_params.yaml` committed; calibration condition documented and
   excluded from result sets.
6. Demonstrable artifact: a table of rotation/translation error + runtime for A and B across
   the clean registration-error axis on S1, plus one before/after alignment render per
   method.

---

## 8. Risks & fallback

| Risk | Fallback |
|---|---|
| Automatic plane matcher (FR-2.10) unreliable within the time-box (R1) | Ship `B_seeded` (FR-2.12) as the reported Baseline B; note automatic matching as future work. |
| RANSAC (Baseline A) unstable on partial mesh sampling | Increase correspondence set / iterations within the frozen budget; document; if still unstable, report A's failure rate as a finding. |
| ICP dominates and erases coarse-method differences on easy cells | Expected and interesting — the coarse-method difference should appear on hard cells (high injected error, heavy occlusion); ensure the grid reaches that regime. |

---

## 9. Out of scope for Phase 2

- Learned features / learned registration (Constitution Art. III).
- Non-rigid registration.
- Deviation computation (Phase 3).
- Multi-scan registration / loop closure (single as-built cloud per sample).
