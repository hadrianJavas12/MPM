---
title: Scientific and authenticity audit 2026-10-15
type: synthesis
tags: [mpm, scientific-validation, authenticity, native-windows, damage]
sources: [docs/SCIENTIFIC_AUDIT_2026-10-15.md, docs/RUN_ACCEPTED_COLLAPSE_WINDOWS.md, docs/evidence/joss-collapse-2026-10-15/manifest.json]
updated: 2026-10-15
---

# Scientific and authenticity audit

After accepting the visual collapse, the user requested an audit for genuine
solver output and scientific validity. The requested Windows-native rerun guide
and fresh-start config were committed/pushed first in `8549c32`; the accepted
pilot checkpoint is `cd5e07f`. See [[joss-reference-reproduction]] and
[[joss-damage-diagnosis-2026-10-15]].

## What was verified

All 174 saved physical VTKs contain 4155 particles/36 finite arrays and constant
mass425664.0625 kg/m. Damage is nondecreasing and the496 protected base MPs retain
zero damage/plastic strain. Position and displacement agree to8.1e-13m. Every
saved physical PNG regenerated pixel-identically;175 decoded video frames agree
with corresponding PNGs within H264 compression error. All35 archived manifest
entries match; log/CSV transitions agree. No prescribed failure trajectory or
painted damage was found in the inspected path.

Historical warm-start constructor/environment hooks, DP subclass and protected
base guards are explicitly documented; the pause hook only controls wall time.
Those interventions do not inject a failure shape, but are not a pristine
unmodified author run. Accelerate uses mass scale10000; its clock is integration/
constitutive time with artificial inertia, not fully unscaled dynamic time.

## Scientific limits reproduced on Windows

- Native two-MP kernel control: nominalR=.5, trueR=.1/.5, gap=.3 gives raw
  pair weights .75759616 and0, rather than a symmetric damaged-radius kernel.
  Averaged driveA becomes43.1041Pa for localA0/B100Pa. Normalized averaging itself
  need not be symmetric; this finding concerns the pre-normalization kernel.
  Kernel shape also differs: native [1-(r/R)^4]^2 vs paper Eq33 [1-(r/R)^2]^2.
- Native aggregation control: four nodes of a disconnected fragment are coupled
  across8m emptygap to a full support with cell-centroid distance9m; E weights reach10/-9 while
  preserving unit translation. Incidence in the accepted run is not measured.
- Native nonuniform displacement/GIMP control: FbarON gives V/V0=1.025 but
  detF/domainarea=1.02375; OFF gives1.025 for all. This needs a documented,
  validated kinematic contract, not an automatic claim of a bug.

There is no closed energy budget, mesh/timestep convergence or material/field
validation of this run. DP, aggregate statistics and Heun damage integration are
author-code adaptations, not literal paper equivalence. E/Gf differences remain
explicit. **Authentic solver output is supported; scientifically validated
collapse/run-out is not established.** No production algorithm or accepted
artifact was changed by this audit. Do not relabel output as validated or tune
parameters silently to retain the accepted appearance.

Full findings and scoped evidence: `docs/SCIENTIFIC_AUDIT_2026-10-15.md`.

Fresh native production replay to4s completed after1658 equilibrium updates,
without historical constructor/environment replacement. Maxdamage.333589398
is again lower-face; position/damage differences from historicalt4 are at most
9.30e-10m/1.18e-7. Four snapshots retain all36finitefields and constantmass/base
damage0. This supports fresh initiation, not a complete40s replay or scientific
validation. Historical accepted artifacts and production algorithms remain intact.
