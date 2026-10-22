---
title: Experimental clay creep slope
type: synthesis
tags: [creep, clay, slope, viscoplasticity, native-windows]
sources: [raw/clay-creep-design-2026-10-22.md, raw/clay-creep-duration-inputs-2026-10-22.md, raw/creep-pusher-clarification-2026-10-22.md, docs/benchmarks/CLAY_CREEP_SLOPE.md, docs/evidence/slope-creep-2026-10-22/hold-120s-001/review.json]
updated: 2026-10-23
---

# Experimental clay creep slope

The user requested creep toward landslide, recorded in
[[clay-creep-design-2026-10-22]]. Branch `codex/slope-creep-landslide` adds a
separate sustained-self-weight scenario to the [[reusable-simulation-framework]].
The completed gravity-only runs have a free crest; no commanded descent/failure
trajectory drives that motion. A later unilateral-pusher experiment passed a
bounded dynamic-release pilot and remains distinct from those completed results.

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

The same-material30s case froma9c3e30 completed19:39 WIB:
`output/slope-creep-2026-10-22/hold-30s-001/`, native/audit/render exit0,
61VTKs/915MPs, zero mass drift,minJ0.97840. Crest descent260.8326mm,max298.1695mm,
kappa_max0.0582425.16 verified artifact hashes retain source/data/proofs/media
and independent review. No active solver remains.

Update: the user subsequently requested longer duration, recorded in
[[clay-creep-duration-inputs-2026-10-22]]. New120s/241state case preserves0.5s
cadence and all physical/solver parameters (native config comparisoncfc65e9 PASS,
5 retained hashes). Historical0.005m/s /0.1m are not caps; no artificial minimum
particle motion is imposed. Job `hold-120s-001` launched21:38 WIB fromcfc65e9,
wrapper4680,4h budget. It completed native exit0/complete=true at22:31 WIB,
audit/render exit0 at22:33 WIB. Restart support is absent, so it recomputed from
the same initial conditions. Strict prefix regression PASS:64 baseline VTK files
(including mesh/gravity) and first61 CSV states are byte-identical; physical
configuration and0.5s cadence match. Do not repeat the run or comparison.

120s/241states/915MPs have finite saved history, zero mass drift, minimum J0.97467,
crest settlement0.92059m, maximum displacement1.17041m, kappa_max0.274855.
18 artifact hashes retain source/native proof/output/media, strict comparison,
independent review and material-capability analysis in hold-120s-001.

**Creep-to-landslide NOT_VERIFIED**: distributed creep/toe-base strain without
detached mass or run-out. Beyond30s, raw crest secant rates decline8.079/7.314/
6.600mm/s across30–60/60–90/90–120s. Residual strength is reached locally at5.5s.
Completion is not calibration or failure validation. No strength/viscosity tuning
was performed. Separate analytical0D fixed-stress reasoning gives constant
`kappa_dot=(q-Yr)/eta` after residual strength; illustrative assumed stresses are
not full-MPM or laboratory measurements. Geometry/stress redistribution can
still change coupled slope behavior; more duration alone does not guarantee failure.

The latest clarification [[creep-pusher-clarification-2026-10-22]] was communicated
as a crest driver moving at0.005m/s with compression-only contact: soil may
outrun the driver and release. This is a new loading experiment, with the same
assumed clay law and no particle velocity floor, position overwrite or scheduled
collapse. It is not a fix for Wang MC. The tracked crest/finite-penalty contact
approximation needs explicit force/gap/release/work diagnostics and limitations.
Implementation ec285c0 passes actual Windows6 contact/3 scenario controls and
Node check/36 tests, with19 artifact hashes in pusher-controls-001. The0.02m/s
control verifies separated geometry and velocity non-mutation; separate native
pilot evidence now demonstrates dynamic release. The fixed original contacts have no new
surface search, and frame-level force/gap CSV is not integrated actuator work.

Two1s/11-state jobs launched23:22 WIB on2026-10-22, both ec285c0 /1h budget:
gravity-compat-001 (wrapper19844) and pusher-pilot-001 (wrapper30008) under
output/slope-creep-2026-10-22. Both are complete and no active jobs remain.
Gravity compatibility completed native/audit/render exit0:
strict14 VTK/all11 CSV states byte-identical to pilot-002, same config/cadence,
15 retained artifact hashes. Do not repeat that comparison or solver.
Pusher pilot completed23:27 WIB, native/audit/render exit0,1s/11states/915MPs,
zero mass drift. Actual patch settlement10.07815mm exceeds the5mm driver command;
max displacement13.24341mm and max speed0.0520888m/s. At the0.1s saved sample,
all6 contacts are active with upward reaction3616.041N/m and maximum compression
gap22.419micrometres. Every saved0.2–1.0s sample has0 active/6 unloaded contacts
and zero reaction; no claim is made about every intermediate timestep.
Source/native data/proof/media/review are retained under
`docs/evidence/slope-creep-2026-10-22/pusher-pilot-001/`.
**Dynamic release PASS; landslide NOT_VERIFIED; full120s pusher NOT_RUN.** The
slow driver loses contact because soil descends faster; no automatic longer run
or material tuning is justified by this result alone. This bounded proof is not
laboratory calibration, general contact validation or an integrated work audit.

Source/commands/assumptions are in `docs/benchmarks/CLAY_CREEP_SLOPE.md`;
linked integrity and evidence practices: [[scientific-authenticity-audit-2026-10-15]].

## Continued drive/hold study,2026-10-23

[[creep-drive-hold-study-2026-10-23]] records continuation and declared experiment:
0.02m/s driver to0.1m at5s, then stationary until10s; material/geometry unchanged,
soil free.15 actual native controls pass on733996a, Nodecheck/36 on462f519;
26 hashes retain controls, initial namespace failure and qualification-only fix.
Actual drive-hold-001 launched04:36 WIB, wrapper38064/native1512,1h budget,
source733996a. Read adjacent status; outcome pending. Command work is a per-step
right-end rectangle estimate, not a closed budget. After completion inspect
ID-aligned above-base downslope motion during hold, work/contact/mass/J and
morphology. Fixed bottom/side rollers limit basal sliding/eventual run-out;
internal shear remains possible. No failure claim, forced contact or tuning.
