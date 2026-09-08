# Project Constitution
## Registration-Error-Aware Deviation Detection Between As-Built Point Clouds and As-Designed BIM Models

**Status:** Draft v0.1 · **Owner:** Project team · **Last updated:** 2026-09-08
**Governs:** all phase SRS documents, task lists, and implementation choices in this repository.

---

### Preamble

This constitution defines the non-negotiable principles that govern how this project is
planned, built, and evaluated. It sits **above** the phase-level Software Requirements
Specifications (SRS). When an SRS, a task, or an implementation choice conflicts with an
article below, the article wins — or the constitution must be formally amended (see
*Amendment Process*).

This is **research software**, not a product. Its purpose is to produce a defensible,
reproducible empirical answer to one research question within a ~7-week academic term.
Every article below serves that purpose.

---

### Article I — Reproducibility is the primary quality metric

1. Every quantitative result in the final report MUST be regenerable from (a) a pinned code
   revision, (b) a versioned config file, and (c) an integer random seed — via a single
   documented command.
2. No result derived from manual point-picking, hand-tuned one-off alignment, or interactive
   GUI steps may appear in the quantitative findings. Such steps are permitted only for
   qualitative illustration and MUST be labelled as such.
3. All randomness (scene perturbation, noise, occlusion, RANSAC sampling) draws from
   explicitly seeded generators. Default seeds are recorded in config.
4. Third-party data (real scans) MUST be documented with source URL, licence, access date,
   and every preprocessing step applied.

*Rationale:* the contribution is an empirical characterization. If it cannot be reproduced,
it is an anecdote.

---

### Article II — Ground truth and evaluation are built before methods

1. The synthetic data generator (Phase 1) and the evaluation metrics (Phase 4) MUST be
   implemented and self-validated **before** either registration baseline is tuned or
   compared.
2. The data generator MUST emit, with every point cloud, a machine-readable ground-truth
   record: the applied rigid transform, the noise parameters, the occlusion configuration,
   and the per-element deviation labels.
3. Evaluation code MUST be verified on cases with a known answer (e.g. zero-error alignment
   ⇒ F1 = 1.0; a known displaced element ⇒ that element flagged) before it is trusted on
   experiments.

*Rationale:* a comparison is only as trustworthy as its yardstick. Building the yardstick
first prevents unconscious tuning toward a desired outcome.

---

### Article III — Scope discipline

1. **In scope:** classical geometric registration (FPFH + RANSAC global, plane-based coarse,
   ICP refinement), point-to-surface deviation analysis, synthetic data with controlled
   perturbations, **at most two** parametric scenes, and **one** qualitative real-data
   demonstration.
2. **Out of scope for the entire term:** learned / deep registration and descriptors;
   automatic semantic segmentation of the scan; curved or MEP geometry; multi-storey
   buildings; real-world ground-truth deviation surveying; a graphical user interface;
   ROS / real-time operation.
3. Moving an item from out-of-scope to in-scope requires a constitution amendment **and**
   the removal of in-scope work of comparable size.
4. The experiment grid is frozen at the end of Phase 1 and changed only by a recorded
   decision.

*Rationale:* a narrow finished study beats a broad unfinished one. The novelty is the
coupling analysis, not algorithmic breadth.

---

### Article IV — Fair comparison between baselines

1. Both registration baselines share the same preprocessing, the same ICP refinement code
   and parameters, the same evaluation code, and the same input clouds per experiment cell.
2. Every tunable parameter (voxel size, feature radius, RANSAC budget, ICP threshold,
   plane-segmentation thresholds) is tuned **once** on a held-out calibration condition,
   then frozen and published in a parameter table.
3. Per-method special-casing of individual experiment cells is forbidden.
4. Runtime is measured on one machine, reported with hardware specs.

*Rationale:* the result must reflect the methods, not the operator's effort budget.

---

### Article V — Research honesty

1. A null or negative result (e.g. "plane-based registration shows no measurable advantage
   under our conditions") is a valid outcome and MUST be reported as found.
2. Hypotheses are written down **before** the full experiment run, in the Phase 4 SRS and
   the decision log, so confirmation and surprise remain distinguishable.
3. The limitations of synthetic-only evaluation are stated plainly in the report.
4. Prior work is cited accurately; nothing the literature review shows to exist is claimed
   as novel.

---

### Article VI — Simplicity and the student time budget

1. Prefer a maintained library function over a custom implementation. Open3D / SciPy / NumPy
   / trimesh primitives are the default; custom code is justified only where no library
   covers the need (the plane-matching heuristic, the coupling analysis, plotting).
2. Target stack: Python ≥ 3.11, Open3D, NumPy, SciPy, trimesh, Matplotlib, pandas, PyYAML.
   A new dependency needs a one-line justification in the decision log.
3. Each phase is time-boxed (see `roadmap.md`). If a phase overruns, its SRS-defined
   fallback is taken rather than extending the phase.
4. Assume limited weekly hours and an AI assistant under usage limits: work in small,
   resumable units and keep every generated artifact reviewable.

---

### Article VII — Traceability to literature

1. Every non-obvious methodological choice cites, in the relevant SRS, the prior work that
   motivates it.
2. `specs/literature-review.md` is a living document; relevant work found mid-term is added,
   not ignored.

---

### Article VIII — Incremental, demonstrable delivery

1. Each phase ends with a **demonstrable artifact**: a figure, a table, a short generated
   report, or a script that produces one of these.
2. "Done" for a phase means its SRS acceptance criteria are met **and** its demonstrable
   artifact exists — not "the code is written".
3. The project must be in a presentable state at every phase boundary, because the
   assessment schedule can move.

---

### Article IX — Modularity and interface contracts

1. Four independent modules with documented, stable interfaces: `datagen`, `registration`,
   `deviation`, `experiment`. A change in one must not force edits in another beyond the
   agreed interface.
2. Data crosses module boundaries as files with documented schemas — point clouds as
   `.ply`, metadata / ground truth as `.json`, results as `.csv` / `.parquet` — not as
   in-memory objects threaded through the whole pipeline.
3. An interface is specified in the SRS before its module is built.

---

### Article X — Documentation as code

1. Specs live in the repo, under version control, beside the code they govern.
2. Any decision that changes scope, method, or an interface is recorded in
   `specs/decision-log.md`: date, context, decision, consequences.
3. The README always carries the current one-command reproduction recipe.

---

### Amendment Process

1. Propose the change as a diff to this file, with a rationale entry in the decision log.
2. The change takes effect once the project owner approves it.
3. Amendments are dated and appended below.

### Amendment History

- **v0.1 (2026-09-08):** initial draft for the preliminary assessment.
