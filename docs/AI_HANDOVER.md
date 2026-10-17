# AI Engineering Handover — CL-MPM

**Operational checkpoint: 2026-10-17, Asia/Jakarta. Read this first.**
**Milestones M0–M6 of the Mohr–Coulomb Hardening (Model H) vs Hardening–Softening (Model HS)
comparative study are 100% COMPLETE on branch `codex/mc-hardening-softening-study` (branched
from `origin/main` at `e6f9abe` after PR #8 merged the Section 2/5 architecture migration).**
Read [`research/reports/FINAL_HARDENING_SOFTENING_COMPARISON.md`](../research/reports/FINAL_HARDENING_SOFTENING_COMPARISON.md)
and [`research/comparisons/h_vs_hs_metrics.json`](../research/comparisons/h_vs_hs_metrics.json) first:
- **M2 (`materials/models/plastic/mohr-coulomb-evolution/`):** Dedicated `cl-mpm/models/mc-evolution:particle-mc-evolution` supporting `:mc-h` (peak plateau) and `:mc-hs` (piecewise-linear & Urmi et al. 2024 Eq. 2 combined exponential–linear softening), active-set 6-plane Koiter return mapping (`project-principal`), and full native diagnostics (`tests/materials/mc-evolution-points.lisp`: 34/34 PASS).
- **M3 (`research/constitutive-tests/`):** 7 paired constitutive point trajectories (`C-RES-100/200`, `C-RES-URMI-100/200`, `C-ZHAN-50/100`, `C-ZHAN-URMI-50`); pre-peak $\max |q_H - q_{HS}| \le 1.17 \times 10^{-11}\text{ kPa}$, post-peak drop $-69.12\%$ (Resende sand) and $-52.69\%$ (Zhan cliff soil).
- **M4 (`research/triaxial/`):** Paired 3D MPM Triaxial simulations (`T-100-H` vs `T-100-HS`, $780$ 3D GIMP particles, $\sigma_3 = 100\text{ kPa}$); pre-peak $\max |\Delta q| = 5.29 \times 10^{-12}\text{ kPa}$, post-peak at $\varepsilon_a = 14.26\%$: $q_H = 242.39\text{ kPa}$ vs $q_{HS} = 91.31\text{ kPa}$ ($-62.33\%$), 3D shear-band $\kappa_{\max} = 0.6586$ ($4.20\times$ localization), zero mass error, plus side-by-side video `research/triaxial/videos/triaxial_100kpa_h_vs_hs.mp4`.
- **M5 (`research/cliff/`):** Paired 2D MPM Cliff simulations (`L-H` vs `L-HS`, $5,667$ 2D GIMP particles, Master Plan Section 2.5 Zhan cliff parameters + Urmi et al. 2024 two-stage MPM protocol: 200 elastic gravity initialization steps + 875 dynamic steps to $t = 1.93\text{ s}$); Stage-1 & pre-peak identity ($\max |\Delta u| = 0.0\text{ m}$), post-peak progressive shear-band localization ($\kappa_{\max}: 1.7993 \to 4.7737$, $2.65\times$), maximum displacement $3.7089\text{ m} \to 5.6345\text{ m}$ ($+51.92\%$), toe runout $3.2254\text{ m} \to 4.4764\text{ m}$ ($+38.79\%$), crest settlement $3.0225\text{ m} \to 3.6408\text{ m}$ ($+20.46\%$), plus side-by-side video `research/cliff/videos/cliff_h_vs_hs.mp4`.
- **M6 (`research/reports/`, `research/comparisons/`):** Final comparison report, metrics JSON, documentation, and Obsidian/LLM Wiki updated.

**Historical P0–P6 architecture migration note:** P0–P6 architecture ownership migration, Section 2/5 physical folder alignment (`5d6a5cf`),
and two-benchmark verification completed on `codex/material-architecture-migration` and merged into `main` (`e6f9abe`).
Read [NEXT_AI_CHECKPOINT.md](architecture/NEXT_AI_CHECKPOINT.md) and
[STATUS.md](architecture/STATUS.md) for the architecture migration archive.** P1–P5, P4-F canonical root ASDF, and physical
Section 2/5 workspace alignment (`src/` 15 engine subdirectories, `materials/`, `scenarios/`,
`cases/{triaxial,cliff,benchmarks,direct-shear}/`, `framework/` retired, `FILE_MIGRATION_RESULT.json`
with `120/120` mapped owners present) are implemented and validated across all contract suites,
`section2-benchmarks/triaxial-2d` (51/51 VTKs & CSV byte-identical to `p1-full`),
`section2-benchmarks/joss-serial-4s` (byte-identical to `before-003`), and
`section2-benchmarks/joss-collapse` (progressive bottom-to-top cliff damage verified via
`audit-particle-damage.py`). G1 and G3 remain `PARTIAL`.
Refresh this fork's live branches/PRs before changes. Detailed earlier history is
preserved in [the archived handover](archive/AI_HANDOVER_BEFORE_M0_2026-10-16.md).
Older statuses there are historical and do not override this checkpoint.

## Mission and authorized scope

The [architecture migration specification](architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md) (M0) and the
[scientific master plan](../research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md) (M1–M6) are now implemented and verified on
`codex/mc-hardening-softening-study`. See [Research status](../research/README.md) and
[Final Comparison Report](../research/reports/FINAL_HARDENING_SOFTENING_COMPARISON.md) for full details.

P0 inventory is complete: 884/884 captured paths, 104 ASDF systems, 11 audit
integrity tests PASS. At that original capture, the two hash-bound sources in
`docs/architecture/MIGRATION_APPROVALS.json` were approved for the
`P1_CONTRACT_EXTRACTION.md` plan. Later P2/P3/P4 plans separately
bind their reviewed sources and do not rewrite that immutable P0 capture.
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

### P4-F and P6 final completion checkpoint — 2026-10-17 (Asia/Jakarta)

Resumed from `9dfb58b` without repeating already-passed checks:
- **All 11 `p6-short/` native checks PASS (`exit 0`, 64 verified artifacts)**:
  `case-snapshot` (3/3), `native-snapshot` (7/7), `standalone-triaxial` (3/3),
  `p4-orchestration-002` (4/4; initial PS 5.1 stderr redirection failure `p4-orchestration`
  retained unchanged), `engine-smoke` (100 MPs, 50 steps), `ownership-normal` (7/7),
  `ownership-legacy` (7/7), `diagnostics-legacy` (3/3), `custom-delegate` (64 MPs, 2 steps,
  80 custom calls, zero diff, VTK readback), `cliff-mc` (70 MPs, 2 substeps, byte-identical
  `vtk/mesh.vtk` and `vtk/sim_00001.vtk` vs P1), and `legacy-triaxial` (480 MPs, 27 updates,
  strict comparison PASS vs P4-E), plus Node syntax check and 36/36 tests passing (`p4-f-node/`).
- **Bounded 4-second serial Joss control PASS (`joss-bounded/`, 54 verified artifacts)**:
  Pre-P2 baseline `before-003` (`a99a4e1` / `7e2aac3`) and final canonical candidate
  `after-001` (`9dfb58b`) both completed 1,658 elastic equilibration steps and 4.0 s
  physical time (`exit 0`), with byte-identical `equilibrium.vtk`, `sim_00001.vtk`, and
  `sim_00002.vtk` and zero position/field/CSV differences. Earlier harness failures
  `before-001` and `before-002` are retained.
- **Full final-layout VM Triaxial 2D and 3D regressions PASS (`p6-full/`, 38 verified artifacts)**:
  Both `triaxial-2d` (480 MPs, 17,443 updates, 51 states) and `triaxial-3d` (780 MPs,
  17,443 updates, 51 states) completed on `9dfb58b` with `nativeExitCode=0`,
  `comparisonExitCode=0`, and `auditExitCode=0`; all 51 VTKs per run and `stress-strain.csv`
  are byte-identical to `p1-full` (`62adb50`), with zero position/CSV/field differences
  and independent audits passing.
- **Final path/hash ledger (`docs/architecture/FILE_MIGRATION_RESULT.json`)**:
  Accounts for all 884 original P0 paths without modifying `FILE_MIGRATION_MATRIX.json`:
  `812` `RETAINED_UNCHANGED`, `14` `RETAINED_MODIFIED`, `58/58` `MAPPED_OWNERS_PRESENT` (`0` pending).
- **Gate status**: `G0` DONE, `G1` PARTIAL, `G2` DONE, `G3` PARTIAL (full 40s Joss on
  migrated code remains `STOPPED_BY_USER` at 4.2 s and was not restarted; historical
  4-worker parallel Joss failure remains open), `G4` DEFERRED (new MC H/HS physics
  deferred to a separate experimental branch), `G5` DONE for active callers and physical
  Section 2 layout (two pre-existing missing legacy examples remain `BLOCKED`).

### Section 2/5 physical folder alignment and two-benchmark validation — 2026-10-17

Following explicit user direction (`"pokoknya ikuti struktur folder di dokemen final nya, setelah itu kamu uji coba dengan 2 benchmark kita triaxial 2d dan tebing yang rusak dari bawah keatas"`), the workspace directory tree in `D:\MPM` was physically aligned with Section 2 and Section 5 of `CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md` (`5d6a5cf`):
- Retired `framework/` (`39` legacy shims), `src/models/`, and root `src/` shims; organized `src/` into the 15 Section 2 engine subdirectories (`core`, `geometry`, `discretization`, `transfer`, `boundaries`, `loading`, `solvers`, `formulations`, `stabilization`, `damage`, `numerics`, `parallel`, `simulation`, `measurements`, `output`); organized `cases/` into `cases/{triaxial,cliff,benchmarks,direct-shear}/` with automatic flat-path fallback in `snapshot-resolve-case-file`; added `materials/cl-mpm-materials.asd` and all Section 2 subdirectories.
- Updated `docs/architecture/FILE_MIGRATION_RESULT.json` and `FILE_MIGRATION_MATRIX.md`: `884` original paths accounted for (`749` `RETAINED_UNCHANGED`, `15` `RETAINED_MODIFIED`, `120/120` `MAPPED_OWNERS_PRESENT`, `0` pending).
- Verified all native contract suites (`smoke-test`, `engine-numerics-compat`, `material-ownership-compat` normal/legacy, `p4-orchestration-compat`, `framework-components`, `config-contracts`, `material-diagnostics`, `p4-standalone-triaxial-compat`, `case-snapshot-contracts`, `native-snapshot-contracts`) and Studio Node `npm run check` + `npm test` (`36/36 PASS`).
- **Benchmark 1 — Triaxial 2D (`cases/triaxial/triaxial-clay-2d.lisp`, exit 0)**:
  Ran to `output/architecture-migration-2026-10-16/section2-benchmarks/triaxial-2d` (480 MPs, 17,443 updates, 51 saved VTK frames); `compare-framework-runs.py` against `p1-full/triaxial-2d` passed (`max_position_difference_m = 0.0`), all 51 VTKs and `stress-strain.csv` are byte-identical (`SHA-256` match), and `audit-triaxial.py` passed (`passed_consistency_checks = true`).
- **Benchmark 2 — Progressive bottom-to-top chalk cliff failure (`tests/cases/joss-serial-integration.lisp` and `cases/benchmarks/joss-collapse.lisp`)**:
  - `section2-benchmarks/joss-serial-4s` (`exit 0`): 1,658 equilibration steps + 4.0 s physical time; `initial.vtk`, `mesh.vtk`, `equilibrium.vtk`, `sim_00001.vtk`, and `sim_00002.vtk` are byte-identical (`SHA-256` match) to `joss-bounded/before-003` (`max_position_difference_m = 0.0`), initiating lower notch/toe damage ($y = 3.625\text{ m} \le 4\text{ m}$, `lower_max_damage = 0.3336`) while upper cliff damage ($y \ge 9\text{ m}$) is `0.0`.
  - `section2-benchmarks/joss-collapse`: `audit-particle-damage.py` confirms undamaged equilibrium (`t = 0..2.0 s`), bottom toe/notch initiation at `t = 4.0 s` (`sim_00002.vtk`, `lower_max_damage = 0.3336`, `upper_max_damage = 0.0`), upward propagation across `t = 4.1..5.0 s` (`sim_00003.vtk`..`sim_00012.vtk`), and arrival at the upper cliff face ($y \ge 9\text{ m}$) across `t = 7.0..7.7 s` (`sim_00013.vtk`..`sim_00020.vtk`, `lower_max_damage = 0.6572 -> 0.7150`, `upper_max_damage = 0.0005 -> 0.0772 > 0.05`) with `all_fields_finite = true` and `mass_change_fraction = 0.0`.


