# Specs — Registration-Error-Aware Deviation Detection

Spec-driven development for a ~7-week semester research project (final submission ≈ last week
of October 2026).

## Read in this order

1. **`constitution.md`** — the non-negotiable principles. Everything else defers to it.
2. **`literature-review.md`** — prior work, the gap, and the design-relevant insights.
3. **`roadmap.md`** — workflow, assumptions, phase list, week-by-week schedule, risk
   register, preliminary-assessment package.
4. **`srs/phase-0-foundations.md` … `srs/phase-5-evaluation-reporting.md`** — one SRS per
   phase: what it must produce and how we know it is done.
5. **`decision-log.md`** — open decisions D1–D5 (need owner ruling) and the record of every
   later change.

## Status (2026-09-08)

| Item | State |
|---|---|
| Constitution | drafted v0.1 |
| Literature review | drafted v0.1 |
| Roadmap | drafted v0.1 |
| Phase SRS 0–5 | drafted v0.1 |
| Decision log | seeded (D1–D5 open) |
| **Implementation** | **not started — awaiting owner verification of these specs** |

## Phase map

| Phase | Produces | Gate |
|---|---|---|
| 0 Foundations | this spec suite + assessment package | owner approves specs |
| 1 Synthetic data | labelled dataset generator + frozen grid | determinism + round-trip tests pass |
| 2 Registration | Baseline A + Baseline B + shared ICP + metrics | known transforms recovered on clean data |
| 3 Deviation detection | signed distance → per-element flag → heatmap + metrics | F1 = 1.0 at perfect alignment |
| 4 Experiment & coupling | frozen-grid runner + coupling curves + registration budget | headline figure + budget table with CIs |
| 5 Evaluation & reporting | report + deck + reproducible repo + real-data demo | fresh-env reproduction succeeds |

## Not started until approved

Per `roadmap.md` §1, no phase code is written until its SRS is approved and its `plan/` and
`tasks/` files exist. `plan/` and `tasks/` folders are created at the start of each phase.
