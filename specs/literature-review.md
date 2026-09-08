# Literature Review & Gap Analysis

**Status:** Draft v0.1 · **Last updated:** 2026-09-08
**Purpose:** establish what has already been done, isolate the gap this project fills, and
record the design-relevant findings each phase SRS will cite.

> Living document (Constitution, Art. VII). Add relevant work as it is found; do not remove
> entries. Insights authored by the project team are marked **[Insight]** and are hypotheses
> to be tested, not established facts.

---

## 1. Framing: Scan-vs-BIM

Two distinct problems are often confused:

- **Scan-to-BIM** — *reconstruct* a BIM model from a point cloud.
- **Scan-vs-BIM** — *compare* a point cloud against an existing as-designed BIM to verify
  construction. **This project is Scan-vs-BIM.**

Scan-vs-BIM has two operations that are almost always treated as a pipeline of independent
steps:

1. **Registration** — bring the scan into the BIM coordinate frame (coarse/global alignment
   followed by fine/local refinement).
2. **Deviation analysis** — compute geometric differences and flag what exceeds tolerance.

The project's thesis is that **step 2 inherits the unquantified error of step 1**, and that
this coupling has not been measured.

---

## 2. Registration of point clouds to BIM

| Work | Approach | Relevance |
|---|---|---|
| Rusu et al., *FPFH* (ICRA 2009); Open3D global-registration tutorial | Generic feature (FPFH) + RANSAC global alignment, then ICP | Defines **Baseline A**; reference parameters and implementation exist in Open3D |
| Besl & McKay 1992; Chen & Medioni 1992 (point-to-plane ICP) | Fine registration by iterative closest-point | Shared refinement stage for both baselines |
| Bosché, *Plane-based registration of construction laser scans with 3D/4D building models* (Univ. Edinburgh); ISARC *Plane-Based Coarse Registration of 3D Point Clouds with 4D Models* | Extract planes from scan and model, match (semi-automatically), then ICP | Direct precedent for **Baseline B**; plane matching is the known hard part |
| Bueno et al., *4-Plane congruent sets for automatic registration of as-is 3D point clouds with 3D BIM models*, Automation in Construction (2018) | Fully automatic plane-based coarse registration + refinement; reports rotation/translation accuracy | Template for an automatic plane matcher and for reporting metrics |
| *Global BIM–point cloud registration and association for construction progress monitoring*, Automation in Construction (2024) | Recent coarse-to-fine BIM registration + per-element association | Method for per-element association used in deviation aggregation |
| *Align to locate: Registering photogrammetric point clouds to BIM for robust indoor localization*, Building and Environment (2022) | Photogrammetric cloud → BIM registration | Confirms the generality of the coarse-to-fine pattern |
| *Speak the Same Language: Global LiDAR Registration on BIM Using Pose Hough Transform*, arXiv 2405.03969 (2024) | Non-classical global registration | Out of scope; noted for completeness |

Links: <https://www.open3d.org/docs/release/tutorial/pipelines/global_registration.html> ·
<https://www.iaarc.org/publications/fulltext/S14-1.pdf> ·
<https://www.research.ed.ac.uk/en/publications/plane-based-registration-of-construction-laser-scans-with-3d4d-bu/> ·
<https://www.sciencedirect.com/science/article/abs/pii/S0926580517301620> ·
<https://www.sciencedirect.com/science/article/abs/pii/S0926580524005326> ·
<https://www.sciencedirect.com/science/article/abs/pii/S0360132321010659>

**Takeaway:** both baselines are established methods with reference implementations. The
project implements neither from scratch conceptually; Baseline B's plane *matcher* is the
only substantial custom component, and a semi-automatic fallback (2–3 seeded plane matches)
is documented precedent.

---

## 3. Deviation / discrepancy analysis

| Work | Contribution | Relevance |
|---|---|---|
| **Anil, Tang, Akinci, Huber**, *Deviation analysis method for the assessment of the quality of the as-is BIM generated from point cloud data*, Automation in Construction (2013); SPIE 2011 precursor | Align cloud to BIM, compute point-to-surface distances, produce color-coded deviation maps, classify deviations | **Canonical reference.** States explicitly that **modeling error and registration error cannot be separated** in the deviation map — the exact confound this project targets |
| *Point-to-point Comparison Method for Automated Scan-vs-BIM Deviation Detection* | Column-based automatic registration + point-to-point comparison; discusses false positives from association thresholds | Shows FP behaviour is threshold-sensitive |
| *Verification of Building Structures Using Point Clouds and Building Information Models*, Buildings 12(12):2218 (2022) | Derives a registration error from alignment accuracy + instrument specs via error-propagation law, then performs deviation checking | **Closest existing work** to "registration-error-aware" deviation analysis — but it neither sweeps registration error nor measures detection precision/recall |
| *Intelligent detection method for construction quality of building structures based on point cloud data and BIM models*, J. Building Engineering (2025) | Inspection indicators: dimensional accuracy, surface quality, flatness, verticality | Source of realistic tolerance values and per-element metrics |
| Lague et al., *M3C2* (ISPRS 2013); CloudCompare C2M | Robust cloud-to-mesh / cloud-to-cloud distance | Candidate distance computation; C2M signed distance is the project default |
| buildingSMART use case *Geometrical verification of as-built BIM models by deviation analysis* | Industry workflow, tolerances, corrective actions | Framing and practitioner relevance |

Links: <https://www.sciencedirect.com/science/article/abs/pii/S0926580513001003> ·
<https://publications.ri.cmu.edu/storage/publications/pub_files/2011/1/2011-anil-spie-qa-final.pdf> ·
<https://www.researchgate.net/publication/325813565_Point-to-point_Comparison_Method_for_Automated_Scan-vs-BIM_Deviation_Detection> ·
<https://doi.org/10.3390/buildings12122218> ·
<https://www.sciencedirect.com/science/article/abs/pii/S2352710225017292> ·
<https://ucm.buildingsmart.org/en/use-cases/2970/en>

**Takeaway:** the deviation-analysis pipeline (signed distance → per-element aggregate →
tolerance flag → heatmap) is standardized. Anil et al. name the registration/modeling
confound as a known, unaddressed limitation.

---

## 4. Registration accuracy, uncertainty, and downstream effects

| Work | Contribution | Relevance |
|---|---|---|
| *Evaluation of point cloud registration using Monte Carlo method*, Measurement (2016) | Propagates registration uncertainty by Monte Carlo simulation | Methodological template for the error-injection experiment |
| *A Quantitative Investigation of the Effect of Scan Planning and Multi-Technology Fusion … on Registration and Data Quality*, Buildings 13(6):1473 (2023) | Studies drivers of registration error and overlap | Establishes realistic registration-error magnitudes; does **not** connect them to defect detection |
| *Point cloud quality requirements for Scan-vs-BIM based automated construction progress monitoring* | Relates point-cloud quality to Scan-vs-BIM decision reliability | Same spirit as this project, but for **progress** (occupancy) detection, not dimensional deviation |
| *BIM-Constrained Optimization for Accurate Localization and Deviation Correction in Construction Monitoring*, arXiv 2504.17693 (2025) | Notes that within-tolerance deviations get absorbed as drift and match rates stay high | Independent statement of the registration/defect confound, framed for SLAM |

Links: <https://www.sciencedirect.com/science/article/abs/pii/S0263224116303116> ·
<https://doi.org/10.3390/buildings13061473> ·
<https://www.academia.edu/87985034/Point_Cloud_Quality_requirements_for_Scan_vs_BIM_based_automated_construction_progress_monitoring> ·
<https://arxiv.org/pdf/2504.17693>

**Takeaway:** registration uncertainty is studied *in isolation*; its propagation into
dimensional deviation-detection precision/recall is not quantified anywhere found.

---

## 5. Synthetic data and benchmarks

| Work | Contribution | Relevance |
|---|---|---|
| Noichl et al., *"BIM-to-Scan" for Scan-to-BIM: Generating Realistic Synthetic Ground Truth Point Clouds*, EC3 (2021) | Strategy for generating realistic synthetic scans with exact ground truth from 3D models | Direct support for the synthetic-primary data strategy |
| *SynBench: A Synthetic Benchmark for Non-rigid 3D Point Cloud Registration*, arXiv 2409.14474 (2024) | Controlled deformation, noise, outliers, incompleteness with GT correspondences | Template for parameterising perturbations (non-rigid focus; not reused directly) |
| *Dataset and benchmark for as-built BIM reconstruction from real-world point cloud*, Automation in Construction (2025) | Notes the field-wide shortage of BIM-as-ground-truth datasets and domain metrics | Justifies building our own synthetic benchmark |
| Mendeley Data `pssxxtjyyf`, *Point Cloud Registration Dataset for Comparative Scan-to-BIM Assessment (ReCap Pro vs CloudCompare)* (2026) | Faro Focus scan of a steel structural frame, openly licensed | Candidate **qualitative** real-data demonstration |

Links: <https://ec-3.org/publications/conferences/EC32021/papers/EC32021_166.pdf> ·
<https://arxiv.org/abs/2409.14474> ·
<https://www.sciencedirect.com/science/article/abs/pii/S0926580525001360> ·
<https://data.mendeley.com/datasets/pssxxtjyyf/1>

**Takeaway:** synthetic generation from a parametric model, with injected transforms / noise
/ occlusion, is an accepted methodology and is the only way to obtain *simultaneous* ground
truth for registration error and for true deviations.

---

## 6. The gap

Across §2–§5:

1. The confound "a flagged deviation may be registration error, not a real defect" is
   **named as a known limitation** (Anil et al. 2013; arXiv 2504.17693) but is treated as a
   caveat, never as the object of study.
2. Registration papers report rotation/translation error. Deviation papers report deviation
   maps or classification accuracy. **No work found connects the two quantitatively** — i.e.
   "at *r*° / *t* mm registration error, deviation-detection precision falls to *p*, recall
   to *q*, with this spatial pattern of false flags."
3. No work compares registration **front-ends** (plane-based vs point-based) on the basis of
   *downstream deviation-detection reliability* rather than alignment RMSE alone.
4. No published "registration budget": the alignment accuracy required to detect defects
   reliably at a stated construction tolerance.

**This project delivers a reproducible characterization of (2)–(4) on controlled synthetic
data.** It introduces no new registration algorithm; the novelty is the coupling analysis.

---

## 7. Design-relevant insights (project team)

- **[Insight I1 — spatial signatures]** A residual *rotational* registration error produces
  a deviation-error field whose magnitude grows ~linearly with distance from the alignment
  centroid; a residual *translational* error produces a spatially uniform deviation bias.
  Prediction: rotational error yields edge-concentrated false positives and disproportionately
  harms large scenes; translational error yields whole-element sign-consistent bias.
  *Tested in Phase 4 (FP/FN spatial analysis).*

- **[Insight I2 — why plane-based should help, central hypothesis]** Plane-based registration
  constrains exactly the degrees of freedom that dominate planar-element deviation (offset
  along the surface normal), while leaving in-plane sliding loosely constrained. Deviation
  analysis of walls/slabs *measures the normal offset*. Therefore Baseline B may degrade more
  gracefully in **normal-direction detection** than its global RMSE suggests, and more
  gracefully than Baseline A. *This is the falsifiable core of the research question.*

- **[Insight I3 — the registration budget, the actionable output]** When registration RMSE
  approaches the construction tolerance τ (typically 5–15 mm for structural elements),
  detection F1 collapses toward chance. The most useful deliverable is the inverse map: for a
  given τ, the registration accuracy required for F1 ≥ 0.9. This converts a method comparison
  into practitioner guidance.

- **[Insight I4 — aggregation interacts with registration error]** A *signed median normal
  offset* per element should be more robust to registration error than a max or 95th-
  percentile point distance, because registration error tangential to a plane barely changes
  the normal offset. The choice of per-element aggregate may therefore change the coupling
  curve — worth a small ablation in Phase 4.

- **[Insight I5 — synthetic-only is the correct choice here, not merely a convenience]** Real
  data cannot provide ground-truth registration error and ground-truth deviations
  simultaneously (measuring one contaminates knowledge of the other). Synthetic data is the
  only setting where the coupling curve is definable. The real scan's role is to show the
  pipeline runs end-to-end, not to validate the curve — and the report must say so.

---

## 8. How each phase uses this review

| Phase | Cites |
|---|---|
| 1 — Synthetic data | Noichl et al. 2021; SynBench 2024; Buildings 2023 (realistic error magnitudes); tolerance values from J. Building Eng. 2025 |
| 2 — Registration | Open3D tutorial + Rusu 2009 (Baseline A); Bosché, Bueno et al. 2018 (Baseline B); point-to-plane ICP |
| 3 — Deviation detection | Anil et al. 2013; Lague et al. 2013 (M3C2); buildingSMART use case; tolerance values |
| 4 — Experiment & coupling | Monte Carlo (Measurement 2016); Anil et al. 2013 (confound statement); Insights I1–I4 |
| 5 — Evaluation & reporting | as-built benchmark gap (Automation in Construction 2025); Insight I5 |
