---
title: Upstream development report 2026-10-15
type: synthesis
tags: [cl-mpm, provenance, windows, development]
sources: [docs/UPSTREAM_CHANGE_REPORT.md, docs/evidence/upstream-comparison-2026-10-15/comparison.json]
updated: 2026-10-15
---

# Development against the original repository

The user requested professional documentation of changes from
samjvsutcliffe/cl-mpm, with evidence. The pinned comparison is upstream
`d8e65543c55634b54b9d8edf2a6bcf6082415bdc` to fork
`f7fb2a3322eabf483b3d6cedd2c090b356ca01ca`; the upstream is the exact merge base.
It records 273 added and 5 modified files, 308/313 upstream files identical and
79/80 old src files identical. Core, models, damage, aggregate and Joss sources
are retained, rather than attributed as newly written fork physics.

The report distinguishes vendored third-party code, Windows bootstrap/MPI shim,
the VTK stream fix, Studio controller/custom code safeguards, parameterized
geometry/materials and the reference Joss adapter. Historical native/Node/browser
evidence is separated from scientific validation. Original numerical concerns
remain visible in [[scientific-authenticity-audit-2026-10-15]].

Section 9 records the later triaxial module outside the fixed diff counts; see
[[triaxial-clay-calibration]]. Professional PDF and Markdown sources include
actual solver figures and evidence links. Raw sources remain immutable.
