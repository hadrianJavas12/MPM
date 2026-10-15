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
Published implementation/evidence checkpoint: `4d141c3`; master-plan intake
`909fddf` and formatting/index follow-up `49e5cdd` are also pushed.
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
| Joss four-worker 40 s | FAIL, retained | Fresh original 176 versus after 191 states; fixed pointwise tolerances fail |
| Joss serial 40 s | PASS, exact | Original `c749d32` versus executed after `41403f4`; 191 physical states, 193 VTKs incl initial/equilibrium, all fields/CSV differences zero |
| Existing Node suite | PASS | 36 tests, zero skipped; no UI session or scientific validation |
| Existing component contracts | PASS | 10 construction contracts, private triaxial contracts, delegate two-step solver/VTK smoke and Joss units |
| Bounded current-head integration | PASS | Joss 4 s and triaxial 27 updates on `9f26cb1`; native MC cliff two updates on `0fece3b` |
| M1 reference-data preparation | PASS, data only | Nine stdlib integrity tests; four reference proposals remain non-executable |
| New generic material diagnostics | IN PROGRESS | Native VM/MC/elastic protocol being tested; requires current-code regression before acceptance |
| Legacy 3D matched regression | RUNNING | Fresh frozen-original serial baseline described below; current-code after run not yet launched |

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

## Current native job and next bounded action

Run root: `output/material-contract-2026-10-16/`.
- Original 3D baseline: `triaxial-3d-before/`; wrapper PID **4232**.
- Status: `triaxial-3d-before-status.json`; log: `triaxial-3d-before.log`.
- Frozen original monolith: `output/framework-refactor-2026-10-15/baseline-source/calibration/triaxial.lisp`
  from `c749d32`; helper copies then loads those exact bytes.
- Config: `triaxial-3d-serial.json`, original 3D recipe with workers=1 and
  OPENBLAS_NUM_THREADS=1 / OMP_NUM_THREADS=1. No physics change.
- Current after case: `tests/cases/triaxial-3d-regression.lisp`. Commit the generic
  diagnostics implementation before launching its full post-change regressions.

Check status and final log line once. Do not launch duplicate baselines. Finish
focused generic-material tests; then run current 2D and 3D regressions with
matched runtime/configuration, compare VTK/CSV using unchanged tolerances and
retain real PASS/FAIL. No new full Joss run is needed when its numerical sources
remain unchanged; prove that source identity rather than relabeling old output.
M0 is **PROVISIONAL**, not complete merely because an exception is documented.
Only then integrate physics on a separate experimental branch, as the plan allows.

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

M2–M6 remain NOT RUN: dedicated MC evolution/state/return-map verification;
matched 3D cylinders at 100/200 kPa; a separate matched soil cliff; sensitivity,
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
