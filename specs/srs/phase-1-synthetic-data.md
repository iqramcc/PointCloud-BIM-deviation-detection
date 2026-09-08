# SRS — Phase 1: Synthetic Data Generation Framework

**Status:** Draft v0.1 · **Time-box:** Week 2 (2026-09-15 – 2026-09-21) · **Gate:** one
command produces a fully labelled dataset; generator self-tests pass; experiment grid frozen.

Governed by `specs/constitution.md` (esp. Art. II — ground truth before methods). Cites
`literature-review.md` §5, Insights I1/I5.

---

## 1. Introduction

### 1.1 Purpose
Build the `datagen` module: given a parametric building scene, produce synthetic as-built
point clouds together with exact ground truth for (a) the rigid transform that misaligns the
scan from the BIM frame, (b) the sensor noise, (c) the occlusion, and (d) which BIM elements
are truly out of tolerance and by how much.

### 1.2 Phase context
Second phase; nothing about registration or deviation methods is touched. Per Constitution
Art. II this module and the Phase 4 metrics are built and validated before any baseline is
tuned.

### 1.3 Definitions
- **Scene** — a parametric as-designed model: a set of labelled planar elements (walls,
  slab, columns, one opening) with element IDs and surface normals.
- **As-designed mesh** — the ground-truth geometry (the "BIM").
- **As-built cloud** — points sampled from a *deviated* copy of the mesh, then perturbed.
- **Nominal deviation** — the intentional per-element displacement applied before sampling.
- **Registration perturbation** — the known rigid transform `T_gt` applied to the whole
  cloud; recovering its inverse is the registration task.

---

## 2. Research context

- Noichl et al. 2021 ("BIM-to-Scan") — precedent for realistic synthetic scan generation with
  exact ground truth.
- SynBench 2024 — precedent for parameterising noise / outliers / incompleteness.
- Buildings 13(6):1473 (2023) — realistic registration-error magnitudes to bound the grid.
- Insight I5 — synthetic data is the only setting where simultaneous ground truth for
  registration error and true deviations exists; this phase operationalises that.

---

## 3. Overall description

- **Inputs:** scene definitions (`configs/scenes/*.yaml`), a perturbation config
  (`configs/grid.yaml`), an integer seed.
- **Outputs per sample:** `cloud.ply` (as-built points, optionally with normals),
  `ground_truth.json` (schema §5.2), `scene_mesh.ply` (as-designed), `render.png` (optional
  QA visual).
- **Consumers:** `registration` (Phase 2) reads `cloud.ply` + `scene_mesh.ply`; `deviation`
  (Phase 3) reads `scene_mesh.ply` + per-element metadata; `experiment` (Phase 4) reads
  `ground_truth.json`.
- **Constraints:** runs on a laptop CPU; a full dataset (all grid cells × seeds) generates in
  minutes, not hours.

### 3.1 Two scenes (Art. III, R4)
- **S1 "well-conditioned"** — a room with walls at distinct orientations, a slab, columns;
  rich, unambiguous planar structure (favourable to plane-based registration).
- **S2 "ambiguous"** — a long corridor / repetitive bay: few distinct normal directions,
  translational sliding weakly constrained (stresses both baselines differently).

---

## 4. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | Generate a parametric as-designed scene from a YAML definition as a labelled triangle mesh; each element carries a stable integer ID, a semantic class, and an outward normal. | M |
| FR-1.2 | Provide ≥ 2 scenes (S1, S2 above). | M |
| FR-1.3 | Sample a point cloud from the mesh surface with controllable density (points/m²), approximately uniform over area. | M |
| FR-1.4 | Inject **nominal deviations**: for a chosen subset of elements apply a known transform (normal-direction offset, in-plane translation, small rotation/tilt) *before* sampling; record magnitude and type per element. | M |
| FR-1.5 | Apply a **registration perturbation** `T_gt` (rotation + translation) to the whole cloud, drawn from configured ranges; store `T_gt` and its inverse. | M |
| FR-1.6 | Add sensor **noise**: Gaussian along the local surface normal with configurable σ; optional small isotropic component; optional sparse outliers at a configurable rate. | M |
| FR-1.7 | Simulate **occlusion** by virtual-scanner visibility: place one or more scanner origins, keep only points with line-of-sight (ray/`hidden_point_removal`), drop shadowed regions. Configurable levels: none / moderate / heavy. | M |
| FR-1.8 | Emit a `ground_truth.json` per sample conforming to the schema in §5.2. | M |
| FR-1.9 | Deterministic given (scene, config, seed): re-running produces byte-identical `cloud.ply` and `ground_truth.json`. | M |
| FR-1.10 | A dataset builder that iterates the frozen experiment grid × seeds and writes a `manifest.csv` (one row per sample: paths, grid coordinates, seed). | M |
| FR-1.11 | Optional QA render (matplotlib/Open3D offscreen) overlaying cloud and as-designed mesh. | S |
| FR-1.12 | A "clean" mode (no perturbation, no noise, no occlusion, no deviation) for pipeline sanity tests. | M |
| FR-1.13 | Random dropout as an *alternative* incompleteness model, off by default, for comparison with realistic occlusion. | C |

---

## 5. Data & interface requirements

### 5.1 Module interface (described, not implemented here)
- `generate_scene(scene_cfg) -> Mesh` (labelled).
- `make_sample(scene_cfg, grid_point, seed) -> writes {cloud.ply, ground_truth.json, scene_mesh.ply}`.
- `build_dataset(grid_cfg, seeds, out_dir) -> writes manifest.csv`.
- Files only across module boundaries (Constitution Art. IX).

### 5.2 `ground_truth.json` schema (v1)

```jsonc
{
  "schema_version": 1,
  "scene_id": "S1",
  "seed": 42,
  "grid_point": { "rot_deg": 1.0, "trans_mm": 25, "noise_sigma_mm": 3,
                  "occlusion": "moderate" },
  "T_gt": [[...4x4 row-major...]],          // cloud-frame -> BIM-frame is inverse(T_gt)
  "sensor": { "origins_m": [[x,y,z], ...], "noise_sigma_mm": 3.0,
              "outlier_rate": 0.0 },
  "point_density_per_m2": 2500,
  "elements": [
    { "id": 3, "class": "wall", "normal": [0,1,0],
      "nominal_deviation": { "type": "normal_offset", "value_mm": 14.0 },
      "is_out_of_tolerance": true }
  ],
  "tolerance_mm": 10.0,
  "notes": ""
}
```

### 5.3 Config files
- `configs/scenes/S1.yaml`, `configs/scenes/S2.yaml` — geometry parameters.
- `configs/grid.yaml` — the **frozen experiment grid** (see §5.4).
- `configs/seeds.yaml` — default seed list.

### 5.4 Frozen experiment grid (proposed; finalised at this gate — decision D5)

| Axis | Levels | Note |
|---|---|---|
| Registration rotation error injected pre-alignment | 0.0, 0.5, 1.0, 2.0, 4.0° | primary axis — keep dense |
| Registration translation error injected pre-alignment | 0, 10, 25, 50, 100 mm | primary axis |
| Sensor noise σ | 1, 3, 5 mm | secondary |
| Occlusion | none, moderate, heavy | secondary |
| Seeds per cell | 10 | for confidence intervals |

> Note: the injected pre-alignment error defines the *difficulty*; the **residual** error
> after registration is what Phase 4 correlates with detection performance. Full Cartesian
> product = 5×5×3×3×10 = 2 250 samples/scene; each generates and processes in seconds.
> Fallback (R2): drop noise to {1,5} and occlusion to {none,heavy} → 1 000/scene.

---

## 6. Non-functional requirements

- **NFR-1.1 Reproducibility:** FR-1.9 holds across machines with the same library versions.
- **NFR-1.2 Performance:** full default dataset for both scenes generates in ≤ 15 min on a
  laptop CPU.
- **NFR-1.3 Traceability:** every perturbation applied appears in `ground_truth.json`.
- **NFR-1.4 Independence:** `datagen` imports nothing from `registration` / `deviation` /
  `experiment`.

---

## 7. Acceptance criteria & verification

Phase 1 is **done** when:

1. `python -m datagen.build_dataset --config configs/grid.yaml` produces both scene datasets
   and `manifest.csv` with the expected row count — *verify by running it*.
2. **Determinism test:** two runs with the same seed produce identical file hashes — *automated test*.
3. **Round-trip test:** applying `inverse(T_gt)` to `cloud.ply` and computing point-to-mesh
   distance on a *clean* sample yields RMS ≤ 0.5 mm (only nominal deviations remain) —
   *automated test*.
4. **Deviation-label test:** for a sample with element *k* offset by 14 mm and τ = 10 mm,
   `ground_truth.json` marks element *k* out of tolerance and all undisturbed elements within
   — *automated test*.
5. **Occlusion test:** heavy occlusion removes a non-trivial, scanner-consistent fraction of
   points (not random) — *visual QA render + coverage statistic*.
6. Demonstrable artifact: a figure showing S1 and S2, each as as-designed mesh + as-built
   cloud, with one deviated element highlighted.
7. Owner approves the frozen grid (D5).

---

## 8. Risks & fallback

| Risk | Fallback |
|---|---|
| Occlusion simulation (hidden-point removal) unstable on thin geometry | Use multi-view ray casting against the mesh; or accept parametric radius tuning per scene, documented. |
| Grid too large for weekly compute budget | Apply the R2 reduced grid; keep the registration-error axis full. |
| Two scenes not ready in the time-box | Ship S1; add S2 in Phase 4 slack (R4 fallback). |

---

## 9. Out of scope for Phase 1

- Any registration or deviation computation (Phases 2–3).
- Real-data ingestion (Phase 5 qualitative demo).
- Curved geometry, MEP, furniture, multi-storey (Constitution Art. III).
- Photorealistic rendering or physically-based LiDAR intensity/beam-divergence modelling.
