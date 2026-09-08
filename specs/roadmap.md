# Roadmap & Spec-Driven Workflow

**Status:** Draft v0.1 · **Last updated:** 2026-09-08

---

## 1. How we work (spec-driven development, adapted for research)

```
constitution.md            ← immutable principles (amend formally)
        │
literature-review.md       ← what exists, what the gap is  (living)
        │
roadmap.md                 ← this file: phases, timeline, gates
        │
specs/srs/phase-N-*.md     ← WHAT each phase must produce + acceptance criteria
        │
specs/plan/phase-N-*.md    ← HOW (technical design)      [written at the start of each phase]
        │
specs/tasks/phase-N-*.md   ← ordered, checkable task list [written at the start of each phase]
        │
   implementation           ← code + demonstrable artifact
        │
   phase gate               ← acceptance criteria met → owner approves → next phase
```

**Rules**

- No code is written for a phase until its **SRS is approved** and its **plan + tasks**
  exist.
- Each phase ends at a **gate**: the SRS acceptance criteria are checked, the demonstrable
  artifact is shown, and the project owner approves proceeding (Constitution, Art. VIII).
- Scope/method/interface changes are logged in `specs/decision-log.md` (Art. X).
- Current stage: **all Phase SRS drafted, awaiting owner verification.** No implementation
  has begun.

---

## 2. Assumptions (correct these if wrong)

| # | Assumption | Impact if wrong |
|---|---|---|
| A1 | Final submission ≈ **last week of October 2026** (planning against **Fri 31 Oct**). | Compresses/extends every phase. |
| A2 | Preliminary assessment ≈ **2026-09-12**; expectation is a *substantive plan + literature command + early evidence*, not finished results. | Changes the Phase 0 deliverable. |
| A3 | Team = small group of students, limited hours/week, assisted by Claude Pro (usage-limited). | Drives time-boxing and "library over custom" (Art. VI). |
| A4 | The as-designed model is generated **programmatically** for the controlled experiments; a Revit export is an optional later "realistic scene". *(Owner to confirm — see decision D1.)* | If Revit-first: Phase 1 blocks on the export. |
| A5 | Compute = a student laptop (no GPU assumed). Classical methods only, so this is sufficient. | GPU-only methods would be excluded anyway (Art. III). |

---

## 3. Phases

| Phase | Goal (one line) | Demonstrable artifact | Time-box |
|---|---|---|---|
| **0 — Foundations** | Spec suite, literature synthesis, assessment package | This spec folder + conceptual figures + risk register | Week 1 |
| **1 — Synthetic data** | Parametric scene → sampled cloud with injected transform / noise / occlusion / per-element deviations + ground-truth records | One command produces a labelled dataset; render of cloud vs mesh | Week 2 |
| **2 — Registration** | Preprocessing + Baseline A (FPFH+RANSAC→ICP) + Baseline B (plane-based→ICP); registration metrics | Table: rotation/translation error + runtime for both baselines on clean data | Weeks 3–4 |
| **3 — Deviation detection** | Signed point-to-mesh distance → per-element aggregate → tolerance flag → heatmap + detection metrics | Heatmap figure + precision/recall/F1 on a case with known displaced elements | Week 4 (overlaps) |
| **4 — Experiment harness & coupling analysis** | Frozen grid runner; coupling curves (detection vs injected registration error); FP/FN spatial analysis | The core result plots (F1 vs registration error, per method, per scene) | Weeks 5–6 |
| **5 — Evaluation & reporting** | Final figures, written report, presentation, reproducible repo | Submitted report + deck + `make reproduce` | Week 7 (+ buffer to 31 Oct) |

Phases 3 and 2b overlap deliberately: the deviation module can be built and tested against a
*perfectly aligned* cloud while Baseline B is still being finished.

### 3.1 Week-by-week

| Week | Dates (2026) | Focus | Gate output |
|---|---|---|---|
| 1 | Sep 08–14 | Phase 0. **Prelim assessment Sep 12.** | Approved specs; assessment package |
| 2 | Sep 15–21 | Phase 1 | Labelled synthetic dataset + generator tests |
| 3 | Sep 22–28 | Phase 2a: preprocessing + Baseline A | Baseline A recovers known transforms on clean data |
| 4 | Sep 29–Oct 05 | Phase 2b: Baseline B + Phase 3 start | Both baselines run; deviation module validated on perfect alignment |
| 5 | Oct 06–12 | Phase 4: harness + first grid run | Coupling curves (draft) for one scene |
| 6 | Oct 13–19 | Phase 4: second scene, ablations, spatial analysis | Complete result set |
| 7 | Oct 20–26 | Phase 5: report + deck + reproducibility pass | Draft report + deck |
| buffer | Oct 27–31 | Revisions, final submission | Final submission |

### 3.2 Fallbacks (taken automatically on time-box overrun — Art. VI)

- **Phase 1 overrun:** ship one scene instead of two; add the second scene only if Phase 4
  finishes early.
- **Phase 2b (plane matcher) overrun:** use the semi-automatic matcher with 2–3 seeded plane
  correspondences (documented precedent: Bosché); note it as a limitation.
- **Phase 4 overrun:** shrink the grid (fewer noise/occlusion levels), keep full resolution
  on the registration-error axis (the primary variable).
- **Any severe overrun:** the study still stands with **Baseline A only** as a
  registration-error → detection-reliability characterization; the A-vs-B comparison becomes
  "future work".

---

## 4. Preliminary assessment package (2026-09-12)

**Goal:** demonstrate command of the field and engineering rigor; show the project is
already de-risked and executing — without claiming finished results.

**Contents**

1. **One-page problem & contribution statement** — the confound, the research question, the
   single-sentence novelty claim.
2. **Literature review** (`literature-review.md`) — the tables in §2–§5 and the gap in §6.
   This is the main "impress" element: it shows the gap is real and precisely located.
3. **Methodology** — the coupling-analysis design: inject known registration error, measure
   deviation-detection precision/recall, compare front-ends. Include:
   - a **pipeline diagram** (preprocess → register ×2 → deviate → evaluate);
   - a **conceptual figure** of how rotational vs translational registration error propagates
     into false positives/negatives (Insight I1);
   - a **mock "coupling curve"** (expected shape of F1 vs registration error) — clearly
     labelled as the hypothesis, not data.
4. **Spec-driven project structure** — the constitution + phased SRS; shows the plan is
   concrete and governed.
5. **7-week roadmap** (§3) with gates and fallbacks.
6. **Risk register** (§5).
7. **Evidence of progress** — the spec suite itself; the frozen experiment-grid proposal;
   the identified real dataset (Mendeley `pssxxtjyyf`); the chosen stack and why.
8. *(Stretch, only if Phase 0 finishes early and owner approves a small code exception)* a
   single rendered figure of a synthetic scene + its point cloud, to show the data pipeline
   is trivial to stand up.

**Format:** a short written progress report **and** a ~8–10 slide deck built from the same
content. Both to be produced *after* the specs are approved.

---

## 5. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner action |
|---|---|---|---|---|---|
| R1 | Plane-matching (Baseline B) is too fiddly to automate in time | Med | Med | Semi-automatic seeded matcher fallback; it is a documented method, not a hack | Decide by end of Week 4 |
| R2 | Experiment grid explodes → runs don't finish | Med | High | Freeze a small grid at end of Phase 1; each run is seconds; parallelise trivially | Grid frozen in Phase 1 SRS |
| R3 | Unfair comparison via per-cell tuning | Low | High | Constitution Art. IV: tune once on held-out condition, freeze, publish table | Parameter table in Phase 2 |
| R4 | Single synthetic scene → weak external validity | Med | Med | Two scenes (well-conditioned + geometrically ambiguous) | Phase 1 |
| R5 | Synthetic-only invites "not realistic" criticism | High | Low | State it as a deliberate, necessary choice (Insight I5); one real-data qualitative run | Framing in report |
| R6 | Claude Pro usage limits stall assisted work | Med | Med | Small resumable units; specs done first so implementation is mechanical | Ongoing |
| R7 | Timeline slips into exam period | Med | High | Fallbacks in §3.2; Baseline-A-only study is a valid finished project | Weekly gate check |
| R8 | Revit export delays Phase 1 (if Revit-first chosen) | Med | Med | Default to programmatic scenes (D1) | Owner confirms D1 |

---

## 6. Decision log seed

These go into `specs/decision-log.md` once the owner rules on them.

| ID | Decision needed | Recommendation |
|---|---|---|
| D1 | Programmatic scenes vs Revit-first | **Programmatic** for controlled experiments; Revit model optional realistic scene later |
| D2 | Distance metric for deviation | Signed cloud-to-mesh (C2M) as default; M3C2 considered if surfaces are noisy |
| D3 | Per-element aggregate | Signed **median** normal offset as primary; 95th-percentile point distance as ablation (Insight I4) |
| D4 | Construction tolerance τ | Single documented value (e.g. 10 mm structural) from J. Building Eng. 2025 / code refs; sensitivity checked in Phase 4 |
| D5 | Experiment grid resolution | Fixed at end of Phase 1; registration-error axis kept dense, other axes coarse |
