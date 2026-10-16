# AI Engineering Handover — CL-MPM

**Operational checkpoint: 2026-10-16, Asia/Jakarta. Read this first.**
Refresh this fork's live branches/PRs before changes. Detailed earlier history is
preserved in [the archived handover](archive/AI_HANDOVER_BEFORE_M0_2026-10-16.md).
Older statuses there are historical and do not override this checkpoint.

## Mission and authorized scope

The immediate priority is the [architecture migration specification](architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md):
continue actual ownership migration after the bounded P1 extraction. Root
`materials/` is the target owner of material models, state, evolution and model
diagnostics; `framework/` remains a compatibility layer until its callers and
numerical behavior are verified. P1 contracts and P3 diagnostics ownership are
implemented; native constitutive/state/evolution ownership remains pending.
The [scientific master plan](../research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md)
M0–M6 remains in force, with new MC H/HS physics deferred until migration gates.
[Research status](../research/README.md) records the separate gates.

P0 inventory is now complete: 884/884 captured paths, 104 ASDF systems, 11 audit
integrity tests PASS. Only the two hash-bound sources in
`docs/architecture/MIGRATION_APPROVALS.json` are approved for the
`P1_CONTRACT_EXTRACTION.md` plan.
The full material form audit preserves existing forward classes/overrides.
Two absent legacy example paths are recorded as pre-existing compatibility
exceptions. P0 was committed/pushed as **6f15148 before production moves**.
P1 was committed/pushed as **3cd172e before testing**. It extracts the approved
contracts into `src/simulation/components/{base,specifications}.lisp`,
`materials/core/definition.lisp` and `materials/adapters/native.lisp`.
All 16 defining-form bodies and the whole native factory file retain exact bytes;
class/package symbols, old path shims and ASDF IDs remain compatible. Focused
contracts and bounded controls pass; P1 remains PROVISIONAL, G1 PARTIAL, full G3 pending.
Before-source/hash evidence is under `output/architecture-migration-2026-10-16/`.
The P0 matrix and hash-bound pre-extraction approvals are immutable; do not
regenerate them from the deliberately changed post-extraction working tree.

- Work headlessly on Windows. No UI/Studio feature work or thesis framing.
- Preserve equations, algorithms, parameter defaults and numerical results during
  migration. New physics requires a separate experimental branch and review.
- No fitting to slide curves, hidden strain multipliers, invented lab data or
  claims of full CU/experimental validation. Residual soil and the separate
  Zhan/Zang reference remain distinct datasets.
- Commit cohesive changes and push each stage. Never merge main, force-push or
  discard local work. A passing deterministic control does not erase a failed run.
- Explain significant problems before new expensive investigation. Avoid repeat
  tests and active polling; inspect saved status/logs before starting native jobs.
- Delete only proven unused files. Preserve compatibility entry points, failed
  evidence, raw sources and personal Obsidian settings. The cleanup inventory
  found no safe deletion candidate; do not equate no search match with disuse.

## Repository and checkpoint topology

Current branch: **codex/material-architecture-migration**, created from
**`7c399fb`** on `codex/reusable-simulation-framework`. Full material/config
regressions executed frozen **`64f47cc`**, with M1 reference preparation.
Earlier implementation/evidence
`4d141c3`, master-plan intake `909fddf` and later documentation checkpoints are
historical ancestors. Attribute each run to its frozen executed source.
Main remains `efd0358b7f571e738c0ecc022c4313fb7fca0d15` after the user's PR #7 merge.
Live GitHub status refreshed on 2026-10-16: draft PRs #2/#3/#4 and separate #6
remain open; no framework PR or merge is claimed. Do not synchronize upstream
as part of this work. The internal engine is the current numerical baseline.

The user requested implementation committed before validation: `66ea5fb` met
that order. Full original post-refactor runs loaded frozen snapshot `2f6476f`;
later bounded integrations used `9f26cb1`, and the distinct MC integration case
was committed as `0fece3b`. Attribute evidence to its executed bytes.

## Verified evidence and open acceptance gates

| Check | Result | Exact scope |
| --- | --- | --- |
| Legacy triaxial 2D | PASS, exact | Snapshot `2f6476f`; 480 MPs, 17,443 updates, 51 VTK hashes identical, all CSV differences zero |
| Current `64f47cc` full triaxial 2D | PASS, exact | All 51 corresponding VTKs identical, all CSV differences zero; independent audit PASS |
| Joss four-worker 40 s | FAIL, retained | Fresh original 176 versus after 191 states; fixed pointwise tolerances fail |
| Joss serial 40 s | PASS, exact | Original `c749d32` versus executed after `41403f4`; 191 physical states, 193 VTKs incl initial/equilibrium, all fields/CSV differences zero |
| Current Node suite | PASS | 36 tests, zero skipped; no UI session or scientific validation |
| Current component contracts | PASS | 10 construction contracts; private callback contract also passed |
| Earlier bounded integration | PASS | Joss 4 s and triaxial 27 updates on `9f26cb1`; native MC cliff two updates on `0fece3b` |
| M1 reference-data preparation | PASS, data only | Nine stdlib integrity tests; four reference proposals remain non-executable |
| Generic material diagnostics | PASS, focused | Nine native contracts; VM/MC/elastic identity, diagnostics, mode rejection and bounded native MC smoke |
| Configuration contracts | PASS | Ten native checks; validation before output, JSON integrity and config isolation |
| Current `64f47cc` full triaxial 3D | PASS, exact | Both exit 0; 780 MPs, 17,443 updates, 51 VTKs byte-identical, all CSV/position differences zero; independent audits PASS |
| Isolated M2 prototype | PASS, provisional points only | 32 native material-point tests; ignored staging directory only, not installed or spatially validated |

Serial Joss has 4,155 MPs, constant mass 425,664.0625 kg per unit depth, finite
arrays and 496 protected-base MPs with zero damage. The after status records
`909fddf` because the wrapper reads HEAD at completion; audited executed snapshot
is **41403f4**, not that completion-time HEAD. See
[the serial report](../research/reports/M0_SERIAL_REGRESSION.md) and
[retained evidence](evidence/framework-refactor-2026-10-15/README.md).
All 134 evidence-manifest hashes verify. The four-worker FAIL is unchanged.
Serial success establishes this control's equivalence; the exact parallel cause
and deterministic parallel execution are not proven.

2D is a 70 × 140 mm **plane-strain rectangle of unit thickness**, not axisymmetry.
Its exporter omits sigma_zz/out-of-plane velocity/displacement; independent full
qJ2 reconstruction is unavailable. Native Fzz assertions and the exact CSV curve
remain distinct evidence. The initial one-MP/cell 2D particle-loss failure is
retained; both passing versions use two MPs per cell direction.
Scientific caveats from [the authenticity audit](SCIENTIFIC_AUDIT_2026-10-15.md)
remain open: no experimental calibration, mesh convergence or closed energy
budget is established by regression or visually similar collapse.

## Completed native evidence and next bounded action

The earlier `64f47cc` jobs completed. The collector finished and packaged
[the material-contract summary](evidence/material-contract-2026-10-16/validation-summary.json)
and 60 SHA-256-verified manifest entries. Full 2D (480 MPs) and 3D (780 MPs)
pairs each completed 17,443 updates, 51 states and 0.2 s. Every corresponding
VTK is byte-identical, all CSV/position differences are zero, and all independent
audits pass within their available-field scope. The 3D original `c749d32`
finished at 22:26:38 UTC; frozen `64f47cc` after finished at 22:44:48 UTC on
2026-10-15, both exit 0. Working outputs remain in
`output/material-contract-2026-10-16/`; do not repeat these runs.

The [Joss source comparison](evidence/material-contract-2026-10-16/verification/joss-numerical-source-identity.json)
proves byte identity only for the listed dedicated numerical modules versus
serial snapshot `41403f4`; it is **not** a new full Joss run on `64f47cc`.
M0 remains **PROVISIONAL**: four-worker strict FAIL is retained and complete
transitive loaded FASL/DLL provenance is not established.

The [P1 bounded evidence](evidence/architecture-migration-2026-10-16/p1/README.md)
contains 32 hash-verified artifacts: 10 framework, 10 configuration, 9 material,
36 Node (zero skipped), 7 normal/7 legacy ownership and 3 snapshot checks pass.
VM 27-update and native MC two-update triaxial controls each have two states,
strict PASS and zero CSV/position differences. Both native MC cliff VTKs match
the prior control exactly; its gnuplot PNG is unavailable, so plotting is not PASS.
Retain both initial test-fixture failures: original-source control proves SBCL's
`SLOT-OBJECT` tail pre-existed; the escape fixture's registry preference was wrong.
Only tests/fixtures were corrected; the containment guard and numerical code were not relaxed.

Bounded evidence/tests were committed and pushed as **62adb50**. Full VM 2D/3D
and serial Joss launched at **11:07:41 WIB** on that fixed copied snapshot under
`output/architecture-migration-2026-10-16/p1-full/{triaxial-2d,triaxial-3d,joss-serial}/`.
Full VM 2D completed: manifest `complete=true`, 480 MPs, 17,443 updates and 51
states; native/comparison/audit exit codes are all 0, strict comparison and
available-field audit PASS with zero position/exported-field/CSV differences.
VM 3D remains running under wrapper **18300**, untouched by the stop request;
no 3D result is claimed yet. Read saved status/logs before any action.

The user explicitly stopped the migrated Joss serial run and prioritized
architecture. Only its process tree (wrapper **46728**, cmd **35268**, SBCL
**42456** and descendants) was terminated. `joss-serial-status.json` records
**STOPPED_BY_USER**, `complete=false`, `nativeExitCode=null` and
`comparisonStatus=NOT_RUN_CANCELLED`; retained output reaches 4.2 s.
This is partial evidence, not PASS or a fabricated native failure code.
The exact `41403f4` serial control remains historical evidence. **Do not restart
or repeat full Joss without a new user request**, including from automation.
51 copied files per run are hashed in `source-snapshots-sha256.json`.

Collect completed VM evidence separately from cancelled Joss. Do not run
`.tmp/finish-migration-p1-full.py` unchanged: its all-three-complete assumption
must first handle user cancellation honestly. Full G3 is PARTIAL, P1 PROVISIONAL
and G1 PARTIAL. The cancelled full Joss run is not a prerequisite for independent
ownership work under the user's latest direction.

Next is independent **P3 diagnostics ownership preparation**: review the source
split and obtain fresh hash-bound approval before implementation. P2 native
formula migration still needs a native-source/provenance plan and remains plan
only; P3 can proceed first. P0 matrix/approval capture is immutable. P2–P6
implementation remains NOT_RUN at this checkpoint; new MC physics stays deferred.

## Isolated M2 preparation checkpoint

**`.tmp/mc-evolution-stage/` is saved but NOT installed or registered.** It holds
five staged Lisp modules (`package`, `law`, `projection`, `state`, `material`),
focused native point tests, `README.md`, `status.json` with source hashes and
`native-points-001.log`. Actual Windows SBCL result: **32/32 tests PASS, exit 0**.
No tracked engine/framework registration, DLL rebuild or full MPM run was made.

This is a dedicated MC H/HS point prototype with coupled strength/kappa,
zero-friction handling, explicit stress/strain conventions and deep material
transactions. It remains **PROVISIONAL**: sampled root isolation lacks a global
completeness proof and adaptive continuation/subdivision; material rollback does
not provide whole-MPM global-step rollback. It is not M2 acceptance or scientific
validation. Preserve the ignored staging directory across sessions. Installation
and new full MC runs are deferred until the migration gates; later physics belongs
on a separate experimental branch, not in folder-migration commits.
See [the M2 design](../research/reports/M2_RETURN_MAPPING_DESIGN.md).

## Architecture and maintenance contracts

Current implementation still spans `src/`, native libraries and `framework/`.
The target separates generic engine/numerics/orchestration in `src/`, model-owned
physics/state/evolution/diagnostics in root `materials/`, reusable procedures in
`scenarios/`, short recipes in `cases/` and scientific inputs/evidence in `research/`.
Material definitions are parameter/provenance profiles, distinct from models;
evolution stays with its model and shared utilities require actual cross-model
reuse. Audit mixed files per form rather than renaming by filename. No duplicate
classes, circular ASDF dependencies or scenario-owned constitutive equations.
MC diagnostics must not use VM formulas; unsupported state/rollback fails explicitly.

The current headless system is `framework/cl-mpm-framework.asd`. Preserve its
public symbols and historical quickload paths until compatibility gate G5 passes.
Remove `framework/` only after active callers transition with evidence. Historical
`calibration/triaxial.lisp` and Studio Lisp files remain compatibility adapters.
`studio/schema.json` remains the existing canonical legacy parameter contract;
new research proposals are separate, execution-gated data. Arbitrary case/custom
Lisp is unrestricted local OS code: trust/opt-in rules still apply.

## Reference sources and milestone progression

Master-plan copy SHA-256:
`e71ae777cf126bef9b48fc7f2c9435b234b4b7842a384accb10d57de7b8b3e7d`.
The 28-page residual-soil PDF is in Downloads and matches
`acd60b668e3b6ed8c7a7378ae3afd053ca0419f4ed63aecc0031b019495f3979`.
Source values, unit conversions, page-specific caveats and disabled H/HS proposals
are in `research/references/` and `research/configs/`. Raw phi=0/c=0 remains raw;
native apex/strain conventions must be verified before enabling those inputs.
The source's missing Zhan prepeak strength and Zhan/Zang naming discrepancy remain
explicit. No source PDF, curve fitting or synthetic lab observations are published.

M1 is complete as reference-data preparation only. M2 has the isolated
provisional point prototype above; installation, full return-map acceptance
and spatial validation remain pending. M3–M6 comparative runs remain NOT RUN:
matched 3D cylinders at 100/200 kPa, a separate matched soil cliff, sensitivity,
quantitative report and human handoff. No UI task is authorized.

## Automation and economical continuation

The former heartbeat was missing. In accordance with the user's standing
auto-continuation request, replacement **mpm-lanjut-migrasi-arsitektur** is now
ACTIVE. The user corrected the reset to **13:13 WIB**; its wakeup is anchored to
**2026-10-16 13:14 WIB**, then every five hours. The tool confirmed the correction.
The updated prompt prioritizes architecture and explicitly forbids restarting
the user-stopped full Joss run without a new request. It reads current VM status
before any action. Do not create another automation. Save checkpoints
when usage is low; avoid active polling, repeated tests and duplicate native jobs.
Notify only for meaningful progress, completion, failure or necessary user input.

Update this concise handover, testing/docs and linked wiki at each checkpoint.
Read `wiki-vault/AGENTS.md` and the llm-wiki/obsidian skills before wiki edits;
maintain index and append-only log, preserve raw sources and personal settings.
For old runner history and security/PR context, use the archived handover and
linked reports instead of repeatedly re-investigating completed work.

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
