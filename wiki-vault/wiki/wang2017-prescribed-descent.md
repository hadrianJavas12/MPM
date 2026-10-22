---
title: Wang 2017 prescribed crest descent
type: synthesis
tags: [wang2017, benchmark, mpm, mohr-coulomb, native-windows]
sources: [research/references/wang2017/source.json, docs/benchmarks/WANG2017_SLOPE_DESCENT.md, raw/wang2017-reference-inputs-2026-10-22.md]
updated: 2026-10-22
---

# Wang 2017 prescribed crest descent

Scope: Soil#1 elastic-perfectly plastic slope from [[wang2017-reference-inputs-2026-10-22]], prepared on `codex/wang2017-prescribed-descent` using the [[reusable-simulation-framework]]. Native execution evidence is **NOT_RUN** at this documentation checkpoint.

Reference inputs are 20 m width, 5 m base, 60° slope, 7 m crest before the 3 m loaded patch (x=7–10 m), unit weight 20 kN/m³, E=20 MPa, nu=0.25, c=30 kPa, phi=35°, psi=0°. **Slope relief 10 m is an implementation assumption**, because the paper gives no numerical relief height. The crest target speed is 1e-4 m/s.

The workflow settles gravity, resets the descent displacement/time origin and velocity while preserving prestress and consistent internal state, then applies penalty-driven downward crest motion. Target platen motion and measured soil motion/reaction must be reported separately. The full target 0.1 m requires 1,000 s physical time; mass/time scaling remain 1. A short pilot cannot establish a complete force–displacement comparison.

This explicit MPM approximation does not implement the paper's FEM local arc-length scheme. Soil#2 softening remains deferred; paper kps needs an explicit mapping to native kappa. No digitized curve, fitting, scientific validation or numerical agreement percentage is claimed. See [[scientific-authenticity-audit-2026-10-15]] and [[mc-hardening-softening-study]] for related limits.

Reproducible Windows commands and acceptance evidence are maintained in `docs/benchmarks/WANG2017_SLOPE_DESCENT.md`; factual provenance is in `research/references/wang2017/source.json`.
