---
title: Studio verification 2026-10-14
type: synthesis
tags: [studio, tests, ci, decisions, handover]
sources: ["[[studio-hardening-2026-10-14]]", docs/testing.md, docs/AI_HANDOVER.md, docs/windows-verification-2026-10-14.md]
updated: 2026-10-14
---

# Studio verification — 2026-10-14

Working branch: `feat/studio-custom-constitutive-lisp-export`, draft
[PR #4](https://github.com/hadrianJavas12/MPM/pull/4), stacked after #1–#3.
The numerical solver update and `main` were preserved. Mission: a practical Windows
workbench for cliff/notch geometry, configurable constitutive laws and Lisp
authoring/export. The user has explicitly separated this project from their thesis.

| Evidence | Current result | Scope |
| --- | --- | --- |
| JavaScript syntax | Passed | Server and browser source |
| Automated suite | 33 passed, none failed/skipped | Final Windows run: Node 24.13.0, SBCL 2.6.9 |
| SBCL contract tests | Real reader/compiler/CLOS; actual production config/loader | Explicit dependency stubs; separate from the full-engine runs |
| Hosted CI | Blocked by confirmed account billing lock | Job never started; no steps/runner |
| Native elastic smoke | Passed, exit 0 | 100 particles, 50 updates; all positions/velocities/stresses finite; mean y 0.25 → 0.24322331 m |
| Full Windows custom delegate | Passed, exit 0 | 64 final particles, two updates, 80 custom calls, zero position/stress difference; 36 finite VTK scalar arrays |
| gnuplot PNG smoke | Passed, exit 0 | Actual success and failed-output paths; complete PNG checks |
| Browser custom delegate | Passed, exit 0 | UI → launcher → full engine, damage/plasticity on, Finished/100%, three PNGs displayed |
| Actual downloaded export | Passed, exit 0 | Unchanged script from path with spaces; adjacent exact custom source |
| UI/export parity | Passed | 28 config settings and exact source; mesh + three VTK + three PNG byte/hash identical |
| Output parser review | Passed | Fresh files accepted; seven corruptions rejected, including preserved pre-fix VTK |
| Scientific benchmark | Not established | No Joss Bay reproduction or mesh-independent prediction |

Checkout: `D:\MPM\MPM-test`, starting commit
`a2e615712b14154a776dba6839041d34be9465cf`, requested branch unchanged. Fixes
remain local/uncommitted; no push, PR edit or merge. Current report:
`docs/windows-verification-2026-10-14.md`.
Live git checks found the baseline 41 ahead of main, zero behind. Main/lifecycle/
material heads are ancestors; latest geometry head `98eff24` is not. Its fix
already exists through material commit `648ceca` with identical patch ID
`ba608523e5f0068a9e05f23465ce0caccbc60721`; the app contains the update. No
cherry-pick was required. `branch-ancestry.json` preserves the checks.

## Native Windows findings

Toolchain: SBCL 2.6.9, Quicklisp client 2021-02-13/dist 2026-01-01, OpenBLAS
0.3.34, gnuplot 6.0 pl1, ffmpeg 9.0.1. Existing executables were reused;
Quicklisp/OpenBLAS were copied into the independent checkout. Fresh Quicklisp
installation through the real setup function separately passed on Windows
PowerShell 5.1 with spaces in the target path. See [[windows-port]].

Observed failures were fixed: Quicklisp `--eval` quoting and premature user-init
dependency loads; two append streams corrupting binary VTK on Windows;
`save-frame` silently accepting missing/partial/old PNG output; oversized button
SVGs. The VTK writer now uses one octet stream and the renderer checks signature
and IEND after removing any old target. These are I/O/setup/UI changes, not a
new numerical law. Current smoke readback checks every binary block, finite
arrays and point/mass equality with the actual simulation.

The actual UI/export run used three frames, five updates per frame, mesh size
10, one particle per cell, one worker and default damage/plasticity on. Output
counts after splitting were 1120, 1120 and 1309. All 36 scalar fields per frame
were finite, and all seven output files matched exactly. This establishes one
short trusted-delegate reproduction case, not arbitrary-law accuracy or long-run
stability. The specialized parser is not a general VTK reader.

Evidence: `output/windows-verification-2026-10-14/` contains toolchain/setup,
Node/native/plot logs, failed-before/fixed-after VTK evidence, downloaded Lisp,
browser screenshots/status/logs, `ui-run/`, preserved `export-run/`,
`config-parity.json`, `output-parity.json`, and independent parser regression
fixtures. Output is git-ignored; preserve it before removing the checkout.

## Provenance and contradiction handling

[[refactor-2026-10-14]] reports smoke, Studio and VTK/PNG/video verification of
the earlier Windows port. Keep that historical claim attributed to its source.
It did not establish that the later custom branch passed the full Windows
toolchain; the new captured Windows evidence above closes that delegate/export
gate independently. Immutable [[studio-hardening-2026-10-14]] records the earlier
Linux 33/33 dependency-stub tests and unavailable browser; those historical facts
remain unchanged. Older handover notes saying CI's cause was unknown are superseded
by public check annotations identifying an account billing lock. Latest inspected
run `38512874136` / check `115685122821` was again blocked before execution.

## Next handover

1. Read root `AGENTS.md` and `docs/AI_HANDOVER.md`; refresh GitHub heads/bases/status.
2. Repeat syntax and required SBCL contract tests (commands in `docs/testing.md`).
3. Account owner resolves billing before a fresh hosted CI run can be reviewed.
4. Repeat native smoke/PNG/UI-export comparisons after relevant changes. Test
   the experimental custom elastic template under the full engine, then establish
   physical reference cases/calibration and convergence before predictive claims.

Feature details: [[studio-custom-models]], [[studio-geometry-material]],
[[cl-mpm-studio]]. Immutable captured source: [[studio-hardening-2026-10-14]].
