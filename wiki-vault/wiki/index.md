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
- [[urmi-mc-strength-damage40]] — extended219MP paired motion/Ds videos ready for0–2s; native stopped2.5s, exactnegative computationaldomainY captured; no solver active
- [[unnotched-mc-gravity]] — completed fine002; new requested40deg/Urmi-like soil MC strength-damage/longer run under development, no new solver yet; unused Joss prototype stopped
- [[unnotched-landslide-method-selection]] — primary journal methods for intact-slope failure; separate MC gravity/SSR control selected, no new full run or landslide claim
- [[wang2017-residual-history-scope]] —100mm history-guard failure, one replay with unchanged residual strength, explicit opt-in scope and native/integration gates
- [[wang2017-apex-60mm-review]] — complete61-state apex trial, no verified landslide;100mm input gate passed and same-material endpoint trial running13:52WIB
- [[wang2017-apex-flow]] — separate explicit volumetric apex model with passed native/regression gates; complete60mm slope reviewed without verified landslide
- [[wang2017-soil2-native]] —18 native and8 actual MPM/output controls PASS; full slope FAILED_NATIVE at08:26WIB, partial states retained
- [[wang2017-soil2-return-failure]] — one exact replay confirms no admissible coupled return;58saved states/media, no landslide; next tensile/apex model gate open
- [[wang2017-fast-trial-2026-10-24]] — complete native0.01m/s to60mm/6s,61states/video, no verified landslide;17native+11review artifact hashes; reference-speed600s remains NOT_RUN
- [[wang2017-apex-and-rate-study]] —5 native legacy/strict apex and3 rate-input controls PASS; interrupted0.002m/s data retained and completedfast010 rate comparison reviewed
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


- [[urmi-mc-proper-main]] � launched h1/PPC2x2 measured-preparation main trial; automatic filled motion/strength-damage movies pending

- [[urmi-mc-proper-main#Terminal28October01:59WIB]] - main001 failed undamped preparation hold; no dynamics/videos, saved diagnosis retained

- [[mc-hardening-softening-study#Native Mohr-Coulomb hardening and softening study]] - correction: user identifies residual clay; old sand label unsupported, source/case density distinction preserved

- [[mc-hardening-softening-study#Human-approved clay slope28October]] - active finer14010MP clay trial, human-approved peak initial/quarter residualstrength, filledmedia pending
