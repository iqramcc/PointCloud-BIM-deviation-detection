# SRS — Phase 4: Experiment Harness & Coupling Analysis

**Status:** Draft v0.1 · **Time-box:** Weeks 5–6 (2026-10-06 – 2026-10-19) · **Gate:** the
core result — deviation-detection performance as a function of residual registration error,
per baseline, per scene — is produced with confidence intervals from one command.

Governed by `specs/constitution.md` (esp. Art. I, IV, V). Cites `literature-review.md` §4/§6,
Insights I1–I4. **This phase produces the project's contribution.**

---

## 1. Introduction

### 1.1 Purpose
Build the `experiment` module: run the frozen grid over both baselines and both scenes,
join registration metrics with deviation metrics and ground truth, and quantify the
**coupling** between registration error and deviation-detection reliability — including the
spatial pattern of false flags and the practical "registration budget".

### 1.2 Phase context
Fifth phase. Consumes files from Phases 1–3 only. No new geometry or estimation methods.

### 1.3 Hypotheses (recorded before the full run — Constitution Art. V)
- **H1** Deviation-detection F1 decreases monotonically as residual registration error
  grows, on both baselines.
- **H2** For a fixed residual *alignment RMSE*, Baseline B yields higher F1 on
  normal-offset deviations than Baseline A (Insight I2).
- **H3** Residual *rotational* error produces false positives concentrated far from the
  alignment centroid; residual *translational* error produces spatially uniform,
  sign-consistent bias (Insight I1).
- **H4** The signed-median-normal-offset aggregate is more robust to residual registration
  error than the 95th-percentile point-distance aggregate (Insight I4).
- **H5** There exists a residual-error threshold (the "registration budget") below which
  F1 ≥ 0.9 for a given τ; it differs between baselines and scenes (Insight I3).

A null result on any hypothesis is reported as found.

---

## 2. Research context

- Monte Carlo registration evaluation (Measurement 2016) — precedent for
  simulation-based error propagation; this phase extends it to *downstream detection*.
- Anil et al. 2013 — the confound this phase quantifies for the first time.
- The gap (`literature-review.md` §6, items 2–4) is closed by the outputs below.

---

## 3. Overall description

- **Inputs:** `data/*/manifest.csv` (Phase 1), and the ability to invoke `registration` and
  `deviation` per sample.
- **Outputs:** `results/runs.parquet` (one row per sample × method), `results/summary/*.csv`
  (aggregated), `results/figures/*` (the result plots), `results/coupling_report.md`
  (auto-generated narrative of findings vs H1–H5).
- **Consumers:** Phase 5 (report / deck).

---

## 4. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | A runner that iterates `manifest.csv` × `{A, B}` (and `B_seeded` if that is the reported B), calls `register` then `deviation`, and writes one result row per combination. | M |
| FR-4.2 | Each row records: grid coordinates, seed, scene, method, residual registration error (`rot_deg`, `trans_mm`, `rmse_mm`), detection metrics (precision/recall/F1, per-type), aggregate method, runtimes, and any failure flag. | M |
| FR-4.3 | Resumable: re-running skips completed rows (keyed by sample_id + method + params_hash). | M |
| FR-4.4 | Trivially parallelisable across samples (process pool); deterministic regardless of worker count. | M |
| FR-4.5 | **Coupling curves:** F1 (and precision, recall) vs residual `rmse_mm`, and vs residual `rot_deg` and `trans_mm` separately; one line per method; ribbons = 95 % CI across seeds; faceted by scene. | M |
| FR-4.6 | **Aggregate ablation:** recompute detection metrics for each alternative aggregate (FR-3.4) and overlay coupling curves (tests H4). | S |
| FR-4.7 | **Spatial analysis:** for a representative high-error cell, map false-positive / false-negative rate vs distance from the alignment centroid, split by residual error type (tests H3). | M |
| FR-4.8 | **Registration budget:** for each (scene, method, τ), the maximum residual `rmse_mm` at which mean F1 ≥ 0.9 (and a sensitivity sweep over τ ∈ {5, 10, 15} mm). Output as a small table + bar chart (tests H5). | M |
| FR-4.9 | **Noise / occlusion effect:** coupling curves faceted by noise σ and by occlusion level, to separate their contribution from registration error. | S |
| FR-4.10 | Auto-generate `coupling_report.md`: for each hypothesis, the relevant statistic, the figure reference, and a "supported / partially / not supported" verdict with numbers. | M |
| FR-4.11 | A one-command entry point: `python -m experiment.run --config configs/grid.yaml --all`. | M |
| FR-4.12 | Record environment: library versions, CPU, OS, wall-clock total. | M |

---

## 5. Data & interface requirements

### 5.1 `results/runs.parquet` columns (v1)
`sample_id, scene, method, params_hash, seed, inj_rot_deg, inj_trans_mm, noise_sigma_mm,
occlusion, res_rot_deg, res_trans_mm, res_rmse_mm, agg_method, precision, recall, f1,
f1_normal_offset, f1_tilt, f1_inplane, tp, fp, fn, tn, n_elements, excluded_low_coverage,
reg_runtime_s, dev_runtime_s, failure`

### 5.2 Statistical treatment
- Central tendency across the 10 seeds per cell = mean; dispersion = 95 % CI (bootstrap or
  t-interval, stated).
- Monotonicity (H1) tested with Spearman ρ between `res_rmse_mm` and `f1`.
- H2 tested by comparing F1 at matched `res_rmse_mm` bins (paired by cell), Wilcoxon
  signed-rank; report effect size, not only p.
- No causal claims beyond the controlled injection design; limitations stated.

### 5.3 Figures (delivered)
1. Coupling curve: F1 vs residual RMSE, per method, faceted by scene. **(headline figure)**
2. Coupling curves vs residual rotation and translation separately.
3. Spatial FP/FN map for a high-error cell, per error type.
4. Registration-budget bar chart + τ-sensitivity.
5. Aggregate-ablation overlay.
6. Noise/occlusion facets.

---

## 6. Non-functional requirements

- **NFR-4.1 Reproducibility:** `experiment.run` from a clean checkout + `configs/` + seeds
  regenerates `runs.parquet` and every figure (Constitution Art. I).
- **NFR-4.2 Runtime:** full grid (both scenes, both methods, default 2 250 samples/scene)
  completes in ≤ 2 h on a 4-core laptop; reduced grid ≤ 40 min.
- **NFR-4.3 Honesty:** `coupling_report.md` verdicts are generated from the data, not
  hand-written; surprises are not smoothed.
- **NFR-4.4 Auditability:** every figure caption names the rows/filters that produced it.

---

## 7. Acceptance criteria & verification

Phase 4 is **done** when:

1. `python -m experiment.run --all` produces `runs.parquet` with the expected row count and
   `failure` rate below a stated threshold (e.g. < 5 %, higher only for the deliberately
   unsolvable S2 cells) — *verify by running*.
2. **Sanity:** the zero-injected-error rows reproduce the Phase 3 detection ceiling
   (F1 ≈ Phase 3 result) for both methods — *automated check*.
3. **Resumability:** killing the run mid-way and restarting completes without recomputation
   of finished rows and yields identical output — *automated test*.
4. All six figures render from `runs.parquet` via committed plotting scripts.
5. `coupling_report.md` exists with a data-derived verdict for each of H1–H5.
6. Demonstrable artifact: the headline coupling-curve figure + the registration-budget
   table, for at least one scene, with confidence intervals.

---

## 8. Risks & fallback

| Risk | Fallback |
|---|---|
| Full grid too slow for weekly budget (R2) | Reduced grid (Phase 1 §5.4 fallback); keep residual-error axis dense. |
| Both baselines collapse to identical curves (ICP dominates) | A finding in itself (report it); ensure the grid includes cells hard enough to separate coarse methods; if still identical, H2 is "not supported" and that is the result. |
| CI ribbons too wide to conclude anything (10 seeds insufficient) | Increase seeds only on the registration-error axis at fixed noise/occlusion; report power limitation. |
| Only one scene ready | Report single-scene coupling analysis; second scene → "future work" (R4). |

---

## 9. Out of scope for Phase 4

- New registration or deviation methods.
- Real-data quantitative analysis (synthetic only — Insight I5; real data is Phase 5
  qualitative).
- Hyperparameter search (parameters frozen in Phase 2 — Constitution Art. IV).
- Machine-learning models of the coupling (a fitted curve/threshold is descriptive only).
