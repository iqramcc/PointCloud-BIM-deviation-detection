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

**Planning phase.** No pipeline code yet. The full spec suite is in [`specs/`](specs/):

| Document | Purpose |
|---|---|
| [`specs/constitution.md`](specs/constitution.md) | Non-negotiable project principles |
| [`specs/literature-review.md`](specs/literature-review.md) | Prior work, the gap, design insights |
| [`specs/roadmap.md`](specs/roadmap.md) | Workflow, 7-week schedule, risks, assessment package |
| [`specs/srs/`](specs/srs/) | One Software Requirements Specification per phase (0–5) |
| [`specs/decision-log.md`](specs/decision-log.md) | Open decisions D1–D5 + change record |

Start with [`specs/README.md`](specs/README.md).

## Planned stack

Python ≥ 3.11 · Open3D · NumPy · SciPy · trimesh · Matplotlib · pandas · PyYAML.

## Planned layout

```
specs/        # governance + phase specs (this phase)
src/          # datagen | registration | deviation | experiment  (Phases 1–4)
configs/      # scenes, experiment grid, frozen parameters, seeds
data/         # generated datasets (git-ignored) + manifests
results/      # metrics, figures (git-ignored except final)
reports/      # assessment package, final report, presentation
tests/
```

## Reproduction

_To be added in Phase 5 — a single command regenerating every figure from configs + seeds._
