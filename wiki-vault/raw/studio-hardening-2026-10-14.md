---
title: Studio hardening evidence 2026-10-14
type: source
tags: [studio, verification, handover]
sources: [docs/testing.md, docs/AI_HANDOVER.md, studio/test/]
updated: 2026-10-14
---

# Studio hardening evidence — 2026-10-14

Immutable session record. Repository: https://github.com/hadrianJavas12/MPM
Branch: `feat/studio-custom-constitutive-lisp-export`; draft PR #4 targets
`feat/studio-material-parameter-controls`. Baseline commit:
`95ded55b9fee22d9e5871d12d5bd09174a8a401f`. PRs #1–#4 were open drafts;
the branch included all ancestors and was 39 commits ahead of main, zero behind.

Captured results: baseline `npm run check` and 22 Node tests passed. Hardening
`npm run check` and `npm test` with required SBCL tests passed **33/33**, zero
failed/skipped, on Linux with Node 24.19.0 and SBCL 2.2.9. Production config and
custom-loader Lisp files were compiled and their CLOS/export behaviour exercised.
JSON/matrix/Quicklisp/runner dependencies were explicitly stubbed. API child
launches were mocked. No full-engine numerical or Windows validation was performed.

Confirmed external blocker: run `38509402658`, check `115674197084`.
https://api.github.com/repos/hadrianJavas12/MPM/check-runs/115674197084/annotations
reported that the job was not started because the account is locked due to a
billing issue. It had no steps and no assigned runner. Earlier unknown-cause
notes are superseded; hosted CI was not green.

Implemented: shared schema normalization and complete exports; shared trusted
loader and primary-method contract; finite/type/dimension stress checks;
elastic undamaged/Kirchhoff state handling; particle damage flag; Lisp decimal,
boolean and integer coercion parity; character/escaped-symbol lexical checks;
import errors/reimport; local Host/origin/confirmation/source/body checks;
concurrency/source round-trip regressions. A real-engine Windows custom smoke
script was supplied and only checked lexically. Browser automation could not
run because the binary download failed. Scientific validation remains open.
