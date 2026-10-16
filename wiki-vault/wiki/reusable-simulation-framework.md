---
title: Reusable native simulation framework
type: synthesis
tags: [cl-mpm, architecture, refactoring, native-windows, regression]
sources: [docs/REUSABLE_FRAMEWORK.md, docs/AI_HANDOVER.md, docs/testing.md, framework/cl-mpm-framework.asd, docs/evidence/framework-refactor-2026-10-15/validation-summary.json, docs/evidence/material-contract-2026-10-16/validation-summary.json, docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md]
updated: 2026-10-16
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
The architecture checkpoint is `7c399fb` on `codex/reusable-simulation-framework`.
Current branch is `codex/material-architecture-migration`, created from it.

The new [[cl-mpm-architecture]] specification governs the next work: root
`materials/` owns model-specific implementation/state/evolution/diagnostics,
`src/` owns generic engine/numerics/orchestration, and `scenarios/` owns reusable
procedures. P0's 884-path inventory was pushed as `6f15148` before moves; its
matrix/approvals stay immutable. The full target remains pending beyond P1.
`framework/` remains temporary compatibility until G5 proves caller transition;
equations, algorithms, defaults and numerical results must remain unchanged.

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
A paired full serial control completed without changing physics or tolerances:
**191 physical states, 193 particle VTKs and complete CSVs are byte-identical**.
All exported position/scalar differences are zero. The source audit identifies
original `c749d32` and executed after `41403f4`; completion status `909fddf`
is HEAD at exit. This establishes serial equivalence and preserves the separate
parallel failure. The listed dedicated Joss numerical sources remain byte-identical
to `41403f4`; no new full Joss run on `64f47cc` is claimed.

Generic diagnostics passed 9 native contracts and configuration passed 10,
with 10 framework contracts and 36 Node tests passing. Full VM regressions on frozen
`64f47cc` now pass for both 2D (480 MPs) and 3D (780 MPs): each completed exit 0,
17,443 updates and 51 states, with all 51 VTKs byte-identical and all CSV/position
differences zero. All independent audits pass within their available-field scope;
the 2D missing-field caveat above remains. The new material-contract bundle has
60 SHA-256-verified manifest entries; native jobs have finished. M0 remains
**PROVISIONAL** with four-worker FAIL and incomplete transitive loaded FASL/DLL
provenance. See [[mc-hardening-softening-study]].

These results establish software regression properties, not experimental clay
calibration, convergence or a closed energy budget. The findings in
[[scientific-authenticity-audit-2026-10-15]] remain open scientific caveats.

## Background continuation requested by user

The user subsequently authorized the M0–M6 master plan, commits/pushes per stage
and reset-aligned automatic continuation. The old heartbeat was missing; the
replacement `mpm-lanjut-migrasi-arsitektur` is ACTIVE with the current architecture
priority. After the user's final reset correction, its first wakeup is 13:14 WIB
on 2026-10-16, then every five hours. It checks saved status before any new work.
The completed serial controls started at 20:53:38 WIB
on 2026-10-15: frozen original `c749d32` versus test case `41403f4`, both one
worker, OpenBLAS/OMP threads set to one. Output folders are
`joss-serial-before` and `joss-serial-after` under the existing run root.
See docs/AI_HANDOVER.md for saved status/log/evidence paths. Preserve the original
four-worker failure alongside the passing serial control.
Bounded Joss 4 s and 2D 27 updates on `9f26cb1` passed. A distinct native Mohr-Coulomb
composition on0fece3b also passed2updates with36finiteVTKarrays andmass504000kg/m
conserved while native splitting changed70MPs to280; no engine edits/rerun.
The four-worker evidence bundle retains `regressionPassed=false`; separate
serial-control evidence reports PASS. All 134 manifest hashes verify. Neither
status should overwrite the other or be presented as experimental validation.
P1 extraction `3cd172e` was pushed before tests. New owners are
`src/simulation/components/{base,specifications}.lisp`,
`materials/core/definition.lisp` and `materials/adapters/native.lisp`; 16 defining
forms and the whole factory file retain exact bytes, symbols, ASDF IDs and shims.
The P1 bundle retains 32 hash-verified artifacts: 10 framework, 10 config,
9 material, 36 Node/zero skipped, 7 normal/7 legacy compatibility and 3 snapshot
checks pass. Strict bounded VM 27-update and MC two-update controls pass with
two states and zero CSV/position differences. MC cliff VTKs match; PNG plotting
is unavailable. Initial SBCL-tail and ASDF-registry fixture failures are retained;
only tests/fixtures changed. P1 remains PROVISIONAL, G1 PARTIAL. Full migrated VM
2D/3D and serial Joss G3 runs started on `62adb50` at 11:07:41 WIB in `p1-full/`;
they are RUNNING, not PASS. P2 is plan only,
P2–P6 NOT_RUN. The isolated
32-test MC prototype is uninstalled; new physics is deferred until migration gates
and belongs on a separate experimental branch.
