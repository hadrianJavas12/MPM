---
title: CL-MPM architecture
type: concept
tags: [architecture, mpm, asdf]
sources: ["[[refactor-2026-10-14]]", docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md, docs/AI_HANDOVER.md]
updated: 2026-10-17
---

# CL-MPM architecture

Time step (`cl-mpm:update-sim`): P2G → nodal momentum update with BCs → G2P and particle motion → constitutive update (Hencky/Kirchhoff, optional C++ `kirchoff.dll`) → optional non-local damage → adaptive dt.

`src/` directories: `core`, `models`, `damage`, `bc`, `solvers`, `dynamic-relaxation`, `ssa`, `mpi`. ASDF systems live in `cl-mpm.asd`.

Platform switches: `:win32` ⇒ `:cl-mpm-no-mpi` ⇒ serial [[serial-mpi-standin]]; expokit skipped. Dependencies are patched, see [[magicl-patches]].

Full text: `docs/architecture.md`. Parent: [[cl-mpm]].

## Migration target, 2026-10-16

P0 inventory is complete: 884 captured tracked paths exactly once, 104 native
ASDF registrations and 11 passing audit-integrity checks. Only two hash-bound
P1 source extractions are approved; 882 semantic reviews remain pending.
P0 was pushed as `6f15148` before moves. The matrix and hash-bound approvals are
immutable pre-extraction evidence; do not regenerate them after moves. See
`docs/architecture/FILE_MIGRATION_MATRIX.json` and the execution log for scope.

P1 production extraction `3cd172e` was pushed before tests: component contracts
now live in `src/simulation/components/{base,specifications}.lisp`, the material
definition in `materials/core/definition.lisp`, and the native factory in
`materials/adapters/native.lisp`. Sixteen defining forms and the whole factory
file retain exact bytes; class/package symbols, ASDF IDs and old path shims remain.
Focused contracts, normal/legacy loaders and snapshot escape checks pass; bounded
VM 27-update/MC two-update controls have strict two-state PASS with CSV/positions
zero. MC cliff VTKs match exactly; its unavailable gnuplot PNG is not a plot PASS.
The initial ownership/SBCL-tail and snapshot-registry fixture failures are retained;
only tests/fixtures changed. P1 is PROVISIONAL and G1 PARTIAL. Full migrated VM
2D on `62adb50` completed 51 states/17,443 updates with native/comparison/audit
exit 0 and strict/available-field audit PASS; positions/CSV/exported fields differ
by zero. VM 3D remains running. The user stopped Joss serial at 4.2 s:
STOPPED_BY_USER, incomplete, native exit null and comparison NOT_RUN_CANCELLED.
Its partial output is retained; the old exact `41403f4` control remains historical.
No full Joss restart is authorized without a new user request. Collect completed
VM evidence separately; fix the all-three collector before using it after cancellation.

The user supplied `docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md`
as the primary migration reference. The complete target remains pending beyond P1.
`codex/material-architecture-migration` starts from the `7c399fb` checkpoint of
[[reusable-simulation-framework]]. P0/G0 requires a complete actual-file matrix,
ASDF/load/Windows/Studio/caller map and form-level ownership for mixed source
before any code moves. The specification's 884-file remote inventory does not
cover untracked local work or prove that semantic audit complete.

Root `materials/` is the final owner of material models, model state, evolution
and diagnostics. A material definition is a parameter/provenance profile, not
a constitutive solver; evolution belongs within its model. Shared utilities need
real cross-model reuse. Generic engine/numerics/orchestration remain in `src/`,
reusable procedures belong in `scenarios/`, and `cases/` composes components.
Material code must not depend on scenarios or Studio; generic solvers call
constitutive protocols without embedding model laws or creating ASDF cycles.

Preserve package/class identity, native backend, equations, algorithms, defaults
and numerical results. `framework/` remains temporary compatibility until G5
proves all active callers/entry points have transitioned. Full G3 is PARTIAL.
The user prioritizes independent P3 diagnostics ownership preparation; a new
hash-bound split approval is pending before moves. P2 native formula migration
remains plan only until native-source/provenance planning. Cancelled Joss does
not block independent ownership work. P2–P6 implementation remains NOT_RUN.
Saved exact VM 2D/3D and
serial Joss controls are baseline evidence; four-worker FAIL and loaded-provenance
limits remain explicit. [[mc-hardening-softening-study]] physics integration is
deferred until migration gates, then requires a separate experimental branch.

Studio extends the existing particle law through a dedicated CLOS subclass
and shared loader/stress guard, preserving the core solver. See
[[studio-custom-models]] and [[studio-verification-2026-10-14]].

### P3 implementation checkpoint, before validation

Pre-move diagnostics approval was committed/pushed as `585af1d`.
Thirty-one original forms from `framework/components/diagnostics.lisp` were
extracted with exact form-body bytes: core protocol in
`materials/core/diagnostics-interface.lisp`, native classes/queries/validators in
`materials/diagnostics/native.lisp`, output helpers in
`src/measurements/material-output.lisp`. Existing package/CLOS symbols and old
source shim remain; ASDF loads owners directly. CLI snapshots now include
`src/measurements`. P3 tests are PENDING at this implementation checkpoint.
No native constitutive formula/state/evolution was moved or changed in P3.

Full P1 VM 3D on `62adb50` subsequently finished: native/comparison/audit exit 0
at 04:35 UTC, manifest complete. Its saved strict result remains separate from
P3 validation and from the cancelled Joss run. No full Joss restart.

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

## [2026-10-16] ingest | P2-A constitutive ownership checkpoint

P2-A implementation `4ed46b4` preserves all 81 original forms across 13 owners.
Five native family catalogs are byte-identical to the saved baseline. Native
VM/MC bounded controls, active MC ownership and Node 36 checks pass; copied-DLL
source freezing is verified. See [[cl-mpm-architecture]] and
`docs/architecture/STATUS.md`. P2-B/C/D and P4 remain pending; Joss stays stopped.

### P2 complete, P4 scenario ownership checkpoint — 2026-10-16

P2 A–D is implemented: 23 original mixed files, 495 audited forms, 49 approved
material targets. The chosen compact plan preserves arithmetic and override
order; old source loaders remain compatibility shims. All twenty post-move
native family catalogs match the five baseline catalogs byte for byte.

P2-B + P4-B: 57 evidence hashes; P2-C + P4-C: 74; P2-D + P4-D: 58.
Each wave passed actual Windows VM/MC short controls with exact saved VTK/CSV
bytes against the preceding wave, material ownership/diagnostics contracts,
scenario/config contracts and Node 36. C additionally passed two native cliff
MC updates with exact P1 VTKs and the custom delegate control. D deliberately
reuses that unchanged cliff proof. Sources were sealed before later edits.
Evidence is under docs/evidence/architecture-migration-2026-10-16/p2-{b,c,d}/.

P4-E is committed at d6d3f61: the approved nested VM diagnostics and homogeneous
material-state transfer now belong to materials/adapters/legacy-triaxial.lisp.
Both exact expression reconstruction proofs are saved; validation is running.
Next is P4-F canonical root ASDF, actual caller/snapshot integration, final full
VM 2D/3D regressions, bounded serial Joss comparison, compatibility, docs and PR.
The fresh four-second old-source Joss control uses isolated verified pre-P2
source copies; it does not restart or replace the cancelled full 40-second run.
G1/G3 remain PARTIAL owing to preserved legacy overrides and Joss exceptions.
No main merge, numeric changes, new H/HS physics or UI work is authorized here.

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

### P4-F and P6 final validation, bounded Joss control, and full VM 2D/3D completion — 2026-10-17

Resumed from handover commit `9dfb58b` without repeating already-passed checks:
- **`p6-short/` (11/11 native checks PASS, 64 verified artifacts)**: `case-snapshot` (3/3),
  `native-snapshot` (7/7), `standalone-triaxial` (3/3), `p4-orchestration-002` (4/4; initial
  Windows PowerShell 5.1 stderr redirection failure `p4-orchestration` retained unchanged),
  `engine-smoke` (100 MPs, 50 steps), `ownership-normal` (7/7), `ownership-legacy` (7/7),
  `diagnostics-legacy` (3/3), `custom-delegate` (64 MPs, 2 steps, 80 custom calls, zero diff,
  VTK readback), `cliff-mc` (70 MPs, 2 substeps, byte-identical `vtk/mesh.vtk` and
  `vtk/sim_00001.vtk` vs P1), and `legacy-triaxial` (480 MPs, 27 updates, strict comparison
  PASS vs P4-E), plus Node syntax check and 36/36 tests passing (`p4-f-node/`).
- **`joss-bounded/` (4-second serial initiation control PASS, 54 verified artifacts)**:
  Pre-P2 baseline `before-003` (`a99a4e1` / `7e2aac3`) and final canonical candidate
  `after-001` (`9dfb58b`) both completed 1,658 elastic equilibration steps and 4.0 s
  physical time (`exit 0`), with byte-identical `equilibrium.vtk`, `sim_00001.vtk`, and
  `sim_00002.vtk` and zero position/field/CSV differences. Earlier harness failures
  `before-001` and `before-002` are retained.
- **`p6-full/` (full final-layout VM Triaxial 2D and 3D regressions PASS, 38 verified artifacts)**:
  Both `triaxial-2d` (480 MPs, 17,443 updates, 51 states) and `triaxial-3d` (780 MPs,
  17,443 updates, 51 states) completed on `9dfb58b` with `nativeExitCode=0`,
  `comparisonExitCode=0`, and `auditExitCode=0`; all 51 VTKs per run and `stress-strain.csv`
  are byte-identical to `p1-full` (`62adb50`), with zero position/CSV/field differences
  and independent audits passing.
- **Ownership result ledger (`docs/architecture/FILE_MIGRATION_RESULT.json`)**:
  Created `docs/architecture/COMPONENTS.md` and generated the 884-path ledger without
  modifying `FILE_MIGRATION_MATRIX.json`: `812` `RETAINED_UNCHANGED`, `14` `RETAINED_MODIFIED`,
  `58/58` `MAPPED_OWNERS_PRESENT` (`0` pending).
- **Gates**: `G0` DONE, `G1` PARTIAL (preserved legacy damage/ice global overrides, concrete
  forward class, mixed C++ transaction), `G2` DONE, `G3` PARTIAL (full 40s Joss on migrated
  code remains `STOPPED_BY_USER` at 4.2 s and was not restarted; historical 4-worker parallel
  Joss failure remains open), `G4` DEFERRED ([[mc-hardening-softening-study]] physics deferred
  to separate experimental branch), `G5` DONE for active callers and retained `framework/`
  compatibility shims (two pre-existing missing legacy examples remain `BLOCKED`).

