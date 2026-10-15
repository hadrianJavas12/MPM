---
title: Modular Lisp import and export
type: concept
tags: [cl-mpm, studio, roadmap, presets, modularity, lisp, import-export]
sources: ["docs/MODULAR_LISP_IO.md", "docs/AI_HANDOVER.md", "https://github.com/hadrianJavas12/MPM/issues/5"]
updated: 2026-10-14
---

# Modular Lisp import/export and complete preset manager

**Status: proposed only (not implemented).** User requires that CL-MPM
Studio be usable through either its GUI or portable Lisp files. Import and
export must be symmetrical for **one specific module**, **multiple selected
modules**, or **the entire preset**.

## User intent / product scope

- A geometry-only `.lisp` import updates geometry and notch settings
  **without changing materials, boundary conditions or solver options**.
- A material-only import likewise must not change geometry.
- Other modules: custom constitutive source, BCs, loading, solver, simulation
  phases and output settings. These need engine adapters if not already
  exposed in Studio; upstream capabilities alone do not make the UI complete.
- Export one module, selected modules, or a full reproducible preset.
- A full preset must also be **importable back into the UI**, not merely a
  generated runnable `simulation.lisp` file.
- Preview changes, select Merge or Replace, then explicitly confirm.
  Apply a multi-module import atomically.

## Key design decisions

1. Build a module registry on `studio/schema.json` and
   `studio/public/config.js`, with owned fields, version, units and deps.
2. Define a **declarative safe Lisp subset** for portable configuration.
   Never `load` arbitrary imported config or evaluate reader macros.
3. Imported custom CLOS model text remains inert until separate local
   opt-in execution; current safeguards do not constitute a sandbox.
4. A complete preset may bundle `.lisp` modules + manifest; record versions
   and all custom code needed to reproduce a run.
5. Run round-trip, field-isolation, unit/enum, dependency and malicious
   reader-macro tests. Separate the physical SBCL benchmark requirement.

## Roadmap and existing features

**P1a:** scalar module registry, safe import/export, previews and atomic apply.
**P1b:** selected modules/full preset manifest and round trips.
**P1c:** source-backed/material-zone/loading/phase adapters with numerical tests.

The current PR #4 has custom constitutive-source import/export and complete
**run script export**, but not general selective module I/O or whole-preset
import. Track delivery in [Issue #5](https://github.com/hadrianJavas12/MPM/issues/5)
and [Design Spec](https://github.com/hadrianJavas12/MPM/blob/feat/studio-custom-constitutive-lisp-export/docs/MODULAR_LISP_IO.md).

Related notes: [[cl-mpm-studio]], [[studio-custom-models]],
[[studio-geometry-material]], [[studio-verification-2026-10-14]].
