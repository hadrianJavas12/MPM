# Repository context for Claude / other AI coding assistants

**Start with [AGENTS.md](AGENTS.md) and [docs/AI_HANDOVER.md](docs/AI_HANDOVER.md).**
These two files define current goals, architecture, stacked PR branches, tests,
open risks and collaboration rules. The handover is date-stamped: re-check
GitHub source and PR statuses rather than trusting an old snapshot.

Core intent: improve the existing CL-MPM SBCL numerical engine through the
Windows-friendly CL-MPM Studio frontend. Current user priorities are custom
cliff/notch geometry, configurable constitutive laws and a Common Lisp
import/editor/export workflow; maintain scientific reproducibility and respect
explicit opt-in for unsafe custom code execution.

Never interpret a preview as a numerical simulation, or a static/syntax check
as proof that SBCL runs or scientific numerical results are valid. The
user specifically stated this project is unrelated to their thesis.

**Do not merge a PR or modify `main` without explicit user approval.**
