# Execution Plan — Modular Lisp Presets (2026-10-14)

**Working branch:** `feat/studio-modular-lisp-presets` (based on draft PR #4 branch `feat/studio-custom-constitutive-lisp-export`). **Tracking:** [issue #5](https://github.com/hadrianJavas12/MPM/issues/5). **Status:** in progress. Main remains unchanged.

## Task order and gates

| Priority | Task | Deliverable / acceptance | Status |
| --- | --- | --- | --- |
| P0 | Recheck baseline/constraints | Read latest code/schema and preserve existing custom model/export security contract | Completed (source review); hosted CI is blocked by account billing |
| P1 | Inert/versioned Lisp module format | Deterministic, strictly parsed module declarations, ownership map and schema validation; no `load`/`eval` | In progress |
| P1 | Selective import/export engine | Export geometry/materials/solver/output only; merge/replace + preview + dependency errors + atomic staged apply | Pending |
| P1 | Multi-module and full preset | Selected-module batch and complete versioned `.lisp` preset including inert custom source, round trip parity | Pending |
| P1 | Browser UI | Import button, scope/selection, diff, merge/replace and confirmation; non-selected settings remain intact | Pending |
| P1 | Tests | Parser rejection incl reader macros, zero/false/SI/enum, conflict/rollback, full preset, syntax checks | Pending |
| P1 | Docs/wiki/handover | Feature docs, root docs index, Obsidian/LLM Wiki index/log, status and next steps | In progress |
| P2 | Windows numerical verification | Real SBCL + solver/UI-export benchmark, ParaView inspection | Blocked pending Windows toolchain access; not to be claimed as completed |
| P2 | Extended physics modules | Boundary/loading/phases/multimaterial/advanced output after corresponding solver adapters | Deferred: not yet exposed in Studio |

## Architectural guardrails

- `studio/schema.json` and `studio/public/config.js` remain canonical for numeric types/ranges/defaults.
- Portable declarative `.lisp` **configuration** is NOT arbitrary executable Common Lisp.
- Import must only parse a strict, inert grammar; no evaluation/reader macros.
- The existing trusted `custom-model.lisp` execution gate is separate, default-deny and NOT sandboxed.
- User must preview and approve; merging only applies present keys to owning module and replacing resets only the chosen module.
- Preserve current built-in chalk/default behaviour and do not touch `main` or merge without approval.
- Record actual evidence; hosted GitHub Actions previously failed due to account billing, not observed Node test failures.

## Running notes

- 2026-10-14 start: branch created, code and existing handover/wiki reviewed. Next action: implement pure module registry and parser; commit tests; then UI.
