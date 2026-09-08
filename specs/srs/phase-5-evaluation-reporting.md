# SRS — Phase 5: Evaluation, Reporting & Reproducibility

**Status:** Draft v0.1 · **Time-box:** Week 7 + buffer (2026-10-20 – 2026-10-31) · **Gate:**
final report + presentation submitted; the whole study reproduces from a clean checkout with
one command.

Governed by `specs/constitution.md` (esp. Art. I, V, VIII). Cites `literature-review.md`,
Insight I5.

---

## 1. Introduction

### 1.1 Purpose
Turn the Phase 4 results into the submitted deliverables: a written report, a presentation,
one qualitative real-data demonstration, and a reproducible repository.

### 1.2 Phase context
Final phase. Consumes `results/` from Phase 4 and the real dataset identified in Phase 0.
No new methods; a real-data run is added purely for qualitative illustration.

---

## 2. Research context

- The gap and contribution are as stated in `literature-review.md` §6.
- Insight I5 governs the real-data section: it shows the pipeline runs end-to-end; it does
  **not** validate the coupling curve, and the report says so explicitly.
- `Dataset and benchmark for as-built BIM reconstruction...` (Automation in Construction
  2025) is cited for the field-wide shortage of BIM ground truth that motivates the
  synthetic approach.

---

## 3. Overall description

- **Inputs:** `results/runs.parquet`, `results/figures/*`, `results/coupling_report.md`,
  the real dataset (Mendeley `pssxxtjyyf` or equivalent), all specs.
- **Outputs:** `reports/final_report.*`, `reports/presentation.*`, `reports/real_data_demo/*`,
  a top-level `README.md` reproduction recipe, a `make reproduce` (or `reproduce.sh`) target,
  an environment lock file, and a short `LIMITATIONS.md`.

---

## 4. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | Final report covering: problem & confound, research question, literature review & gap, method (pipeline, data generation, baselines, metrics), experimental design, results vs H1–H5, the registration-budget finding, limitations, future work, reproducibility statement. | M |
| FR-5.2 | The report's every quantitative claim references a figure/table traceable to `runs.parquet`. | M |
| FR-5.3 | A presentation (~12–15 slides) derived from the report: motivation, gap, method, headline coupling curve, registration budget, limitations. | M |
| FR-5.4 | **Qualitative real-data demo:** download the real scan (record source/licence/date), preprocess, run both registration baselines against a coarse BIM/plane model of the scene, run deviation computation, produce one heatmap figure. No quantitative claims. | S |
| FR-5.5 | `README.md` with: project summary, install steps, and the single command that regenerates the full result set and figures. | M |
| FR-5.6 | A `reproduce` target that runs datagen → experiment → figures end-to-end on the reduced grid in a documented time. | M |
| FR-5.7 | Environment lock (`requirements.txt` pinned or `pyproject.toml` + lock); a `python --version` note. | M |
| FR-5.8 | `LIMITATIONS.md`: synthetic-only scope, single tolerance model, two scenes, classical methods, plane-matcher mode used, statistical power. | M |
| FR-5.9 | `specs/decision-log.md` finalised: every D-item resolved, every mid-project change recorded. | M |
| FR-5.10 | A short "reproducibility checklist" in the report (data, code, config, seeds, environment, command). | S |
| FR-5.11 | Archive the final dataset manifest + configs + `runs.parquet` (not raw clouds) so results are checkable without regeneration. | S |

---

## 5. Data & interface requirements

- Report format: whatever the course requires (LaTeX/PDF or DOCX). The repo keeps the
  source and the built artifact.
- Figures reused verbatim from `results/figures/` — no re-plotting by hand.
- Real-data artifacts isolated under `reports/real_data_demo/` with their own README noting
  licence and that the section is qualitative.

---

## 6. Non-functional requirements

- **NFR-5.1 Reproducibility (hard gate):** a second person, clean checkout, following only
  `README.md`, regenerates every figure in the report on the reduced grid — *tested with a
  fresh virtual environment*.
- **NFR-5.2 Honesty:** limitations and any null results are in the report body, not only an
  appendix (Constitution Art. V).
- **NFR-5.3 Self-containment:** the report is understandable without reading the code;
  the code is runnable without reading the report.
- **NFR-5.4 No unlabelled manual results:** any figure involving a manual step (e.g. the
  real-data plane seeds) is labelled as qualitative.

---

## 7. Acceptance criteria & verification

Phase 5 is **done** when:

1. The final report and presentation are submitted in the required format by the deadline.
2. **Fresh-environment reproduction:** clean clone + new venv + `make reproduce` regenerates
   `runs.parquet` (reduced grid) and all report figures without manual intervention —
   *executed and logged*.
3. Every numeric claim in the report resolves to a figure/table and a `runs.parquet` filter
   — *checked line by line*.
4. `LIMITATIONS.md` and a finalised `decision-log.md` are committed.
5. The real-data demo produces one heatmap and is clearly marked qualitative.
6. Demonstrable artifact: the submitted report + deck + a terminal log of the fresh-env
   reproduction.

---

## 8. Risks & fallback

| Risk | Fallback |
|---|---|
| Time runs out before the real-data demo | Drop FR-5.4; the study is synthetic-only by design and stands without it. State it in future work. |
| Reproduction fails on another machine (library drift) | Pin exact versions; provide a `conda`/`venv` spec; if Open3D differs, pin the tested Open3D build and note it. |
| Report scope balloons | Enforce the FR-5.1 outline; results section leads with the headline figure and the budget table. |
| Results are inconclusive | Report honestly: "under these controlled conditions the coupling is X; separating the baselines needs Y" — an inconclusive-but-rigorous study is a valid semester outcome. |

---

## 9. Out of scope for Phase 5

- Any new experiment not already in `runs.parquet` (except the qualitative real-data run).
- Quantitative analysis of the real dataset (Insight I5).
- Journal/conference paper preparation (can be listed as future work).
- Packaging as a reusable library / PyPI release.
