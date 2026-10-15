---
title: Native clay triaxial calibration
type: synthesis
tags: [cl-mpm, clay, triaxial, calibration, windows]
sources: [docs/TRIAXIAL_CALIBRATION.md, calibration/README.md, docs/evidence/triaxial-clay-2026-10-15/manifest.json]
updated: 2026-10-15
---

# Triaxial clay demonstration and calibration method

Checkpoint published as [PR #7](https://github.com/hadrianJavas12/MPM/pull/7)
from `codex/triaxial-clay-calibration` to `main`, at the user's request. The
cumulative PR includes ancestry of PRs #1–#4, Windows/collapse/audit work and
the reports/calibration feature; PR #6 remains separate. It is open for review,
with no merge performed. Both PDF hashes match their manifest. Auto-continuation
is paused after completing the requested deliverables.

User confirmed an undrained example without laboratory data. The standalone
native module uses a nominal 70 mm diameter/140 mm high specimen, E 5 MPa,
nu .49, strength scale su 25 kPa and confinement 50 kPa. Existing particle-vm
provides a total-stress J2 surrogate, with rho=sqrt(8/3)su; no pore-water,
consolidation, damage, softening, Fbar, aggregation or mass scaling is claimed.

Actual native 3D MPM: 780 particles, 17,443 updates/51 VTKs, platen strain 10%,
specimen-domain extent strain 9.89852%, final q 50.00844 kPa and lateral stress
50.02246 kPa. Homogeneous native material-point comparator: 1,000 increments,
51 frames, final q 50.01000 kPa. The latter visualizes affine F and is explicitly
not a spatial MPM run. Both retain finite fields and constant mass.

Figures/videos place recorded particles next to the recorded q-strain curve.
The solid line uses specimen extent strain; the dashed MPM line uses prescribed
platen strain. Colour is the native plastic-strain measure (1.5 times the standard
equivalent measure in this VM implementation), not damage. No invented shear band.

The CSV helper initializes E/su/rho and records selected strain column and input
hash. It does not optimize the native forward model or calibrate real clay.
E initializers are approximately 4.627 MPa from platen strain, 5.044 MPa from
specimen extent, and 5.010 MPa for the homogeneous comparator. This demonstrates
fixture/measurement sensitivity, not independent experimental validation.

Native elastic/yield/lateral/hydrostatic controls passed; estimator 4/4 unit
tests and Node 36/36 passed. Limits remain: 3D coarse volume bias +3.4507%,
bilateral normal-spring end constraints, .020016% volume drift, early kinetic
transient, no mesh/rate/timestep convergence or closed energy budget. Exact
pre-load source snapshots were unavailable for production runs and are declared;
the future launcher snapshot path was tested with final controls.

See [[upstream-development-report-2026-10-15]] for attribution, and
[[scientific-authenticity-audit-2026-10-15]] for the separate historical cliff audit.
