---
title: Joss damage diagnosis and accepted physical collapse 2026-10-15
type: synthesis
tags: [joss-bay, damage, drucker-prager, native-windows, calibration]
sources: [docs/JOSS_DAMAGE_DIAGNOSIS_2026-10-15.md, docs/evidence/joss-collapse-2026-10-15/README.md, output/reference-reproduction-2026-10-15/criterion-probe/summary.json, output/reference-reproduction-2026-10-15/dp-physical-pilot/damage-location-audit.json, output/reference-reproduction-2026-10-15/dp-physical-pilot/final-shape-comparison.json, output/reference-reproduction-2026-10-15/validation/validation-summary.json]
updated: 2026-10-15
---

# Joss damage diagnosis and accepted physical collapse

The user accepted the actual native DP pilot's lower-face damage and
collapse/run-out as the requested visual result after viewing its video and the
later 40 kPa final image. They requested a commit recording successful collapse;
no further calibration is requested. The pilot still over-collapses relative to
the reference image, so visual acceptance is separate from numerical agreement
or scientific validation. See
[[joss-reference-reproduction]] and `docs/JOSS_DAMAGE_DIAGNOSIS_2026-10-15.md`.

The recovered legacy DR one-trial probe retains native time 0 and sets dt 1;
committed positions do not move, while trial positions do. Its assigned timeline
does not demonstrate a physical trajectory. Exact identity with the real damage
clip remains unproved: [[antigravity-native-history-2026-10-15]].

Strict native aggregate preparation converged in 1658 updates, energy ratio
5.068e-9/projected OOBF 9.9667e-5, 4155 MPs/mass 425664.0625 kg/m. Same-state
six-component-stress/nonlocal comparison found lower DP 50.409 kPa versus MC
16.076 kPa at correct initiation 18.926 kPa. Upper DP is 33.937 kPa. The probe
integrated no damage. Production reference-only methods now use author Joss DP
with radian friction and protected elastic index-1 foundation/beach. Ordinary
Studio/chalk defaults are unchanged.

The first saved damaged physical frame is t=4 s, max 0.333589 at approximately
(13.125, 3.625) m with upper damage 0. At the t=4.3552376 s pause, max damage
is 0.386528 and all 496 base MPs have zero damage. The resumed pilot finishes
40 s/174 frames with finite audited fields, constant mass and mass-weighted
damage 0.493673. Its final shape comparison against reference t=221.14 s yields
occupancy IoU 0.699825, run-out +7.8 m and plateau edge −5.2 m. These are image
proxies at different times, not physical accuracy or timing agreement.

Evidence directory `output/reference-reproduction-2026-10-15/dp-physical-pilot/`
contains metadata, time/transition CSV, damage-location audit, final comparison
and `damage-t4.png`/`damage-t40.png`. `complete=true` refers only to its 40 s
target; scientific validation remains unverified. PNGs were rendered separately
from real VTK; native pilot gnuplot was disabled.
Selected media and supporting evidence are preserved under
`docs/evidence/joss-collapse-2026-10-15/`: `accepted-collapse.mp4`,
`accepted-collapse-t40.png`, and the separate `latest-40k-t221.png`.
Its README records configs, CSVs, metadata, audits, sources and validation logs.
The accepted pilot used a saved strict-equilibrium warm start and isolated
`joss-probe-dp-chalk` subclass; keep that historical continuation distinct from
a fresh production CLI replay through the current reference class. Identical
production replay remains unproved.

Actual integration checks in `validation/validation-summary.json` passed Node
36/36 including three real SBCL contracts, a native reference smoke (179 prep
steps/1092 MPs/124 protected base MPs/four finite VTKs/two PNGs) and the failed
equilibrium guard. The smoke is frame-limited at 0.02 s and proves no collapse.

The later production CLI **unverified calibration** in `strength-40k-run/`
completed **221.14 s / 111 frames**, final phase accelerate, with no collapse:
initiation 40 kPa between the measured lower/upper DP drives, derived cohesion
54949.548389 Pa/ductility 12, unchanged Gf 4.8 J/m²/delay 10 s, h 0.5 m/two MPs
per axis/four workers. Final max damage is 0.49062952033 and mass-weighted
damage 0.008064637675. Raw cap 5000 normalized through the schema to effective
2000, and the requested time was reached before the cap. It is not literal paper
parameters or a sweep. The old PID 29416/pending statement is superseded.
Heartbeat `mpm-lanjut-setelah-reset` is confirmed **PAUSED** after user acceptance;
no further simulations, calibration or UI work are requested.

Live public GitHub API refresh on 2026-10-15 retains draft stacked PRs #1–#4;
separate draft #6 is modular-preset background work, based on #4's branch and
not imported into this result. Active branch remains
`feat/studio-custom-constitutive-lisp-export`, based on f70e410 before the
authorized acceptance commit. No push or merge was requested.
Raw wiki sources and earlier log entries were preserved.
