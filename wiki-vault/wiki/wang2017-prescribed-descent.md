---
title: Wang 2017 prescribed crest descent
type: synthesis
tags: [wang2017, benchmark, mpm, mohr-coulomb, native-windows]
sources: [research/references/wang2017/source.json, research/references/wang2017/mpm-reference-contract.json, docs/benchmarks/WANG2017_MPM_PREPARATION.md, docs/benchmarks/WANG2017_SLOPE_DESCENT.md, raw/wang2017-reference-inputs-2026-10-22.md, raw/wang2017-mpm-return-2026-10-23.md]
updated: 2026-10-23
---

# Wang 2017 prescribed crest descent

Current scope: [[wang2017-mpm-return-2026-10-23]] explicitly keeps MPM and follows
paper physical inputs on `codex/wang2017-reference-preparation`. The earlier
Soil1 pilot on the Wang branch remains historical evidence. The full paper curve
is **NOT_RUN**; no J2 creep case is substituted.

Reference inputs are 20 m width, 5 m base, 60° slope, 7 m crest before the 3 m loaded patch (x=7–10 m), unit weight 20 kN/m³, E=20 MPa, nu=0.25, c=30 kPa, phi=35°, psi=0°. **Slope relief 10 m is an implementation assumption**, because the paper gives no numerical relief height. The crest target speed is 1e-4 m/s.

The workflow settles gravity, resets the descent displacement/time origin and velocity while preserving prestress and consistent internal state, then applies penalty-driven downward crest motion. Target platen motion and measured soil motion/reaction must be reported separately. The full target 0.1 m requires 1,000 s physical time; mass/time scaling remain 1. A short pilot cannot establish a complete force–displacement comparison.

This explicit MPM approximation does not implement the paper's FEM local arc-length scheme. Soil#2 softening remains deferred; paper kps needs an explicit mapping to native kappa. No digitized curve, fitting, scientific validation or numerical agreement percentage is claimed. See [[scientific-authenticity-audit-2026-10-15]] and [[mc-hardening-softening-study]] for related limits.

Reproducible Windows commands and acceptance evidence are maintained in `docs/benchmarks/WANG2017_SLOPE_DESCENT.md`; factual provenance is in `research/references/wang2017/source.json`.

## Pilot evidence

915 MPs; 3,425 gravity and 3,440 loading updates; 11 VTKs; target 0.1 mm,
measured mean 0.0992383 mm; final reaction 1.09678 kN/m; mass error zero.
Saved-output consistency passes. Native controls 8, framework 10 and Node 36 pass.
Initial reaction transients are retained, so quasi-static curve agreement is not
verified. Full 0.1 m target would take 1000 physical seconds, estimated about
2.35 wall days at pilot throughput. The user subsequently authorized a fast trial.
Evidence and complete commands are linked from the maintained benchmark guide.

## Accelerated trial checkpoint

User-requested0.005 m/s targets0.1 m in20s (50x reference), with unchanged
Soil#1/geometry/mass scale. The actual native run launched12:32 WIB on2026-10-22
from52f9367: `output/wang2017-fast-2026-10-22/fast-005-001/`.
Actual outcome: **FAILED_NATIVE**, exit1 at13:30 WIB, about58 wall minutes.
Gravity converged; last saved loading state15.4s, command77mm and measured76.518656mm
of100mm. The MC integrator found no admissible coupled active-set solution.
There are78 loading VTKs; last saved mass error0 is not an independent full audit.
Force/energy CSVs are absent after abnormal exit; no complete curve or energy PASS
is claimed.10 artifact hashes retain source, logs and remaining raw output under
`docs/evidence/wang2017-descent-2026-10-22/fast-005-001-failure/`.

Four new native controls and Node36/check passed; do not repeat unchanged tests.
Energy diagnostics are observational proxies, not a closed energy budget;
prestress can hide kinetic significance. Review raw signed reactions, tracking,
conservation, finite fields and stability before the separately authorized slower
0.002 m/s comparison. Preserve source/data and report actual failures.
See [[scientific-authenticity-audit-2026-10-15]] and the benchmark guide.

Historical next-gate note: exception-safe history retention has since been fixed
and tested. Exact failed-state capture/replay remains open; the slower full run
remains NOT_RUN. Do not repeat a full trial just to rediscover the failure.

## Current preparation,2026-10-23

The Windows `scripts/prepare-wang2017.ps1` command passes7 native construction/
configuration groups,35 input comparisons and Nodecheck/36 tests on7319e42.
Two native MC particles constructed, zero physical/settling updates.18 hashes
retain actual exports, law samples, logs and inputs. Numerical engine sources
are unchanged from59a564b. Preparation is not a newly simulated curve.

Central contract distinguishes Soil1/Figure3 perfect plastic from Soil2/Figure4
cohesion30→15kPa over paperkps0→.02. Eq5 is the deviatoric plastic-tensor norm;
native cumulative J2 increments are not automatically equivalent. Soil2 adapter
is pending. No guessed .02 native-kappa case is provided.

Paper author-upload text was re-read via web; original PDF path is missing and
new figure-image inspection unavailable. Relief10m, bottom tangential fixity
and0.1m endpoint remain explicit assumptions/unresolved items. The public source
and exact open gates are in docs/benchmarks/WANG2017_MPM_PREPARATION.md.

## Paper-history checkpoint,2026-10-23

[[wang2017-paper-history]] records the new isolated Eq5–6 tensor state/cohesion
module and MC failure capsule/replay. Source db71b63 passes17 history,7 capture
and34 legacy MC material-point groups in actual Windows native execution.
No new Soil2 particle or full reference curve has run. Successful legacy MC
equations/tolerances remain unchanged; missing historical failed J remains missing.
