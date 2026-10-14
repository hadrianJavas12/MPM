---
title: Studio verification 2026-10-14
type: synthesis
tags: [studio, tests, ci, decisions, handover]
sources: ["[[studio-hardening-2026-10-14]]", docs/testing.md, docs/AI_HANDOVER.md]
updated: 2026-10-14
---

# Studio verification — 2026-10-14

Working branch: `feat/studio-custom-constitutive-lisp-export`, draft
[PR #4](https://github.com/hadrianJavas12/MPM/pull/4), stacked after #1–#3.
The original solver and `main` were preserved. Mission: a practical Windows
workbench for cliff/notch geometry, configurable constitutive laws and Lisp
authoring/export. The user has explicitly separated this project from their thesis.

| Evidence | Current result | Scope |
| --- | --- | --- |
| JavaScript syntax | Passed | Server and browser source |
| Automated suite | 33 passed, none failed/skipped | Node 24.19.0, SBCL 2.2.9, Linux |
| SBCL tests | Real reader/compiler/CLOS; actual production config/loader | Dependency stubs; no MPM solver/Quicklisp/OpenBLAS |
| Hosted CI | Blocked by confirmed account billing lock | Job never started; no steps/runner |
| Full Windows custom engine/export parity | Not run | Supplied `scripts/studio-custom-smoke.lisp` remains to execute |
| Browser automation | Not run | Browser binary download failed |
| Scientific benchmark | Not established | No Joss Bay reproduction or mesh-independent prediction |

## Provenance and contradiction handling

[[refactor-2026-10-14]] reports smoke, Studio and VTK/PNG/video verification of
the earlier Windows port. Keep that historical claim attributed to its source.
It does not establish that the later custom branch passed the full Windows
toolchain. Older handover notes saying CI's cause was unknown are superseded
by the public check annotation identifying an account billing lock.

## Next handover

1. Read root `AGENTS.md` and `docs/AI_HANDOVER.md`; refresh GitHub heads/bases/status.
2. Repeat syntax and required SBCL contract tests (commands in `docs/testing.md`).
3. Account owner resolves billing before a fresh hosted CI run can be reviewed.
4. Execute real Windows smoke and exported/UI config/VTK/PNG comparison, then
   establish physical reference cases and convergence before scientific claims.

Feature details: [[studio-custom-models]], [[studio-geometry-material]],
[[cl-mpm-studio]]. Immutable captured source: [[studio-hardening-2026-10-14]].
