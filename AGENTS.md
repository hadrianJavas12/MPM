# AI Agent Guide — hadrianJavas12/MPM

**Read [docs/AI_HANDOVER.md](docs/AI_HANDOVER.md) FIRST.** It contains the
current project mission, verified stacked PR topology, architectural contracts,
user goals, testing state, scientific caveats, security policy and priorities.
It is date-stamped: **refresh live GitHub status before making changes**.

## Product intent

Extend the **existing** Common Lisp MPM engine into a practical, Windows-friendly
**CL-MPM Studio** for:
- custom cliff geometry and toe notches;
- selectable and parameterised constitutive models, with an import/edit/export
  workflow for trusted Common Lisp methods;
- reproducible VTK/CSV/PNG simulations that can eventually be benchmarked.

This work is **not connected to the user's thesis**. Do not steer it elsewhere.
Studio is a controller, not a replacement physics engine; never present a
geometry SVG preview or unvalidated custom model as a scientifically validated
simulation.

## Non-negotiable collaboration rules

1. **Inspect actual files and branches** (don't infer repo state from old chats).
2. **Preserve backward-compatible default behaviour** of the original chalk
   and MPM solver, unless changing it is intentional, reviewed and tested.
3. **Don't change `main` or merge any PR without express user direction.**
   PRs #1–#4 form a stacked draft series; see the handover for exact names.
4. Prefer small, cohesive, testable commits and PRs. For a new feature, branch
   from the appropriate ancestor and tell the user which branch contains it.
5. Treat `studio/schema.json` as the canonical parameter specification.
   Keep UI, Node validation, Common Lisp config, and export output consistent.
6. Treat arbitrary Lisp as unrestricted **OS-level code execution**, not
   sandboxed. It must stay disabled by default; local opt-in and explicit user
   confirmation are safeguards only. Never execute untrusted source.
7. Be exact about evidence. Clearly distinguish code review, lexical/static
   checks, actual Node tests, actual SBCL runs and scientific validation.
8. Update `docs/AI_HANDOVER.md` (dated progress, open risks, next actions)
   when handing work to another AI. Also update the Obsidian/LLM Wiki after significant work: read `wiki-vault/AGENTS.md` and the repository llm-wiki/obsidian skills, maintain linked pages, index and append-only log, and preserve immutable raw sources.

## Fast navigation

- `docs/AI_HANDOVER.md` — **operational source of truth for AI handover**
- `wiki-vault/wiki/index.md` — Obsidian/LLM Wiki knowledge index
- `studio/GEOMETRY.md` — cliff/notch coordinates, preview limitations
- `studio/MATERIAL.md` — constitutive parameters and units
- `studio/CUSTOM_MODELS.md` — CLOS extension contract, editor, export, security
- `docs/MODULAR_LISP_IO.md` — **planned** selective module .lisp I/O and complete preset import/export (issue #5; not shipped)
- `studio/schema.json` — shared param keys/defaults/units
- `studio/lisp/scenario.lisp` and `runner.lisp` — actual simulation creation/run
- `studio/public/app.js` and `model-workspace.js` — frontend workflow
- `studio/public/config.js` — shared API/export normalization against schema
- `studio/lisp/custom-model.lisp` — loader, dedicated class and stress contract
- `docs/testing.md` — test levels, repeatable commands and CI blocker
- `studio/server.js` — HTTP, simulation lifecycle, optional custom execution
- `studio/test/` — JS tests; `.github/workflows/studio-node.yml` — CI
- `docs/windows-setup.md` and `docs/development.md` — Windows setup/tests

## Before claiming a change works

```sh
cd studio
npm run check
npm test
```

For physics or custom model updates, additionally **run SBCL on Windows**,
check the VTK output and compare against a reference case. GitHub Actions was
blocked as of 2026-10-14 by an account billing lock (confirmed check annotations).
See the handover for the full verification checklist.
