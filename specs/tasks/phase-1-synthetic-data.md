# Tasks — Phase 1: Synthetic Data Generation Framework

Ordered, checkable. Implements the plan in `specs/plan/phase-1-synthetic-data.md`.
Check off in commits, not in this file's prose — keep `[ ]`/`[x]` as the only edits.

## Scaffold
- [x] `pyproject.toml` / `requirements.txt` with the Art. VI stack (Python ≥3.11, Open3D,
      NumPy, SciPy, trimesh, Matplotlib, pandas, PyYAML) + pytest. (Also added `rtree`,
      a trimesh runtime dependency for spatial queries — not in Art. VI's list explicitly,
      noted as a transitive necessity, not a new top-level choice.)
- [x] `src/datagen/__init__.py` package skeleton.
- [x] `configs/scenes/`, `configs/grid.yaml`, `configs/seeds.yaml` directories.
- [x] Python 3.12 venv (`.venv/`) — 3.13 (the system default) has no `open3d` wheel yet;
      installed Python 3.12 via winget alongside it, used only for this project's venv.

## Scene construction (FR-1.1, FR-1.2)
- [x] `elements.py`: `Element` dataclass + `.mesh()` quad builder.
- [x] `configs/scenes/S1.yaml`: 4 walls + slab + 4 columns (room).
- [x] `configs/scenes/S2.yaml`: 2 walls + slab + 4 repeated columns (corridor).
- [x] `scene.py`: `generate_scene(scene_cfg) -> (trimesh.Trimesh, list[Element])`, with a
      `face_id -> element_id` lookup array.
- [x] `test_scene.py`: element count/ids/unit-normal checks for S1 and S2 — 5 tests pass.

## Sampling (FR-1.3)
- [x] `sampling.py`: `sample_cloud(mesh, density_per_m2, rng) -> points, normals, face_ids`.
- [ ] Visual QA render confirming uniform coverage (FR-1.11, stretch — optional, not done).

## Perturbation (FR-1.4–1.7)
- [x] `perturb.py::apply_nominal_deviations` — offset/tilt selected elements' quads before
      re-meshing; returns per-element `{type, value_mm}`.
- [x] `perturb.py::sample_registration_transform` — seeded `T_gt` (rotation deg, translation
      mm) from grid-point ranges.
- [x] `perturb.py::add_noise` — Gaussian along local normal + optional outliers.
- [x] `perturb.py::apply_occlusion` — Open3D hidden-point-removal per scanner origin,
      none/moderate/heavy levels.
- [ ] `test_occlusion.py`: heavy occlusion removes a non-trivial, non-random (scanner-
      consistent) fraction of points (SRS §7.5) — needs a visual/coverage-statistic check,
      not just an automated assertion; **not done**, do by hand once time allows.

## Ground truth + I/O (FR-1.8, FR-1.9)
- [x] `groundtruth.py`: writer/reader for schema v1 (SRS §5.2), `is_out_of_tolerance` from τ.
- [x] `io.py`: `cloud.ply` / `scene_mesh.ply` read-write via Open3D.
- [x] `test_determinism.py`: same seed twice -> identical file hashes (FR-1.9) — 2 tests pass.

## Dataset builder (FR-1.10, FR-1.12)
- [x] `build_dataset.py`: CLI iterating `configs/grid.yaml` × `configs/seeds.yaml`, writes
      `manifest.csv` per scene.
- [x] `--clean` mode (FR-1.12): one no-perturbation sample per scene.
- [x] `test_roundtrip.py`: clean sample, `inverse(T_gt)` applied, point-to-mesh RMS ≤ 0.5 mm
      — passes (needed adding `rtree` — trimesh's spatial-query backend — to requirements).
- [x] `test_labels.py`: element offset 14 mm at τ = 10 mm mesh flagged; others not — 3 tests
      pass (covers the flagged / sub-tolerance / no-deviation cases).

## Point density — resolved mid-build (see decision log note below)
- [x] Benchmarked `point_density_per_m2`: the SRS §5.2 schema example (2500/m²) is a
      *documentation example*, not a frozen value — at 2500 the full grid projected to
      ~5.5h / ~47GB, violating NFR-1.2 (≤15 min) and the laptop-disk assumption (A5).
      Reset to **100/m²** in `configs/grid.yaml` → ~13 min / ~2.1GB projected, confirmed by
      an actual full run (see Gate below). This is a config value, not one of D1–D5, so
      resolved directly rather than escalated; raise it again later per-experiment if wanted.

## Gate (Phase 1 SRS §7 / roadmap Week 2)
- [x] Full run: `python -m datagen.build_dataset --config configs/grid.yaml` produces both
      scene datasets + manifests with expected row counts — **ran to completion**,
      `data/S1/manifest.csv` and `data/S2/manifest.csv` each have exactly 2250 data rows
      (5×5×3×3×10, matching decision D5's frozen grid).
- [x] Demonstrable artifact: `reports/figures/phase1_scenes.png` — S1 and S2, each as-designed
      mesh (wireframe) + as-built cloud (scatter), deviated element highlighted in red.
- [ ] Owner confirms the frozen grid (D5 already ratified in decision log covers the grid
      *shape*; still want a look at the actual run / figure, and at the density change above).
- [ ] Commit + push (held for owner's return per their instruction).

## Deferred (documented, not silent — see plan §2)
- [ ] Wall opening (doorway/window cut) — not attempted this pass, time went to the density
      fix and the full run instead. Still a documented, harmless gap: no FR/§7 criterion
      depends on it.
