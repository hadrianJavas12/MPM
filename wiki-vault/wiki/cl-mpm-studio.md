---
title: CL-MPM Studio
type: entity
tags: [studio, ui, nodejs]
sources: ["[[refactor-2026-10-14]]"]
updated: 2026-10-14
---

# CL-MPM Studio

Web UI for a 2D cliff-collapse chalk simulation. `studio/public/` (frontend) → `studio/server.js` (zero-dependency Node ≥18, 127.0.0.1:3000) → `windows\cl-mpm.cmd studio\lisp\run.lisp` (ASDF system `cl-mpm-studio`). `studio/schema.json` is the single source of parameters for server and runner. Output in `output/studio/{frames,vtk,video.mp4}`.

Changes vs the Gemini version: `fractureEnergy` (not a model parameter) replaced by `ductility`; logs are cursor based; no hardcoded paths; path traversal rejected.

[[refactor-2026-10-14]] reports end-to-end verification of the earlier Windows
port (run/logs/frames/VTK/video/double-run rejection). That historical source
does not validate subsequent custom-model changes. Current evidence: 33
Node/SBCL contract tests passed with explicit dependency stubs; hosted Actions
blocked by account billing. Full Windows/custom physics remains unverified.

Current controls: [[studio-geometry-material]]. Trusted Lisp workspace/export:
[[studio-custom-models]]. Test scope and next handover:
[[studio-verification-2026-10-14]]. Docs: `docs/studio.md`, `docs/testing.md`,
`docs/AI_HANDOVER.md`. Parent: [[cl-mpm]].
