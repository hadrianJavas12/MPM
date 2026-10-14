# Execution Plan — Modular Lisp Presets (2026-10-14)

**Working branch:** `feat/studio-modular-lisp-presets` (based on draft PR #4 branch `feat/studio-custom-constitutive-lisp-export`). **Tracking:** [issue #5](https://github.com/hadrianJavas12/MPM/issues/5). **Status:** v1 implemented on development branch, verification in progress. Main remains unchanged.

## Task order and gates

| Priority | Task | Deliverable / acceptance | Status |
| --- | --- | --- | --- |
| P0 | Recheck baseline/constraints | Read latest code/schema and preserve existing custom model/export security contract | Completed (source review); hosted CI is blocked by account billing |
| P1 | Inert/versioned Lisp module format | Deterministic, strictly parsed module declarations, ownership map and schema validation; no `load`/`eval` | Implemented; 11 tests authored |
| P1 | Selective import/export engine | Export geometry/materials/solver/output only; merge/replace + preview + dependency errors + atomic staged apply | Implemented in pure JS |
| P1 | Multi-module and full preset | Selected-module batch and complete versioned `.lisp` preset including inert custom source, round trip parity | Implemented; Unicode tests authored |
| P1 | Browser UI | Import button, scope/selection, diff, merge/replace and confirmation; non-selected settings remain intact | Implemented; browser automation pending |
| P1 | Tests | Parser rejection incl reader macros, zero/false/SI/enum, conflict/rollback, full preset, syntax checks | 11 regression tests authored; V8 isolated checks; Node CI unavailable |
| P1 | Docs/wiki/handover | Feature docs, root docs index, Obsidian/LLM Wiki index/log, status and next steps | Updated during development; verify final commit links |
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

- 2026-10-14 v1 implementation: added `public/preset-modules.js`, source-independent parser/exporter and preview, `public/index.html` module picker/import UI, `public/app.js` staged import/commit + unit conversions, and eight regression tests. JS syntax and selected behavior checked in an isolated V8 environment. Hosted CI currently blocked by account billing; no real browser/full Windows numerical run performed.

- 2026-10-14 final checkpoint: [Draft PR #6](https://github.com/hadrianJavas12/MPM/pull/6) opened against PR #4 branch. Eleven modular preset test cases passed in a V8 isolate with explicit UTF-8/assertion stubs. Syntax and source/UI bindings reviewed. Full native Node, hosted CI (billing lock), browser automation, full Windows MPM test gates remain open. Import does not execute Lisp. 

- 2026-10-14 extra milestone: users may import **only selected modules from one full preset file** via a checkbox; all other modules and source remain untouched. Added schema-ownership coverage and custom-source export completeness checks. 11/11 modular tests passed in the V8 isolated harness, syntax and HTML bindings checked. PR #6 remains draft; native Node/browser/SBCL physics gates remain open.
