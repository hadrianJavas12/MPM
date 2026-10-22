---
title: Experimental clay creep slope
type: synthesis
tags: [creep, clay, slope, viscoplasticity, native-windows]
sources: [raw/clay-creep-design-2026-10-22.md, docs/benchmarks/CLAY_CREEP_SLOPE.md, docs/evidence/slope-creep-2026-10-22/controls/summary.json]
updated: 2026-10-22
---

# Experimental clay creep slope

The user requested creep toward landslide, recorded in
[[clay-creep-design-2026-10-22]]. Branch `codex/slope-creep-landslide` adds a
separate sustained-self-weight scenario to the [[reusable-simulation-framework]].
The crest is free; no commanded descent/failure trajectory drives motion.

Material: phi_u=0 total-stress clay surrogate with J2 Perzyna overstress and
strength loss driven by accumulated equivalent creep strain. Kirchhoff yield
and viscosity, compressible nu.25 and no pore-fluid coupling are explicit.
No subyield or primary creep, laboratory calibration, mesh independence or
Wang MC equivalence is established. See [[wang2017-prescribed-descent]] for the
separate failed MC trial; changing material does not solve its numerical defect.

Windows native13 material/4 history/2 scenario controls and Node36/check passed
at33eed96. The held-stress point curves show continued creep and accelerating
strain under softening; they are actual point updates, not a slope result.
19 artifact hashes retain those tests, CSVs, PNG and negative manifest.

Pilot001 failed on a vector/list mismatch in crest measurement, not the material
law.10 hashes preserve that failure.7be4503 fixes sequence handling;3 expanded
scenario controls passed, with5 hashes in `crest-sequence-regression/`.
Actual replacement1s pilot launched18:24 WIB on2026-10-22 from7be4503:
`output/slope-creep-2026-10-22/pilot-002/`, wrapperPID34608,
Completed18:27 WIB, native/audit/render exit0,1s/11VTKs,915MPs, zero mass drift,
minJ0.98696. Crest descent11.9218mm, max displacement13.4915mm, kappa_max0.00246253,
minimum yield dropped19.7%.14 artifact hashes retain actual source/data/media.
This is an operational pilot, not verified landslide/acceleration: activation
transients cause velocity/kinetic oscillations, while max creep rate decreases.

The same-material30s case launched19:24 WIB froma9c3e30:
`output/slope-creep-2026-10-22/hold-30s-001/`, wrapper50876,4h native budget.
Quiet status-first continuation starts20:00 WIB. Review actual plots/video and
localization/run-out after completion; no duplicate computation or tuned timeline.

Source/commands/assumptions are in `docs/benchmarks/CLAY_CREEP_SLOPE.md`;
linked integrity and evidence practices: [[scientific-authenticity-audit-2026-10-15]].
