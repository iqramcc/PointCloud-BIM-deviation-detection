# Decision Log

Append-only. Each entry: date · context · decision · consequences. Open items are
recommendations awaiting the project owner's ruling (Constitution, Art. X).

---

## Open decisions (awaiting owner)

_(none currently — D1–D5 resolved 2026-09-15, see below)_

---

## Resolved decisions

### D1 — As-designed model source
- **Date:** 2026-09-15
- **Context:** the controlled experiments need an as-designed geometry with per-element
  labels and known deviations. Owner has Revit available.
- **Decision:** generate scenes **programmatically** (parametric meshes with element IDs)
  for all quantitative work. A Revit-exported model is used only as an optional realistic
  scene later (Phase 5), not on the critical path.
- **Consequences:** Phase 1 starts immediately, no Revit dependency on the critical path;
  ground truth is exact and machine-generated rather than manually mapped.

### D2 — Deviation distance metric
- **Date:** 2026-09-15
- **Decision:** signed cloud-to-mesh (C2M) distance as default; M3C2 (Lague et al. 2013)
  only if synthetic surfaces prove too noisy.
- **Consequences:** simpler, faster; M3C2 kept as a `[C]` requirement (FR-3.11).

### D3 — Per-element aggregate
- **Date:** 2026-09-15
- **Decision:** signed **median** normal offset as primary; 95th-percentile absolute point
  distance as an ablation (Insight I4, tested in H4).
- **Consequences:** primary metric is robust to residual in-plane registration error; the
  ablation becomes a result, not just a check.

### D4 — Construction tolerance τ
- **Date:** 2026-09-15
- **Decision:** one documented default (**10 mm** for structural elements, sourced from
  J. Building Eng. 2025 / code references), with a sensitivity sweep over {5, 10, 15} mm in
  Phase 4.
- **Consequences:** results are reported at one headline τ with a sensitivity panel.

### D5 — Experiment grid resolution
- **Date:** 2026-09-15
- **Decision:** frozen per Phase 1 SRS §5.4. Registration-error axis dense (5 rotation × 5
  translation levels); noise and occlusion coarse (3 levels each); 10 seeds/cell.
- **Consequences:** ~2 250 samples/scene, seconds each; reduced-grid fallback (R2) defined
  for time overrun.

---

## Amendments to the constitution

_(none yet)_
