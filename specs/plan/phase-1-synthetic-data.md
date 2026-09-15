# Plan — Phase 1: Synthetic Data Generation Framework

**Status:** Draft v0.1 · Implements `specs/srs/phase-1-synthetic-data.md` (FR-1.1–1.13).
Technical design ("HOW"); requirements live in the SRS ("WHAT").

---

## 1. Module layout (Constitution Art. IX)

```
src/datagen/
├── __init__.py
├── elements.py        # Element dataclass, per-element geometry helpers
├── scene.py            # generate_scene(scene_cfg) -> (trimesh.Trimesh, list[Element])
├── sampling.py          # sample_cloud(mesh, density_per_m2, rng) -> (N,3) points + normals
├── perturb.py            # nominal deviation, T_gt rigid perturbation, noise, occlusion
├── groundtruth.py         # ground_truth.json schema (v1) writer/reader
├── io.py                   # cloud.ply / scene_mesh.ply read-write (Open3D)
└── build_dataset.py         # CLI: iterate grid x seeds -> manifest.csv

configs/
├── scenes/S1.yaml, S2.yaml
├── grid.yaml            # frozen experiment grid (Phase 1 SRS §5.4)
└── seeds.yaml

tests/
├── test_scene.py          # element count, ids unique, normals unit-length
├── test_determinism.py     # same seed -> identical file hashes (FR-1.9)
├── test_roundtrip.py        # inverse(T_gt) + clean sample -> RMS <= 0.5mm (SRS §7.3)
└── test_labels.py             # deviated element correctly flagged (SRS §7.4)
```

`datagen` imports only trimesh/Open3D/NumPy/SciPy/PyYAML — nothing from `registration`,
`deviation`, `experiment` (NFR-1.4).

---

## 2. Element representation

Every scene element is a **planar rectangular patch** (Phase 1 SRS §1.3 definition), not an
arbitrary solid — this keeps "one outward normal per element" (the `ground_truth.json`
schema, §5.2) exactly true and keeps mesh construction to a single two-triangle quad per
element.

```python
@dataclass
class Element:
    id: int
    cls: str            # "wall" | "slab" | "column"
    center: np.ndarray  # (3,) world-space centroid, meters
    normal: np.ndarray  # (3,) unit outward normal
    u_axis: np.ndarray  # (3,) unit "width" direction, in-plane, perpendicular to normal
    width: float         # meters, along u_axis
    height: float          # meters, along v_axis = normal x u_axis
```

`element.mesh()` builds the two-triangle quad in world space from these five numbers.
Columns are modelled as one representative planar face each (the face visible from the
scanner origins) rather than a 4-sided box — a deliberate simplification consistent with the
SRS's "planar elements" definition; noted as a limitation in the final report, not hidden.

**Scoped down for this time-box (documented fallback, not silently dropped):** the "one
opening" mentioned in the SRS §1.3 definitions (a doorway/window cut into a wall) requires
polygon-with-hole triangulation. It is deferred to a later pass if time allows — S1/S2 ship
without an opening first, since FR-1.1/1.2 (labelled mesh, 2 scenes) do not require it and no
acceptance criterion in §7 depends on it.

---

## 3. Scene geometry (concrete numbers, not in the SRS — decided here)

### S1 "well-conditioned" — a room
- Footprint 6.0 m (x) × 5.0 m (y), height 3.0 m (z).
- Elements: 4 walls (N/S/E/W, distinct normals ±x/±y), 1 floor slab (normal +z), 4 corner
  columns (0.4 m wide representative face each, normal pointing to room center) → 9 elements.

### S2 "ambiguous" — a repetitive corridor bay
- 12.0 m (x, corridor axis) × 2.5 m (y) × 3.0 m (z).
- Elements: 2 long side walls (normals ±y only — few distinct directions, by design), 1 floor
  slab, 4 columns repeated every 3 m along x (all identical spacing/orientation → weak
  translational constraint along x) → 7 elements.

Both defined declaratively in `configs/scenes/S{1,2}.yaml`; `scene.py` is generic over the
YAML, not hardcoded per scene.

---

## 4. Pipeline per sample (`make_sample`)

1. Load scene YAML → build `Element` list → assemble as one labelled `trimesh.Trimesh` with a
   `face_id -> element_id` map (this is `scene_mesh.ply`, the as-designed geometry).
2. **Nominal deviation (FR-1.4):** for the subset of elements named in the grid point, offset
   the element's plane along its own normal (and/or small in-plane translation / tilt) —
   rebuild just those element quads, re-triangulate the mesh. Record `{type, value_mm}` per
   deviated element.
3. **Sample cloud (FR-1.3):** `trimesh.sample.sample_surface(mesh, n_points)` — area-weighted,
   already uniform; `n_points = round(density_per_m2 * total_surface_area)`.
4. **Occlusion (FR-1.7):** for each configured scanner origin, run Open3D
   `PointCloud.hidden_point_removal` (Katz et al. visibility) and keep the union of visible
   points across origins; occlusion level maps to origin count/placement (none = keep all;
   moderate = 1 origin; heavy = 1 origin placed to graze the scene, e.g. near a wall).
5. **Noise (FR-1.6):** Gaussian offset along each point's local face normal, σ from config;
   optional isotropic jitter; optional uniform-random outlier injection at `outlier_rate`.
6. **Registration perturbation (FR-1.5):** draw `T_gt` (rotation from `rot_deg`, translation
   from `trans_mm`, random axis/direction from the seeded RNG) and apply to the whole cloud.
   Store `T_gt` (4×4) and confirm `inverse(T_gt) @ T_gt ≈ I` in the round-trip test.
7. Write `cloud.ply` (points + normals), `scene_mesh.ply` (undeviated *or* deviated-but-
   unperturbed, per `ground_truth.json.elements[*].nominal_deviation` — the mesh always
   represents true as-built geometry pre-scan-perturbation, matching SRS §7.3's round-trip
   contract), `ground_truth.json` (schema v1, SRS §5.2).

All randomness comes from one `numpy.random.default_rng(seed)` threaded explicitly through
every step (Constitution Art. I.3) — no hidden global RNG state.

---

## 5. `build_dataset` CLI

```
python -m datagen.build_dataset --config configs/grid.yaml --out data/
```
Iterates the Cartesian product in `configs/grid.yaml` × `configs/seeds.yaml` per scene,
calls `make_sample`, writes one row per sample to `data/<scene>/manifest.csv`
(FR-1.10). A `--clean` flag runs the FR-1.12 no-perturbation sanity mode (one sample per
scene, used by the round-trip test).

---

## 6. Test-first order (Constitution Art. II — generator validated before methods)

1. `test_scene.py` — mesh has expected element count/ids/unit normals for S1 and S2.
2. `test_determinism.py` — two `make_sample` calls, same seed, byte-identical `cloud.ply`.
3. `test_roundtrip.py` — clean sample, apply `inverse(T_gt)`, point-to-mesh RMS ≤ 0.5 mm.
4. `test_labels.py` — element offset 14 mm at τ = 10 mm ⇒ flagged; undisturbed elements not.

These four are the Phase 1 gate (SRS §7 items 2–4) and are written alongside the code that
makes each one pass, not after.

---

## 7. Dependencies added this phase

- `trimesh` — mesh construction/sampling (already in Art. VI stack).
- `open3d` — hidden-point-removal occlusion, `.ply` I/O.
- No new dependency beyond the constitution's target stack.
