# AI Engineering Handover — CL-MPM

**Operational checkpoint: 2026-10-16, Asia/Jakarta. Read this first.**
Refresh this fork's live branches/PRs before changes. Detailed earlier history is
preserved in [the archived handover](archive/AI_HANDOVER_BEFORE_M0_2026-10-16.md).
Older statuses there are historical and do not override this checkpoint.

## Mission and authorized scope

Execute [the user's master plan](../research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md)
M0–M6: finish the reusable native framework, verify dedicated Mohr–Coulomb
hardening-only (H) and hardening–softening (HS), then run fair paired 3D triaxial
and soil-cliff comparisons. [Research status](../research/README.md) records gates.

- Work headlessly on Windows. No UI/Studio feature work or thesis framing.
- Preserve legacy numerical defaults. New physics uses a separate experimental
  branch after the framework checkpoint, dedicated classes and actual solver runs.
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

Current branch: **codex/reusable-simulation-framework**.
Latest pushed checkpoint: **`64f47cc`**, including the generic material/config
contracts and M1 reference preparation. Earlier implementation/evidence
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
| Bounded current-head integration | PASS | Joss 4 s and triaxial 27 updates on `9f26cb1`; native MC cliff two updates on `0fece3b` |
| M1 reference-data preparation | PASS, data only | Nine stdlib integrity tests; four reference proposals remain non-executable |
| Generic material diagnostics | PASS, focused | Nine native contracts; VM/MC/elastic identity, diagnostics, mode rejection and bounded native MC smoke |
| Configuration contracts | PASS | Ten native checks; validation before output, JSON integrity and config isolation |
| Legacy 3D matched regression | AFTER RUNNING | Original completed exit 0 at 22:26:38 UTC, 17,443 updates and 51 states; frozen `64f47cc` after run last observed at frame 29/50 |
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

## Current native jobs and next bounded action

Run root: `output/material-contract-2026-10-16/`.
- Original 3D baseline: `triaxial-3d-before/`; **completed exit 0 at
  22:26:38 UTC**, 17,443 updates and 51 states.
- Before status: `triaxial-3d-before-status.json`; log: `triaxial-3d-before.log`.
- Frozen original monolith: `output/framework-refactor-2026-10-15/baseline-source/calibration/triaxial.lisp`
  from `c749d32`; helper copies then loads those exact bytes.
- Config: `triaxial-3d-serial.json`, original 3D recipe with workers=1 and
  OPENBLAS_NUM_THREADS=1 / OMP_NUM_THREADS=1. No physics change.
- Current 3D after run: `triaxial-3d-after/`, frozen **`64f47cc`**; wrapper PID
  **42300**, last observed at **frame 29/50**. After status:
  `triaxial-3d-after-status.json`; log: `triaxial-3d-after.log`.
- After case: `tests/cases/triaxial-3d-regression.lisp`. The generic/config
  implementation was committed and pushed before its full regressions.
- Current `64f47cc` full 2D comparison and audit have already passed: 51 VTKs
  byte-identical and all CSV differences zero. Do not repeat that run.

The completion collector **`.tmp/finalize-material-contract.py` is ready**.
Never run it until both 3D statuses report exit 0 and both native manifests
report complete. Inspect status and the final log line once; while the after
run is healthy, let it continue. Once complete, use the collector to compare
3D VTK/CSV with unchanged tolerances, run the independent audits and package
actual evidence. Then update docs and checkpoint commit/push. Retain honest
PASS/FAIL; no reruns or duplicate native jobs are required. Focused generic
9/9, config 10/10, Node 36/36 and component 10/10 checks already passed.
No new full Joss run is needed when its numerical sources remain unchanged;
prove that source identity rather than relabeling old output.
M0 is **PROVISIONAL**, not complete merely because an exception is documented.
Only then integrate physics on a separate experimental branch, as the plan allows.

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
validation. Preserve the ignored staging directory across sessions. Root must
create the separate physics branch and review/copy selected modules only after
the M0 checkpoint/gate; do not install it into the current framework branch.
See [the M2 design](../research/reports/M2_RETURN_MAPPING_DESIGN.md).

## Architecture and maintenance contracts

Native equations belong in `src/`/native libraries. Framework components own
material/geometry contracts, simulation assembly and diagnostics; scenario modules
own loading/boundaries/measurements; `cases/` holds short trusted executable recipes;
`research/` holds source values, frozen study inputs and reports. No copied
constitutive equations in scenario setup. Material-specific diagnostics must not
apply VM yield formulas to MC. Unsupported homogeneous state/rollback must fail
explicitly until its material adapter is implemented.

The headless system is `framework/cl-mpm-framework.asd`. Historical
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

Existing heartbeat **mpm-lanjut-setelah-reset** is ACTIVE in this chat. Its next
reset-aligned start is **2026-10-16 09:51 WIB**, after the observed account reset
at **09:50:08 WIB**, then every five hours. Preserve its current prompt/preferences;
inspect live limits and real resetsAt before adjusting, never create a duplicate.
Local scheduled work needs the laptop and desktop app running. The schedule does
not change the shared account quota. When usage is nearly exhausted, save a
checkpoint and rely on the next wakeup; do not leave active polling loops.
Notify only for meaningful progress, completion, failure or required input.

Update this concise handover, testing/docs and linked wiki at each checkpoint.
Read `wiki-vault/AGENTS.md` and the llm-wiki/obsidian skills before wiki edits;
maintain index and append-only log, preserve raw sources and personal settings.
For old runner history and security/PR context, use the archived handover and
linked reports instead of repeatedly re-investigating completed work.
