---
title: CL-MPM Studio
type: entity
tags: [studio, ui, nodejs]
sources: ["[[refactor-2026-10-14]]", "[[studio-verification-2026-10-14]]", docs/windows-verification-2026-10-14.md]
updated: 2026-10-14
---

# CL-MPM Studio

Web UI for a 2D cliff-collapse chalk simulation. `studio/public/` (frontend) → `studio/server.js` (zero-dependency Node ≥18, 127.0.0.1:3000) → `windows\cl-mpm.cmd studio\lisp\run.lisp` (ASDF system `cl-mpm-studio`). `studio/schema.json` is the single source of parameters for server and runner. Output in `output/studio/{frames,vtk,video.mp4}`.

Changes vs the Gemini version: `fractureEnergy` (not a model parameter) replaced by `ductility`; logs are cursor based; no hardcoded paths; path traversal rejected.

[[refactor-2026-10-14]] reports end-to-end verification of the earlier Windows
port (run/logs/frames/VTK/video/double-run rejection). That historical source
does not validate subsequent custom-model changes. Current native Windows
evidence separately establishes 33 Node/SBCL contract tests, actual launcher
elastic/delegate/PNG smokes, browser delegate execution and unchanged downloaded
export. All 28 settings and exact source matched; mesh + three VTK + three PNG
outputs were byte-identical with finite particle arrays. Setup quoting/init,
Windows VTK stream corruption, missing/partial PNG completion and button SVG
sizing were fixed. Hosted Actions remains blocked by account billing. Physical
calibration, full-engine custom elastic validation and convergence remain open.

Current controls: [[studio-geometry-material]]. Trusted Lisp workspace/export:
[[studio-custom-models]]. Test scope and next handover:
[[studio-verification-2026-10-14]]. Docs: `docs/studio.md`, `docs/testing.md`,
`docs/AI_HANDOVER.md`. Parent: [[cl-mpm]].

The new experimental `joss-bay` path adapts the author Joss example to a
two-segment face, notch, explicit reference material and equilibrium/accelerate/
collapse phases. Named 1 GPa prose and 100 MPa table profiles retain the paper's
ambiguity. The user requested similar geometry/crack/collapse/run-out rather
than numerical identity. Current reference verification is separate from the
earlier delegate/export tests: [[joss-reference-reproduction]].
