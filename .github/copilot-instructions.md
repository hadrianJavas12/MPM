# AI coding instructions for CL-MPM Studio

**Before editing, read the project's canonical guidance:**
- [AGENTS.md](../../AGENTS.md) — expected workflow and non-negotiable constraints.
- [docs/AI_HANDOVER.md](../../docs/AI_HANDOVER.md) — full mission, PR stack,
  architecture, scientific limitations, test status and next steps.

Develop the existing Common Lisp Material Point Method engine and Windows
CL-MPM Studio frontend for parametric cliff geometry, toe notches, and
custom/parameterized material laws with reproducible Lisp exports. Keep model
physics separate from visual previews. Keep schema/JavaScript/Node/Lisp units
and defaults consistent. Do not claim a numerical model is validated based on
static analysis or frontend unit tests. Arbitrary Lisp is not sandboxed;
execution must remain disabled by default.

At handover, update docs/AI_HANDOVER.md with a dated progress entry, the exact
branch/PR, tests actually executed and unresolved issues. Do not merge to
main without user approval.
