---
title: Joss Bay reference reproduction
type: synthesis
tags: [joss-bay, studio, common-lisp, reference, validation]
sources: ["[[joss-reference-inputs-2026-10-14]]", docs/REFERENCE_REPRODUCTION.md, docs/evidence/joss-collapse-2026-10-15/README.md, examples/chalk/joss.lisp, studio/lisp/reference-joss.lisp]
updated: 2026-10-15
---

# Joss Bay reference reproduction

## Workspace and latest state, 2026-10-15

The Windows-native rerun guide is `docs/RUN_ACCEPTED_COLLAPSE_WINDOWS.md`, with
fresh-start configuration `studio/reference/joss-bay-accepted-collapse.json`.
It retains the accepted pilot's geometry/material/40 s target, but recomputes
elastic equilibrium (cap 3000, tolerance 1e-4) instead of reusing a live SBCL
state. Canonical-schema round trip passed; full fresh replay is not yet proved
identical. The user now requests a scientific/authenticity audit after delivery
of this guide. This is not a request for additional visual calibration.

The active checkout is `D:\MPM`; `MPM-test` is no longer used. The former root
checkout and its local changes are preserved under
`.workspace-backup/before-flatten-20261015-0432`. Forty-one changed/untracked
source files retained their hashes, and the relocated Windows bootstrap passed.
The earlier pilot stopped for relocation; the raw candidate produced upper-face
damage at t=111 s. The later actual native DP pilot completes 40 s/174 frames
with lower-face damage and collapse/run-out. **The user accepted this visual
collapse result and requested a commit**, after viewing its video and the later
40 kPa image. Its measured reference mismatch remains: run-out +7.8 m, plateau
edge −5.2 m and image occupancy IoU 0.699825 against reference final 221.14 s.
This is an approximate image comparison at different times, not numerical or
scientific validation. The 40 kPa candidate completed 221.14 s/111 frames without
collapse (max damage 0.49062952033, mass-weighted damage 0.008064637675).
No further calibration is requested; the continuation heartbeat is **PAUSED**.
[[joss-damage-diagnosis-2026-10-15]] records the actual evidence and stopping point.
`docs/evidence/joss-collapse-2026-10-15/README.md` indexes the accepted media,
separate 40 kPa image, configs, CSVs, metadata, audits, provenance and actual
test logs. The accepted pilot used a saved strict-equilibrium warm start; a fresh
production CLI replay is a separate provenance claim. Commit `8fba2b7`
uses a different 100 m example and defaults to stress coloring; its bounded
compatibility run did not establish a basal crack. Consult [[studio-verification-2026-10-14]]
for the separate completed integration checks.

[[antigravity-native-history-2026-10-15]] recovers the user's prior native run:
the old red base followed a switch from damage to Von Mises stress plotting.
That history supports the native-first/UI-later workflow, but does not establish
a previously validated basal fracture or Joss Bay collapse.

The user's later WhatsApp clip is different: it labels damage0–1 on a31 m
Joss-shaped case, with a clear lower-face colored patch at15.87 s and red by
19.83 s. It corrects the broader stress-color inference. Its exact source run
and chronology remain unproved; the earlier D:\model Joss runner/renderer are
the next leads. See the correction in [[antigravity-native-history-2026-10-15]].

The user clarified that the target is similar cliff geometry, crack progression,
collapse and run-out from the supplied paper/video, not numerical identity.
They asked to build from `examples/chalk/joss.lisp`; the research dataset is not
required. Immutable input identities and request scope:
[[joss-reference-inputs-2026-10-14]].
The latest instruction prioritizes actual simulation results and defers new
reference UI controls. Their patch is preserved in the local evidence directory;
the current path is CLI/library profiles.

The dedicated `joss-bay` scenario in [[cl-mpm-studio]] adapts the example's
geometry/material/phases into a bounded runner, keeping the ordinary
`studio-cliff` path. New reference methods/classes isolate parameter and angular
unit handling from the generic chalk defaults. Source/example and published
configuration differ, so provenance remains explicit.

## Reference profiles

`studio/reference/joss-bay-prose.json` uses E1GPa from paper section 6.1;
`joss-bay-table.json` exposes E100MPa from Table 5. The latter is an explicit
sensitivity variant, not a resolved erratum. Shared setup is15.5 m cliff/1 m base,
78 degree lower slope,6.8 m upper vertical segment,45degree0.5 m notch, h1/6 m,
3x3 bulk MPs/cell, and up to four boundary bisections. The6.8 m upper height and
beach aspect 1 are from the author example/video, not dimensioned paper values.

Chalk parameters:rho1700kg/m3,nu0.24,damage cohesion 26kPa/friction 50degrees,
plastic cohesion 26x75.6 kPa/friction 50degrees/dilatancy0, Gf48J/m2,R0.5 m,
delay 10s/exponent2 and tensile/compressive/shear degradation1/0/0.51.
The tensile initiation derived from the engine conversion is18,926.452 Pa.
Using explicit Eq.(44) helper factor k1 gives ductility 535.99755 for1GPa,
and Eq.(57) gives oversize 75.64918, supporting the prose candidate. Actual
source-run identity is not claimed.

Separate CLI `joss-bay-video-candidate.json` keeps E1 GPa/R0.5 m, uses Gf4.8
J/m2, ductility53.59975506 and target title time221.14 s. The active example
and Fig.16 lower-Gf case have timing closer to the video, but that is inference,
not identified original parameters. The baseline48 J/m2 profiles and explicit
plastic cohesion remain preserved; the candidate is not added to the UI/API
catalogue and must pass initial equilibrium before interpreting a collapse.

## Phases and result boundaries

Initial elastic self-weight equilibrium disables plasticity and damage. Failure
to converge within a configured cap is reported, then no fracture run is started.
After equilibrium, reset the fracture clock, enable cliff material evolution and
reduce damping. Index-1 foundation/beach keeps damage and plasticity disabled.
Reference-only damage driving now uses author Joss DP with stored radian friction;
ordinary chalk defaults are unchanged. Accelerate uses mass scale10,000;
collapse uses1. The0.01 energy/work
and OOBF criteria switch states; returning to accelerate resets work and velocity.
Physical check/output intervals are1s and 0.1 s respectively.

The runner writes VTK/PNG, time/phase/mass/damage CSV, transitions and
`reference-metadata.json`. Reaching a frame cap is unfinished; `complete` only
means requested physical time was reached. It does not establish physical
validation. The actual pilot's visual collapse is now accepted; quantitative
calibration and mesh convergence remain unverified, with no further work requested.
The initial coarse/loose-convergence smoke is distinct from the strict pilot.
The 0.5 m, two-MPs-per-axis, physical-mass pilot was interrupted during
nonconverging elastic equilibrium after more than 37,000 updates; no completed
crack/collapse trajectory or final metadata was obtained. Full-resolution initial
geometry exists, but its gnuplot timeout and separate scientific initial render
do not establish a simulated failure sequence.

Corrected volume-weighted diagnostics and the factor-two/grid-size damping
conversion subsequently converged the F-bar-on 0.5 m equilibrium at update
3,898 with strict 1e-4 criteria and no damage. Metadata explicitly records a
weighted L2 force norm adaptation to the paper's ambiguous Eq.(67). Fresh Node
contracts passed 36/36; ordinary and custom-delegate native smokes passed. Fine
initial geometry has 82,351 MPs and mass 425,920.5054 kg/m. A two-update cache
comparison found exact equality across 37 fields for 4,155 MPs; it is parity
evidence rather than a speed claim. The lower-Gf raw trajectory was subsequently
stopped at t=111 s after localized upper-face damage without the target collapse.
The later native-aggregation preparation check converged in 1658 updates;
same-state DP/MC comparison and the completed 40 s physical DP pilot are now
captured in [[joss-damage-diagnosis-2026-10-15]]. The lower DP drive is 50.409 kPa
versus MC 16.076 kPa at correct threshold 18.926 kPa; that frozen comparison
integrates no damage. Latest integration checks passed Node 36/36 with three
real SBCL contracts plus the bounded protected-base smoke/guard. The user
subsequently accepted the pilot's visual result; its exact reference shape remains
unmatched and scientific validation remains unverified. The later 40 kPa case
did not collapse; its raw cap 5000 became effective 2000 through schema
normalization, and it completed the requested 221.14 s in 111 frames.

The video comparison tool is an approximate occupancy/edge/plateau proxy. IoU
is not physical accuracy, and changing particle shape, raster threshold, rotation,
compression or time alignment changes the score. Actual title/simulator times
must be supplied; the tool does not infer a physical clock from playback.

The paper itself overpredicts field cutback/run-out and notes the2D assumption
fails during granular run-out. Similarity to its numerical pictures and fidelity
to the real field event remain separate targets. Earlier delegate/export evidence
in [[studio-verification-2026-10-14]] does not validate this new reference case.

Implementation guide/results: `docs/REFERENCE_REPRODUCTION.md`.
Scientific mechanisms: [[cl-mpm-architecture]], [[studio-geometry-material]].
