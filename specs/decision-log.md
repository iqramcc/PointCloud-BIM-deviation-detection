# Decision Log

Append-only. Each entry: date · context · decision · consequences. Open items (D1–D5) are
recommendations awaiting the project owner's ruling (Constitution, Art. X).

---

## Open decisions (awaiting owner)

### D1 — As-designed model source
- **Context:** the controlled experiments need an as-designed geometry with per-element
  labels and known deviations. Owner has Revit available.
- **Recommendation:** generate scenes **programmatically** (parametric meshes with element
  IDs) for all quantitative work — full control, reproducible, trivial per-element ground
  truth. Use a Revit-exported model only as an optional realistic scene in Phase 5.
- **Consequences if accepted:** Phase 1 starts immediately, no Revit dependency on the
  critical path.
- **Consequences if rejected (Revit-first):** Phase 1 blocks until an IFC/OBJ export with
  clean per-element separation is provided; ground-truth labelling becomes a manual mapping
  step.

### D2 — Deviation distance metric
- **Recommendation:** signed cloud-to-mesh (C2M) distance as default; M3C2 (Lague et al.
  2013) only if synthetic surfaces prove too noisy. 
- **Consequences:** simpler, faster; M3C2 kept as a `[C]` requirement (FR-3.11).

### D3 — Per-element aggregate
- **Recommendation:** signed **median** normal offset as primary; 95th-percentile absolute
  point distance as an ablation (Insight I4, tested in H4).
- **Consequences:** primary metric is robust to residual in-plane registration error; the
  ablation becomes a result, not just a check.

### D4 — Construction tolerance τ
- **Recommendation:** one documented default (proposed **10 mm** for structural elements,
  sourced from J. Building Eng. 2025 / code references), with a sensitivity sweep over
  {5, 10, 15} mm in Phase 4.
- **Consequences:** results are reported at one headline τ with a sensitivity panel.

### D5 — Experiment grid resolution
- **Recommendation:** freeze at the end of Phase 1 (Phase 1 SRS §5.4). Keep the
  registration-error axis dense (5 rotation × 5 translation levels); noise and occlusion
  coarse (3 levels each); 10 seeds/cell.
- **Consequences:** ~2 250 samples/scene, seconds each; reduced-grid fallback defined.

---

## Resolved decisions

_(none yet)_

---

## Amendments to the constitution

_(none yet)_
