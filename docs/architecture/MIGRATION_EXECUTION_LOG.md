# Architecture migration execution log

## 2026-10-16 — P0 intake and audit

- Branch: `codex/material-architecture-migration`, created from `7c399fb`.
- Main refreshed as `efd0358`; open fork PRs #2/#3/#4/#6 inspected. No main edit,
  PR merge, upstream synchronization or new physics integration.
- User specification copied unchanged from Downloads to
  `docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md`; SHA-256
  `40a4583286de05024869eedcfae7f08d6bd18444e0a4fa64c14cf2aa266734ca`.
- Initial inventory: 884 tracked paths at `7c399fb`. Dirty tracked wiki files
  and untracked evidence/settings are recorded separately and preserved.
- No native SBCL process is still running. Existing `64f47cc` VM 2D and 3D
  regressions both completed: 51 VTKs per dimension identical to baseline,
  positions/CSV differences zero; independent available-field audits PASS.
  Evidence: [current material-contract bundle](../evidence/material-contract-2026-10-16/README.md).
- Previous Joss serial control is exact PASS at executed `41403f4`; the original
  four-worker strict FAIL remains open. Full transitive FASL provenance and
  experimental physical validation are not established.
- P0 permits audit tooling/documentation only. No material/engine source has
  moved. The matrix covers all 884 captured paths exactly once across 29 roots;
  every path has a conservative decision and an explicit semantic-review scope.
  Native ASDF introspection found 104 systems across 11 definitions, with zero
  metadata errors. It did not execute engine source or a simulation.
- Existing ASDF declarations reference two absent tracked examples:
  `examples/dr/quasi-time.lisp` and `examples/octree/slope-stability.lisp`.
  Their availability is BLOCKED independently of migration; declarations and
  evidence are preserved. No missing example has been invented or activated.
- Material source audit records concrete's forward superclass and existing
  global definition replacements in damage/ice. Their order is part of the
  preserved baseline, not repaired under the guise of folder cleanup.

| Phase / gate | Current status | Exit evidence / next action |
| --- | --- | --- |
| P0 / G0 inventory | DONE, bounded inventory gate | 884/884 paths; 104 systems; 11 audit integrity tests PASS; only two P1 sources approved for extraction |
| P1 / G1 contracts | NOT_RUN | Central material contract ownership with tested compatibility |
| P2 model ownership | NOT_RUN | One family per checkpoint, exact forms/order/backend preserved |
| P3 material diagnostics/definitions | NOT_RUN | Separate model-owned and generic diagnostics; no duplicate implementation |
| P4 / G2 orchestration | NOT_RUN | Native engine assembly and scenario owners, legacy loaders retained |
| P5 engine internals | NOT_RUN | Only justified small changes with direct regression |
| P6 / G5 compatibility and cleanup | NOT_RUN; pre-existing example exceptions | Proven caller transition before removal; two missing legacy examples remain blocked |
| G3 numerical baseline | PASS for executed snapshots; parallel exception OPEN | Repeat affected controls on each migrated executed snapshot |
| G4 new MC H/HS physics | DEFERRED | Separate experimental branch; staged point prototype is not full MPM acceptance |

## Checkpoint discipline

Each stage appends changed paths/reason, source/form hashes, executed commit,
commands/exit codes, PASS/FAIL/NOT_RUN and evidence locations, known risks and
the next bounded action. Commit and push cohesive stages. If a gate fails,
retain its output, explain the cause before expensive investigation, and revert
or repair the stage without deleting history. Rollback uses a forward corrective
commit or a separate checkout of the recorded parent, never a destructive reset.

At P0 the former auto-continuation entry was unavailable: update returned
"Automation does not exist in the app" and its saved TOML is absent. It has not
been recreated or claimed active.

### P0 verification and next stage

Actual audit output is retained in `P0_AUDIT_VALIDATION.txt`: 11/11 integrity
checks, generation and `--check` passed. This proves inventory/approval guard
behavior, not numerical migration. `MIGRATION_APPROVALS.json` binds two reviewed
sources to exact pre-extraction hashes and concrete target/form lists. The other
882 semantic reviews remain pending; bulk migration is not approved. New tracked
checkpoint files are registered separately as NEW rather than silently added to
the immutable 884-path capture. [P1 extraction plan](P1_CONTRACT_EXTRACTION.md)
defines the next small change and its still-unexecuted regression requirements.

## P1 implementation checkpoint — validation pending

P0 was committed and pushed as **6f15148 before any production extraction**.
The two approved sources now forward to their new owners. Sixteen existing
defining forms were extracted with identical body bytes; the native factory
file was copied byte-identically. Evidence before sources and form hashes:
`output/architecture-migration-2026-10-16/p1-source-before/` and
`p1-extraction-form-hashes.json`.

ASDF preserves the old specification/factory component IDs with relative owner
paths and explicit base/material-definition prerequisites. The CLI copies the
new ownership trees, compares each copy byte-for-byte, and verifies all framework
source component paths lie within the frozen source root **before** loading.
It records those paths; the external collector supplies SHA-256 manifests.
Native engine/FASL/DLL identity remains a separate, limited provenance scope.

No constitutive algorithm, particle ancestry, numerical parameter or tolerance
was changed. P1 compatibility/native/Node and full numerical tests are **NOT_RUN**
at this implementation checkpoint; neither P1 nor G1 is declared complete.

### P1 bounded verification after 3cd172e

Actual checks pass: 10 framework, 10 configuration, 9 material diagnostics,
7 normal and 7 legacy ownership, 3 snapshot-boundary checks, Node syntax and
36 tests with zero skips. VM 27-update and MC two-update triaxial controls pass
the unchanged strict comparator with zero position/CSV differences. Both saved
native MC cliff VTKs are byte-identical to the prior control.

The initial ownership test failed due to its incorrect hardcoded SBCL class
tail; an original-source control proves `SLOT-OBJECT` was already present. The
first snapshot negative fixture still preferred the frozen registry; its setup
was corrected so the unchanged guard now rejects actual checkout paths.
Both failed logs remain retained. No numerical assertion/tolerance was changed.
The cliff control reports an unavailable gnuplot PNG; plotting is not PASS.

[Bounded evidence](../evidence/architecture-migration-2026-10-16/p1/README.md)
retains 32 hash-verified artifacts, actual source copies, VTK/CSV, all logs and
form-byte comparisons. P1 remains PROVISIONAL/G1 PARTIAL pending deeper owner
migration and full G3 runs. P2 is only a conditional plan, not execution approval.

### P1 full regression launched after checkpoint

Bounded evidence/test correction checkpoint **62adb50** is pushed. At 11:07:41
WIB, full VM 2D/3D and Joss serial jobs started from that executed source:
wrapper PIDs 18500/18300/46728, respectively. Outputs, launch records, scripts,
51 copied-source SHA-256 records per job and eventual statuses are under
`output/architecture-migration-2026-10-16/p1-full/`. No duplicate baseline runs.
Wrappers automatically compare fixed criteria and audit VM on native success;
completion packing is `.tmp/finish-migration-p1-full.py`. Full G3 is RUNNING.

The replacement continuation entry **mpm-lanjut-migrasi-arsitektur** is ACTIVE.
After the user's reset-time clarification, its first wakeup is 15:14 WIB on
2026-10-16, followed by five-hour intervals. It prioritizes the new architecture
specification and stays quiet on unchanged healthy status. The old entry remains
missing; no duplicate schedule is claimed.

Schedule correction: the user subsequently clarified **13:13 WIB**, superseding
15:13. The active heartbeat was updated to **2026-10-16 13:14 WIB**, then every
five hours; the tool confirmed ACTIVE. Native jobs and numerical settings are
unchanged by this correction.

### User-directed Joss stop and architecture continuation

The user explicitly requested stopping Joss serial and continuing architecture.
Only the Joss process tree was terminated: wrapper 46728, cmd 35268, SBCL 42456
and descendants. Saved `p1-full/joss-serial-status.json` records source `62adb50`,
STOPPED_BY_USER, `complete=false`, `nativeExitCode=null` and
`comparisonStatus=NOT_RUN_CANCELLED`; partial outputs reach 4.2 s. No native
exit code or regression PASS is invented. Historical exact serial `41403f4`
evidence remains separate. No full Joss restart is authorized without a new request.

Full migrated VM 2D on `62adb50` has completed: manifest complete, 480 MPs,
17,443 updates, 51 states, native/comparison/audit exit 0, strict/available-field
audit PASS and zero CSV/position/exported-field differences. VM 3D remains running
under wrapper 18300 and was untouched. Full G3 is PARTIAL; P1 stays PROVISIONAL
and G1 PARTIAL. Collect completed VM evidence separately. The completion collector's
all-three-complete assumption must be corrected before it is run after cancellation.

The user's architecture priority permits independent P3 diagnostics ownership
preparation before P2. A new source split and hash-bound P3 approval are pending;
no P3 move is claimed. P2 native formula migration still needs its native-source/
provenance plan. The cancelled Joss run does not block independent ownership work.
P0 capture/approvals remain immutable, new physics remains deferred, and the active
13:14 WIB/five-hour automation now carries the no-Joss-restart directive.

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

- **Remaining `p6-short/` native compatibility checks (8/8 exit 0; 11/11 total)**:
  `p4-orchestration-002` (4/4), `engine-smoke` (100 MPs, 50 steps), `ownership-normal` (7/7),
  `ownership-legacy` (7/7), `diagnostics-legacy` (3/3), `custom-delegate` (64 MPs, 2 steps,
  80 custom calls, zero position/stress diff, VTK readback), `cliff-mc` (70 MPs, 2 substeps,
  `vtk/mesh.vtk` and `vtk/sim_00001.vtk` byte-identical to `p1`), and `legacy-triaxial`
  (480 MPs, 27 updates, strict comparison exit 0 vs `p4-e`). The initial Windows PowerShell 5.1
  `p4-orchestration` invocation failed at wrapper level (`exitCode: -1`) because PS 5.1 treats
  SBCL `stderr` redefinition warnings under `*>` redirection as `NativeCommandError`; that record
  is retained unchanged alongside the passing `pwsh.exe` run (`p4-orchestration-002`).
  Evidence: `docs/evidence/architecture-migration-2026-10-16/p6-short/` (64 verified hashes).
- **Bounded 4-second serial Joss integration control (`joss-bounded/`, exit 0)**:
  Pre-P2 baseline `before-003` (`a99a4e1` / `7e2aac3`) and canonical final-layout candidate
  `after-001` (`9dfb58b`) both completed 1,658 elastic equilibration steps and 4.0 s physical
  time (`workers=1`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`). All saved VTKs
  (`equilibrium.vtk`, `sim_00001.vtk`, `sim_00002.vtk`) are byte-identical (`SHA-256` match)
  and `compare-framework-runs.py` exited 0 with zero position, scalar-field, or CSV differences.
  Earlier harness failures `before-001` and `before-002` are retained. This bounded 4-second
  control does not replace the user-stopped 40-second run or close full G3.
  Evidence: `docs/evidence/architecture-migration-2026-10-16/joss-bounded/` (54 verified hashes).
- **Full final-layout VM Triaxial 2D and 3D regressions (`p6-full/`, exit 0)**:
  Both `triaxial-2d` (480 MPs, 17,443 updates, 51 states) and `triaxial-3d` (780 MPs, 17,443
  updates, 51 states) completed on `9dfb58b` with `nativeExitCode=0`, `comparisonExitCode=0`,
  and `auditExitCode=0`. Every saved VTK (`51/51` in 2D and `51/51` in 3D) and `stress-strain.csv`
  is byte-identical (`SHA-256` match) to `p1-full` (`62adb50`), with zero position/CSV/field
  differences and independent consistency audits passing.
  Evidence: `docs/evidence/architecture-migration-2026-10-16/p6-full/`.
- **Ownership result ledger (`docs/architecture/FILE_MIGRATION_RESULT.json`)**:
  Created `docs/architecture/COMPONENTS.md` (mapped target of `framework/components/README.md`)
  and ran `scripts/report-architecture-migration.py` without modifying immutable
  `FILE_MIGRATION_MATRIX.json`: `884` original paths accounted for (`812` `RETAINED_UNCHANGED`,
  `14` `RETAINED_MODIFIED`, `58/58` `MAPPED_OWNERS_PRESENT`, `0` pending).
- **Gate summary**: `G0` DONE, `G1` PARTIAL (preserved legacy global overrides in damage/ice,
  concrete forward class, mixed C++ transaction), `G2` DONE, `G3` PARTIAL (full VM 2D/3D and
  bounded 4s serial Joss exact PASS; 40s serial Joss on migrated code remains `STOPPED_BY_USER`;
  historical 4-worker parallel Joss failure remains open), `G4` DEFERRED (new MC H/HS physics
  deferred to separate experimental branch), `G5` DONE for active callers and compatibility shims
  (`framework/` shims retained; two pre-existing missing legacy example files remain `BLOCKED`).

