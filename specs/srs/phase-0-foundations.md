# SRS — Phase 0: Foundations, Literature Synthesis & Assessment Package

**Status:** Draft v0.1 · **Time-box:** Week 1 (2026-09-08 – 2026-09-14) · **Gate:** owner
approval of the spec suite + delivery of the preliminary-assessment package (2026-09-12).

Governed by `specs/constitution.md`. Cites `specs/literature-review.md`.

---

## 1. Introduction

### 1.1 Purpose
Produce the governance and planning artifacts for the whole project, synthesise the prior
work, and package both for the preliminary assessment. No pipeline code is written in this
phase.

### 1.2 Phase context
First phase. Everything downstream depends on the specs approved here. Output is documents
and figures only.

### 1.3 Definitions
- **Coupling analysis** — the study of how registration error propagates into
  deviation-detection precision/recall.
- **Registration budget** — the alignment accuracy required to detect defects reliably at a
  given construction tolerance (Insight I3).
- **Demonstrable artifact** — see Constitution, Art. VIII.

---

## 2. Research context

Serves the framing of the research question (RQ) and the positioning of the contribution.
The gap is established in `literature-review.md` §6: the registration/deviation coupling is
named as a limitation (Anil et al. 2013) but never measured; no comparison of registration
front-ends by downstream detection reliability exists.

---

## 3. Overall description

- **Inputs:** the proposal (`proposal.docx`), the prior web research, domain knowledge.
- **Outputs:** `constitution.md`, `literature-review.md`, `roadmap.md`, six phase SRS
  documents, a decision log, a conceptual figure set, the assessment package.
- **Constraints:** deadline 2026-09-12 for the package; students' limited hours.
- **Dependencies:** none (first phase).

---

## 4. Functional requirements

Priority: **M** must / **S** should / **C** could.

| ID | Requirement | Priority |
|---|---|---|
| FR-0.1 | A constitution defining ≥ 8 non-negotiable principles with rationale and an amendment process. | M |
| FR-0.2 | A literature review with categorised tables covering registration, deviation analysis, registration uncertainty, and synthetic data; each entry linked; a stated gap. | M |
| FR-0.3 | A roadmap: spec-driven workflow, assumptions, phase list with time-boxes and fallbacks, a week-by-week schedule to the final deadline. | M |
| FR-0.4 | One SRS per phase (Phases 0–5), each with functional requirements, data/interface requirements, acceptance criteria, and risks. | M |
| FR-0.5 | A risk register with likelihood, impact, and mitigation per risk. | M |
| FR-0.6 | A decision-log seed listing open decisions (D1–D5) with recommendations. | M |
| FR-0.7 | A conceptual figure set for the assessment: (a) pipeline diagram, (b) registration-error → FP/FN propagation schematic, (c) hypothesised coupling curve. | S |
| FR-0.8 | The preliminary-assessment package: written progress report + slide deck, assembled from the specs. | S |
| FR-0.9 | A one-line reproduction-recipe placeholder in a repo README, plus the proposed repo layout. | S |
| FR-0.10 | Identify and record the candidate real-data set (source, licence, access date). | S |
| FR-0.11 | A single rendered synthetic-scene figure as an early proof the data pipeline is trivial to stand up. | C |

---

## 5. Data & interface requirements

- All documents are Markdown under `specs/`, version-controlled.
- Proposed repository layout (created, not populated, in Phase 0):

```
Project/
├── specs/                     # this folder (Phase 0)
│   ├── constitution.md
│   ├── literature-review.md
│   ├── roadmap.md
│   ├── decision-log.md
│   ├── srs/                    # phase SRS (0–5)
│   ├── plan/                   # per-phase technical design (added at phase start)
│   └── tasks/                  # per-phase task lists (added at phase start)
├── src/
│   ├── datagen/                # Phase 1
│   ├── registration/           # Phase 2
│   ├── deviation/              # Phase 3
│   └── experiment/             # Phase 4
├── configs/                    # YAML: scenes, grid, parameters, seeds
├── data/                       # generated datasets (git-ignored) + manifests
├── results/                    # metrics tables, figures (git-ignored except final)
├── reports/                    # assessment package, final report, deck
├── tests/
├── README.md
└── pyproject.toml / requirements.txt
```

- Figure set delivered as SVG or PNG under `reports/figures/`.

---

## 6. Non-functional requirements

- **NFR-0.1** Every methodological claim in the literature review is traceable to a linked
  source or explicitly marked `[Insight]`.
- **NFR-0.2** The spec suite is internally consistent: phase numbers, module names, artifact
  names, and interface names match across all documents.
- **NFR-0.3** The assessment package is readable by a domain expert in ≤ 15 minutes and by a
  non-specialist supervisor in ≤ 30.
- **NFR-0.4** Documents are concise: no phase SRS exceeds ~300 lines.

---

## 7. Acceptance criteria & verification

Phase 0 is **done** when:

1. `constitution.md`, `literature-review.md`, `roadmap.md`, and six phase SRS exist and are
   mutually consistent (NFR-0.2) — *verify by a cross-reference read-through*.
2. The gap statement in `literature-review.md` §6 is supported by ≥ 12 distinct linked
   sources across the four categories — *verify by counting entries*.
3. The roadmap schedule terminates on or before the assumed final deadline with a buffer —
   *verify against A1*.
4. Each phase SRS has explicit, checkable acceptance criteria — *verify each §7*.
5. The owner has reviewed the suite and recorded **proceed / revise** in the decision log.
6. *(Stretch)* the assessment package (report + deck) is assembled.

---

## 8. Risks & fallback

| Risk | Fallback |
|---|---|
| Not enough time to build the deck before 2026-09-12 | Submit the written report + the spec suite; present from the specs directly. |
| Owner wants major scope changes | Revise SRS before any Phase 1 work; the constitution's amendment process applies. |

---

## 9. Out of scope for Phase 0

- Any pipeline code (`datagen`, `registration`, `deviation`, `experiment`).
- Downloading or preprocessing the real dataset (only identification).
- Finalising parameters or the experiment grid (Phase 1).
