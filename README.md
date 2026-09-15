# Registration-Error-Aware Deviation Detection Between As-Built Point Clouds and As-Designed BIM Models

Semester research project — Computer Vision for Construction Engineering.

## Problem

Construction QC compares an as-designed BIM model against the as-built structure captured by
laser scanning / photogrammetry. This needs (1) **registration** of the point cloud into the
BIM coordinate frame and (2) **deviation analysis** between the two. These steps are almost
always treated independently, so reported "deviations" are contaminated by unquantified
**registration error** rather than reflecting true construction discrepancies.

## Research question

Under controlled, quantifiable registration error, how does a plane-based coarse-to-fine
registration strategy compare to a generic point-based baseline (FPFH+RANSAC / ICP) in
(a) alignment accuracy and (b) the reliability of downstream deviation detection? How does
registration error propagate into false-positive / false-negative deviation flags?

The contribution is a **reproducible empirical coupling analysis** (detection precision/recall
vs injected registration error, plane-based vs point-based, plus a practical "registration
budget"), not a new registration algorithm.

## Status

**Phase 1 (synthetic data) implemented and gate-tested.** Phase 0 (spec suite) is approved;
decisions D1–D5 are resolved. The full spec suite is in [`specs/`](specs/):

| Document | Purpose |
|---|---|
| [`specs/constitution.md`](specs/constitution.md) | Non-negotiable project principles |
| [`specs/literature-review.md`](specs/literature-review.md) | Prior work, the gap, design insights |
| [`specs/roadmap.md`](specs/roadmap.md) | Workflow, 7-week schedule, risks, assessment package |
| [`specs/srs/`](specs/srs/) | One Software Requirements Specification per phase (0–5) |
| [`specs/plan/`](specs/plan/) | Per-phase technical design (added at phase start) |
| [`specs/tasks/`](specs/tasks/) | Per-phase task checklist (added at phase start) |
| [`specs/decision-log.md`](specs/decision-log.md) | Resolved decisions D1–D5 + change record |

Start with [`specs/README.md`](specs/README.md).

## Stack

Python ≥ 3.11 (venv uses 3.12 — `open3d` has no 3.13 wheel yet) · Open3D · NumPy · SciPy ·
trimesh · rtree · Matplotlib · pandas · PyYAML.

## Layout

```
specs/        # governance + phase specs, plans, task lists
src/datagen/  # Phase 1: synthetic as-built cloud / as-designed BIM generator (done)
configs/      # scenes (S1, S2), experiment grid, seeds
scripts/      # one-off figure/report generation scripts
data/         # generated datasets (git-ignored) + manifests
results/      # metrics, figures (git-ignored except final)
reports/      # assessment package, final report, demonstrable-artifact figures
tests/
```

## Reproduction

```
python -m venv .venv && .venv/Scripts/activate   # (or source .venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
pytest                                            # Phase 1 self-validation (Art. II)
python -m datagen.build_dataset --config configs/grid.yaml --out data/   # ~13 min, ~2GB
python scripts/render_phase1_figure.py            # Phase 1 demonstrable artifact
```

A single command regenerating every *figure* end-to-end (all phases) will be added in
Phase 5.
