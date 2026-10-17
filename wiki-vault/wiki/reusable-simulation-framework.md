---
title: Reusable native simulation framework
type: synthesis
tags: [cl-mpm, architecture, refactoring, native-windows, regression]
sources: [docs/REUSABLE_FRAMEWORK.md, docs/AI_HANDOVER.md, docs/testing.md, framework/cl-mpm-framework.asd, docs/evidence/framework-refactor-2026-10-15/validation-summary.json, docs/evidence/material-contract-2026-10-16/validation-summary.json, docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md]
updated: 2026-10-17
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
Its updated prompt forbids restarting the user-stopped full Joss run without a
new request and prioritizes independent architecture ownership work.
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
2D on `62adb50` passed 51 states/17,443 updates, native/comparison/audit exit 0,
with zero CSV/position/exported-field differences; available-field limitations
remain. VM 3D is running. The user stopped Joss serial at 4.2 s, with saved
STOPPED_BY_USER/incomplete status, null native exit and cancelled comparison.
Retain partial evidence; do not restart full Joss without a new request.
Full G3 is PARTIAL. Collect VM evidence separately and correct the collector's
all-three-complete assumption before use. The cancelled run does not block the
user's independent architecture priority: P3 diagnostics split/approval is next,
while P2 native formula ownership still needs native-source/provenance planning.
P2–P6 implementation is NOT_RUN. The isolated
32-test MC prototype is uninstalled; new physics is deferred until migration gates
and belongs on a separate experimental branch.

### P3 validated checkpoint — 2026-10-16

Implementation `315a46d` preceded tests; supported-factory fixture correction
`333306b` is the executed snapshot. All 13 finite validation commands exit 0:
10 component, 10 config, 9 material, 3+3 diagnostic ownership, 7+7 original
ownership, 3 snapshot and 36 Node tests (zero skipped), plus Node syntax checks
and strict bounded comparisons. VM 480 MPs/27 updates and native MC 32 MPs/two
updates each retain two byte-identical VTK files versus P1; CSV/position/field
numerical differences are zero. All 31 original source forms retain exact bodies.
Live unit source hashes remained unchanged throughout checks; the CLI additionally
loaded copied source. This does not complete native engine/FASL/DLL provenance.

Evidence: `docs/evidence/architecture-migration-2026-10-16/p3/` (37 verified
manifest entries), and `p1-full/` (44 entries: completed full VM 2D/3D, cancelled
Joss retained separately). Joss stays stopped; full G3 and G1 remain PARTIAL.
The initial P3 packaging attempt failed only because its Node reporter regex
expected `# pass` instead of the actual Unicode reporter. Partial packaging is
retained in `output/architecture-migration-2026-10-16/p3-packaging-attempt001/`;
parser corrected and packaging completed without rerunning tests or simulations.

No active simulation remains from these validation jobs. Next: implement/review
native-source freezing per `docs/architecture/NATIVE_SOURCE_SNAPSHOT_PLAN.md`,
then P2 elastic ownership extraction with exact per-form approval and focused
regression. Preserve the cancelled Joss directive, native formulas and all prior
positive/negative evidence; no UI, main merge, or premature framework deletion.

### Full-migration continuation, 2026-10-16

The user explicitly authorized continuing until the entire architecture refactor
is finished. P2 now has a committed compact plan: 23 source files / 495 forms,
49 cohesive targets. The 109-fragment exact-order plan is an audit alternative,
not the chosen execution layout. Independent definitions may be regrouped only
under the reviewed dependency/override order; arithmetic bodies stay exact.
P2/P4 plans were checkpointed before source moves. No P2/P4 move is claimed yet.

P5 engine grouping (`59928ba`) is implemented: numeric kernels and matrix-free
linear solver moved byte-identically to `src/numerics/fastmaths.lisp` and
`src/solvers/linear-systems.lisp`, preserving ASDF IDs and old source shims.
Three analytical/legacy/path contracts and actual gravity smoke (100 MPs,
50 updates) passed. Evidence: `docs/evidence/architecture-migration-2026-10-16/p5/`
(12 hashes). The live unit status records HEAD at completion; it is not a frozen
pre-load source claim. Engine bodies match the implementation commit.

Five fresh native family load/catalog baselines passed before model migration
(engine/framework, chalk, ice, limestone, visco); sources stayed unchanged.
Evidence `p2-baseline/` (21 hashes) preserves the first reflection-fixture failure
and corrected complete catalogs. Console size reporting was corrected separately;
the serialized sorted catalogs were already complete. These are structural
compatibility baselines, not numerical/scientific validation of optional models.

Native source freezing was implemented at `7a320f5`; existing snapshot 3 and new
native snapshot 7 contracts passed, including actual Windows copied-DLL path and
private FASLs. Its first bounded VM attempt failed before stepping because the
new metadata/cache occupied the otherwise-empty output root. Fix `0a17ece`
places them under reserved `source/` without weakening the runner guard and adds
future canonical-root ASDF support. Native snapshot/VM retry and bounded MC checks
are now running once under `output/architecture-migration-2026-10-16/native-freeze/`.
Do not edit selected native/P4 sources until that agent reports completion.
The frozen CLI currently requires Windows; core ASDF remains separate/portable.

Next: P2 compact stages A–D, then P4 helpers/owners/canonical ASDF and caller
transition, final compatibility/regressions/docs/PR. P2 helper never edits ASD;
route-aware updater must preserve existing P5 paths. No full Joss restart, no
new physics, no main merge. Existing global override/forward-class/atomic C++
transaction exceptions stay visible; folder relocation does not repair them.

### Human handover checkpoint — 2026-10-17 (Asia/Jakarta)

The user requested a committed handover before another AI continues. Read
`docs/architecture/NEXT_AI_CHECKPOINT.md` first; it supersedes older next steps.
P2 A–D and P4 B–E are implemented/tested. P4-F canonical root ASDF/callers are
implemented at 436b561. E evidence has 34 verified hashes; F partial evidence
has 20 verified hashes and 252 sealed source files (snapshot3/native7/standalone3
all exit 0 at actual launch HEAD326268a). Node36/check also pass.

The remaining F short queue was deliberately stopped before further launches;
its controller interruption is USER_STOPPED_QUEUE, not a failed assertion.
Final full VM2D/3D wrappers are prepared but NOT_RUN. One independent immutable
old-source four-second Joss baseline before-003 remains running; do not duplicate
it or confuse it with the cancelled full40s run. The initial two harness failures
are retained. All details/PIDs/paths and next steps are in the checkpoint.

Automatic continuation is PAUSED to avoid concurrent work during human handoff.
No final migration PR, main merge, scientific acceptance or complete G3 is claimed.

### P4-F and P6 final completion — 2026-10-17

Canonical root `cl-mpm-framework.asd` (`436b561` / `9dfb58b`) is now fully validated:
- **`p6-short/` (11/11 checks PASS, 64 verified artifacts)**: `case-snapshot` (3/3),
  `native-snapshot` (7/7), `standalone-triaxial` (3/3), `p4-orchestration-002` (4/4;
  initial PS 5.1 stderr redirection failure `p4-orchestration` retained), `engine-smoke`
  (50 steps), `ownership-normal` (7/7), `ownership-legacy` (7/7), `diagnostics-legacy`
  (3/3), `custom-delegate` (80 custom calls, zero diff), `cliff-mc` (byte-identical VTKs
  vs P1), and `legacy-triaxial` (strict comparison PASS vs P4-E), plus Node 36/36 (`p4-f-node/`).
- **`joss-bounded/` (4-second serial control PASS, 54 verified artifacts)**: `before-003`
  (`a99a4e1` / `7e2aac3`) and `after-001` (`9dfb58b`) both finished 1,658 equilibration
  steps and 4.0 s (`exit 0`) with byte-identical `equilibrium.vtk`, `sim_00001.vtk`, and
  `sim_00002.vtk` and zero position/field/CSV differences.
- **`p6-full/` (full final-layout VM 2D and 3D regressions PASS, 38 verified artifacts)**:
  Both `triaxial-2d` (480 MPs, 17,443 updates, 51 states) and `triaxial-3d` (780 MPs,
  17,443 updates, 51 states) completed on `9dfb58b` (`exit 0`) with all 51 VTKs per run
  and `stress-strain.csv` byte-identical to `p1-full` (`62adb50`), zero position/CSV/field
  differences, and independent audits passing.
- `docs/architecture/FILE_MIGRATION_RESULT.json` records all 884 original P0 paths with
  `120/120` `MAPPED_OWNERS_PRESENT` (`749` `RETAINED_UNCHANGED`, `15` `RETAINED_MODIFIED`) after
  the user-directed Section 2/5 physical directory alignment (`5d6a5cf`), which retired legacy
  `framework/`, `src/models/`, and root `src/` shims, organized `src/` into the 15 Section 2
  engine subdirectories, and organized `cases/` into `cases/{triaxial,cliff,benchmarks,direct-shear}/`
  (with flat-path fallback in `snapshot-resolve-case-file`).
- On the aligned Section 2 layout, **Benchmark 1 — Triaxial 2D** (`cases/triaxial/triaxial-clay-2d.lisp`
  -> `section2-benchmarks/triaxial-2d`) passed with all 51 VTKs and `stress-strain.csv` SHA-256
  byte-identical to `p1-full/triaxial-2d` (`audit-triaxial.py` PASS), and **Benchmark 2 —
  Progressive bottom-to-top chalk cliff failure** passed both the bounded 4.0 s serial control
  (`section2-benchmarks/joss-serial-4s`, SHA-256 byte-identical to `before-003`) and the
  progressive bottom-to-top damage propagation audit (`section2-benchmarks/joss-collapse`,
  bottom toe/notch initiation at `t = 4.0 s` `lower_max_damage = 0.3336`, `upper_max_damage = 0.0`
  propagating upward to the upper cliff face $y \ge 9\text{ m}$ at `t = 7.0..7.7 s`
  `upper_max_damage = 0.0554 -> 0.0772 > 0.05`). See [[cl-mpm-architecture]].

