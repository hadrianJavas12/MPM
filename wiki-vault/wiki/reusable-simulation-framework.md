---
title: Reusable native simulation framework
type: synthesis
tags: [cl-mpm, architecture, refactoring, native-windows, regression]
sources: [docs/REUSABLE_FRAMEWORK.md, docs/AI_HANDOVER.md, docs/testing.md, framework/cl-mpm-framework.asd, docs/evidence/framework-refactor-2026-10-15/validation-summary.json]
updated: 2026-10-15
---

# Reusable native simulation framework

The user requested interchangeable material, geometry, boundary/loading and
solver components, with short executable case files instead of long scripts
mixing setup, material overrides and output. UI work is explicitly deferred.
The existing [[cl-mpm]] engine remains the numerical implementation; reusable
adapters organize its construction and execution rather than duplicate laws.

## Checkpoint and commit order

The user merged [PR #7](https://github.com/hadrianJavas12/MPM/pull/7) into `main`,
merge commit `efd0358b7f571e738c0ecc022c4313fb7fca0d15`. Public GitHub API status
was refreshed on 2026-10-15: merged at 14:57:44 WIB. Older wiki statements that
PR #7 remains open describe the publication checkpoint and are superseded here.
The active branch is `codex/reusable-simulation-framework`.

Initial refactoring was committed as `66ea5fb` **before post-refactor simulation
validation**, as requested. Compatibility/launcher/API fixes followed, including
native constructor-option correction `c5fd10d`; composition/regression tooling
was committed as `9f26cb1`. Full native post-refactor runs loaded copied source
snapshot `2f6476f`. Later commit tests and bounded integration evidence are
recorded separately, rather than relabeling that snapshot. A new framework PR
has not yet been claimed at this intermediate update.

## Component and scenario boundaries

`framework/cl-mpm-framework.asd` loads component contracts, configuration,
dedicated chalk classes, geometry/builders, boundaries, measurements/output and
scenario phases. `cases/*.lisp` composes these through `make-simulation`; the
headless Windows entry is `scripts/run-case.lisp`. Native old entry points remain
compatibility adapters. See [[cl-mpm-architecture]] and [[windows-port]].

Material factories return native particles, and geometry filters are per-run
`(x,y,z)->boolean` callbacks. They do not install broad engine method overrides.
Triaxial measurement state is bound locally for one run and supplied configuration
is not mutated. Construction supports VM/elastic selection, native VM subclasses
and actual geometry clipping. The elastic adapter disables plasticity on the
native VM class to preserve its diagnostic state. Unrecognized options and
incompatible combinations reject explicitly. Triaxial models with other state
require a measurement adapter; the Joss recipe retains its special material,
base and phase contracts. This is not universal compatibility between all laws
and scenarios.

## Completed native 2D regression

A frozen original triaxial monolith received only an auditable 2D mesh/specimen
adaptation before being run. The refactored public CLI then ran the same case:

| Recorded quantity | Before and after |
| --- | --- |
| Geometry | 70 × 140 mm plane-strain rectangle, unit thickness |
| Particle count | 480 |
| Native updates / saved VTK states | 17,443 / 51 |
| Native time / prescribed strain | 0.2 s / 10% |
| Measured specimen extent strain | 9.86716593% |
| qJ2 / projected triaxial q | 50.01733976 / 43.30520503 kPa |
| Numerical comparison | Every VTK byte hash identical; all CSV/field/position differences zero |
| Mass drift | Zero |

This is **plane strain**, not an axisymmetric or three-dimensional cylinder.
Native saved-frame assertions check Fzz=1 and zero out-of-plane shear, position
and velocity. Full 3D constitutive stress is retained in memory, so the native
qJ2 and the historical projected q differ. Old [[triaxial-clay-calibration]] 3D
curves are contextual only; exact equality is tested between matching 2D cases.

The existing 2D VTK exporter omits sigma_zz and out-of-plane velocity/displacement.
The independent audit therefore declares full qJ2, projected 3D stress and
Kirchhoff yield recomputation from VTK unavailable. It does not infer missing
components. Finite fields, mass, volume, in-plane displacement/kinetic energy,
axial stress and CSV identities pass; the full native CSV qJ2 curve is compared
exactly in the before/after regression. This limitation is separate from the
runtime Fzz assertions.

The first one-MP-per-cell-direction attempt failed around 6.3% strain: lateral
GIMP domain expansion reached the engine's default removal threshold, deleting
two particles and triggering the mass invariant. Failed outputs and source are
retained. Both successful runs use two MPs per cell direction. Neither the
engine removal rule nor the mass check was weakened to obtain a pass.

Actual-data final PNG/video and before/after/old-3D curve overlays were generated
and inspected. The H.264 video decodes fully: 51 frames at 15 fps means 3.4 s
playback, distinct from 0.2 s numerical time. Sources and hashes are recorded
under `output/framework-refactor-2026-10-15/`.

## Other tests and completed four-worker cliff comparison

Ten framework component contracts passed with no time integration; private
triaxial component contracts also passed. Node syntax checks and all 36 tests
passed with zero skips. Actual two-step custom-delegate compatibility smoke
retained zero stress/position differences, and Joss reference unit checks passed.
These are narrower scopes than a complete native scenario regression.

Both fresh-start Joss versions completed 40 s, but **strict regression failed**:
176 original versus 191 framework frames. The unchanged comparator uses
absolute tolerance 1e-8 and relative tolerance 1e-7; common-clock fields also
fail. At 40 s maximum position-component difference is 0.0811648 m and RMS is
0.00234568 m. This failure remains in the evidence summary.

Both initiate lower damage above 0.05 at 4 s and upper damage at 7.5 s. Final
run-out is 31.01589046 versus 31.01587968 m, and shape IoU is 0.99667193.
All saved arrays are finite, mass is conserved, and the 496 protected base MPs
retain zero damage. These are diagnostic collapse and integrity checks, not
proof of numerical equivalence or physical accuracy. The historical pilot in
[[joss-reference-reproduction]] used a warm start and differs separately; its
differences must not be assigned automatically to this refactor.

Existing independent runs with identical private numerical source already
show comparable tiny differences at equilibrium and 4 s, while all initial
VTKs are byte-identical. Unchanged parallel accumulation offers a plausible
mechanism, but does not prove the entire 40 s difference is runtime variability.
A paired full serial control now tests that question without changing physics
or tolerances. The user authorized a checkpoint commit/push while waiting;
final acceptance and the PR remain pending that assessment.

These results establish software regression properties, not experimental clay
calibration, convergence or a closed energy budget. The findings in
[[scientific-authenticity-audit-2026-10-15]] remain open scientific caveats.

## Background continuation requested by user

The user requested an explanation before further investigation, so the existing
heartbeat is **paused**. Existing native processes continue independently;
do not resume automatic work without user direction. They started at 20:53:38 WIB
on 2026-10-15: frozen original `c749d32` versus test case `41403f4`, both one
worker, OpenBLAS/OMP threads set to one. Output folders are
`joss-serial-before` and `joss-serial-after` under the existing run root.
See docs/AI_HANDOVER.md for exact status/log/helper paths. Preserve the original
four-worker failure even if the separate serial control passes. Pause the
heartbeat when the task is complete.
CurrentHEAD bounded Joss4s and2D27updates passed. A distinct native Mohr-Coulomb
composition on0fece3b also passed2updates with36finiteVTKarrays andmass504000kg/m
conserved while native splitting changed70MPs to280; no engine edits/rerun.
The four-worker evidence bundle is retained with hashes and
`regressionPassed=false`; the separate serial control is pending.
