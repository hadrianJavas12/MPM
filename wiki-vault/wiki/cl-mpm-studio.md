---
title: CL-MPM Studio
type: entity
tags: [studio, ui, nodejs]
sources: [[[refactor-2026-10-14]]]
updated: 2026-10-14
---

# CL-MPM Studio

Web UI for a 2D cliff-collapse chalk simulation. `studio/public/` (frontend) → `studio/server.js` (zero-dependency Node ≥18, 127.0.0.1:3000) → `windows\cl-mpm.cmd studio\lisp\run.lisp` (ASDF system `cl-mpm-studio`). `studio/schema.json` is the single source of parameters for server and runner. Output in `output/studio/{frames,vtk,video.mp4}`.

Changes vs the Gemini version: `fractureEnergy` (not a model parameter) replaced by `ductility`; logs are cursor based; no hardcoded paths; path traversal rejected.

Verified end-to-end (run, logs, frames, VTK, video, 409 on double run). Docs: `docs/studio.md`. Parent: [[cl-mpm]].
