# SRS — Phase 3: Deviation Detection Module

**Status:** Draft v0.1 · **Time-box:** Week 4, overlapping Phase 2b (2026-09-29 – 2026-10-05)
· **Gate:** module validated against a perfectly aligned cloud with known displaced elements;
detection metrics match ground truth.

Governed by `specs/constitution.md` (esp. Art. II). Cites `literature-review.md` §3, Insight
I4.

---

## 1. Introduction

### 1.1 Purpose
Build the `deviation` module: given an aligned as-built cloud and the as-designed geometry,
compute signed geometric deviations, aggregate them per BIM element, flag elements outside
construction tolerance, produce a heatmap, and score the flags against ground truth.

### 1.2 Phase context
Fourth phase, deliberately overlapped with Phase 2b: it can be built and validated on a
*perfectly aligned* cloud (`inverse(T_gt)` applied) while the plane-based baseline is being
finished. This isolates deviation-module correctness from registration quality.

### 1.3 Definitions
- **Signed distance** — point-to-mesh distance, positive outside the surface (along the
  outward normal), negative inside.
- **Per-element aggregate** — a single deviation value per BIM element (default: signed
  median normal offset — decision D3 / Insight I4).
- **Out-of-tolerance flag** — element aggregate magnitude > τ.
- **Detection metrics** — precision / recall / F1 of the flag set vs
  `ground_truth.elements[*].is_out_of_tolerance`.

---

## 2. Research context

- Anil et al. 2013 — the standard pipeline: align → point-to-surface distance → per-element
  classification → color-coded map; and the source of the confound this project measures.
- Lague et al. 2013 (M3C2) — robust distance alternative if surfaces are noisy (D2).
- Insight I4 — a signed median normal offset should be more robust to residual registration
  error than a max/percentile point distance; both are implemented so Phase 4 can compare.

---

## 3. Overall description

- **Inputs:** aligned `cloud'` (cloud after `T_est` or, for validation, after `inverse(T_gt)`),
  `scene_mesh.ply` with per-element face groups, `tolerance_mm`, the per-element metadata.
- **Outputs:** `deviation_result.json` (schema §5.2), `heatmap.png` (or `.ply` with scalar
  field), a per-element table (`.csv`).
- **Consumers:** `experiment` (Phase 4) reads `deviation_result.json` and joins it with
  `registration_metrics.json` and `ground_truth.json`.

---

## 4. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | Compute signed point-to-mesh distance for every cloud point (sign from the nearest face's outward normal). | M |
| FR-3.2 | Assign each cloud point to a BIM element by nearest face / face group. | M |
| FR-3.3 | Per-element aggregate = signed **median** normal offset (primary). | M |
| FR-3.4 | Alternative aggregates available and selectable: signed mean, 95th-percentile absolute distance, max absolute distance (for the Phase 4 ablation, Insight I4). | S |
| FR-3.5 | Flag an element out of tolerance when \|aggregate\| > τ; τ from config (decision D4). | M |
| FR-3.6 | Report, per element: point count, aggregate value, flag, and coverage (fraction of element area with points — low coverage ⇒ low-confidence flag). | M |
| FR-3.7 | Produce a deviation **heatmap**: cloud (or mesh) colour-mapped by signed distance, diverging colormap centred at 0, symmetric limits, colorbar in mm. | M |
| FR-3.8 | Compute detection metrics (precision, recall, F1, confusion counts) against ground-truth labels; also per deviation *type* (normal offset vs tilt vs in-plane). | M |
| FR-3.9 | Optionally exclude low-coverage elements from scoring (configurable threshold) and report how many were excluded. | S |
| FR-3.10 | Deterministic; no manual steps. | M |
| FR-3.11 | M3C2-style distance as an alternative to plain C2M, off by default (D2). | C |

---

## 5. Data & interface requirements

### 5.1 Module interface
- `signed_distance(cloud, mesh) -> per_point_distance, per_point_element_id`
- `aggregate_per_element(distances, element_ids, method) -> {element_id: {value, n, coverage}}`
- `flag(aggregates, tolerance_mm) -> {element_id: bool}`
- `score(flags, ground_truth) -> {precision, recall, f1, tp, fp, fn, tn, by_type}`
- `heatmap(cloud, distances, out_path)`

### 5.2 `deviation_result.json` schema (v1)

```jsonc
{
  "schema_version": 1,
  "sample_id": "S1/rot1.0_trans25_noise3_moderate/seed42",
  "alignment_source": "T_est:B",          // or "T_gt_inverse" for validation
  "tolerance_mm": 10.0,
  "aggregate_method": "signed_median_normal_offset",
  "elements": [
    { "id": 3, "class": "wall", "n_points": 5120, "coverage": 0.88,
      "aggregate_mm": 12.7, "flagged": true, "gt_out_of_tolerance": true }
  ],
  "metrics": { "precision": 0.86, "recall": 0.92, "f1": 0.89,
               "tp": 11, "fp": 2, "fn": 1, "tn": 40,
               "by_type": { "normal_offset": {"f1": 0.94}, "tilt": {"f1": 0.7} } },
  "excluded_low_coverage": 1
}
```

---

## 6. Non-functional requirements

- **NFR-3.1 Correctness first:** validated on perfect alignment before use with `T_est`.
- **NFR-3.2 Performance:** full deviation computation for one sample ≤ 5 s on a laptop CPU.
- **NFR-3.3 Determinism / no manual steps** (Constitution Art. I).
- **NFR-3.4 Independence:** `deviation` imports nothing from `registration` / `experiment`;
  it receives an already-aligned cloud.
- **NFR-3.5 Visual standard:** heatmaps follow a fixed, colour-vision-safe diverging palette
  and consistent scale across figures in a set.

---

## 7. Acceptance criteria & verification

Phase 3 is **done** when:

1. **Perfect-alignment ceiling:** with the cloud aligned by `inverse(T_gt)` and no noise,
   detection F1 = 1.0 on a sample with known displaced elements — *automated test*.
2. **Noise robustness:** with perfect alignment and noise σ = 5 mm, τ = 10 mm, F1 ≥ 0.9 and
   no systematic bias in within-tolerance elements — *automated test*.
3. **Sign correctness:** an element pushed *outward* by 15 mm yields a positive aggregate; a
   *recessed* element yields negative — *automated test*.
4. **Coverage behaviour:** an element with < 20 % coverage is marked low-confidence /
   optionally excluded, and this is reported — *automated test*.
5. **Metric correctness:** `score()` reproduces hand-computed precision/recall on a 5-element
   toy case — *automated test*.
6. Demonstrable artifact: a heatmap of a deviated scene + its per-element table + a
   precision/recall/F1 line, all from perfectly aligned input (the detection ceiling).

---

## 8. Risks & fallback

| Risk | Fallback |
|---|---|
| Point-to-mesh distance slow (large cloud, many faces) | Use a KD-tree / BVH (trimesh `proximity`, Open3D raycasting scene); downsample cloud for deviation as a last resort, documented. |
| Point-to-element assignment ambiguous at element joints | Assign by nearest face with a small margin band; exclude a thin seam region from aggregates; document. |
| Tilt/rotation deviations poorly captured by a single scalar aggregate | Report per-type metrics (FR-3.8); a tilt-aware aggregate (offset gradient across the element) is a stretch item, not required. |

---

## 9. Out of scope for Phase 3

- Registration (Phase 3 always receives an aligned cloud).
- Surface-quality / flatness / crack detection beyond a single per-element deviation scalar.
- Defect *classification* into construction causes.
- Automatic tolerance selection (τ is configured, sensitivity tested in Phase 4).
