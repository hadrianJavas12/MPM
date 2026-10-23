# Index

## Entities
- [[cl-mpm]] — the MPM code base, upstream and scope
- [[cl-mpm-studio]] — web UI for the cliff-collapse simulation

## Concepts
- [[cl-mpm-architecture]] — P0–P6 ownership migration and Section 2/5 physical directory alignment complete (`120/120` mapped owners, `src/` 15 engine subdirectories, `framework/` retired); Triaxial 2D and progressive bottom-to-top Joss cliff benchmarks PASS; G1/G3 partial
- [[windows-port]] — native Windows layout, overrides, gotchas
- [[serial-mpi-standin]] — `cl-mpm/mpi` replacement without MPI
- [[magicl-patches]] — patched vendored dependencies
- [[studio-custom-models]] — trusted CLOS law/editor/export contract and execution policy
- [[studio-modular-lisp-io]] — planned selective module .lisp I/O and complete preset portability (issue #5)
- [[studio-geometry-material]] — notch/base conventions, material controls and SI units

## Sources
- [[wang2017-mpm-return-2026-10-23]] — user replaces creep with Wang paper-input preparation and explicitly keeps MPM
- [[creep-drive-hold-study-2026-10-23]] — user continuation and explicit0.02m/s to0.1m driver then stationary hold; not paper/lab inputs
- [[creep-pusher-clarification-2026-10-22]] — user permits faster soil motion; communicated unilateral0.005m/s crest driver with release, no particle velocity floor
- [[clay-creep-duration-inputs-2026-10-22]] — user authorizes longer duration; speed/displacement can exceed earlier references
- [[clay-creep-design-2026-10-22]] — immutable creep request, explicit surrogate choices and assumed time/material inputs
- [[wang2017-reference-inputs-2026-10-22]] — immutable Wang et al. (2017) PDF identity, Table 1 and Figures 2–3 facts
- [[antigravity-native-history-2026-10-15]] — native runner color change and the supplied Joss damage clip that corrects the broader stress inference
- [[studio-hardening-2026-10-14]] — immutable hardening-session evidence and CI diagnosis
- [[joss-reference-inputs-2026-10-14]] — immutable paper/video identities, user clarification and author-example starting point

## Synthesis
- [[wang2017-apex-and-rate-study]] —5 native legacy/strict apex and3 rate-input controls PASS; unchanged-material0.002m/s rate study active
- [[wang2017-paper-history]] —19 coupled fixed-frame Soil2 point controls plus optional ASDF smoke PASS; existing17 history/7 capture/34 MC evidence retained; native particle and finite-strain convention pending
- [[clay-creep-slope]] —10s reviewed without verified landslide; complete release only9–10s; unchanged20s post-release observation running with strict prefix gate
- [[wang2017-prescribed-descent]] —17 history/7 capture/34 MC groups PASS; diagnostic FAILED/replayed, verified partial video0–15.4s available; Soil2 coupling and paper curve pending
- [[mc-hardening-softening-study]] — M0–M6 COMPLETE on `codex/mc-hardening-softening-study`: dedicated `:mc-h` / `:mc-hs` model family (`34/34` unit assertions), M3 constitutive point verification (`7` pairs), M4 3D MPM Triaxial (`T-100-H` vs `T-100-HS`, $-62.33\%$ post-peak softening drop), and M5 2D MPM Cliff (`L-H` vs `L-HS`, $+51.92\%$ max displacement, $+38.79\%$ toe runout) with plots and `.mp4` videos
- [[reusable-simulation-framework]] — canonical root ASDF (`cl-mpm-framework.asd`), Section 2/5 physical folder layout (`cases/{triaxial,cliff,benchmarks,direct-shear}/`), and post-alignment Triaxial 2D + bottom-to-top Joss cliff benchmarks exact PASS
- [[upstream-development-report-2026-10-15]] — professional Git-based comparison with original CL-MPM and linked evidence
- [[triaxial-clay-calibration]] — native 70 × 140 mm clay demonstration, computed curves and scientific limits; checkpoint PR #7 merged into main at efd0358
- [[scientific-authenticity-audit-2026-10-15]] — real-data/video derivation verified, numerical counterexamples and limits to scientific validity recorded
- [[refactor-2026-10-14]] — decisions and results of the Windows-port refactor
- [[studio-verification-2026-10-14]] — native Windows/Studio/export parity, observed fixes, historical evidence and remaining scientific/CI gates
- [[joss-reference-reproduction]] — experimental reference path, visually accepted actual DP collapse, preserved evidence and quantitative limits in D:\MPM
- [[joss-reference-reproduction#Workspace and latest state, 2026-10-15|Windows native rerun guide]] — fresh-start config, command-line run, VTK rendering and checks in docs/RUN_ACCEPTED_COLLAPSE_WINDOWS.md
- [[joss-damage-diagnosis-2026-10-15]] — accepted 40 s DP collapse/run-out, measured mismatch, completed no-collapse 40 kPa case and paused continuation
