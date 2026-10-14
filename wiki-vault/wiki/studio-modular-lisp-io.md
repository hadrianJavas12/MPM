---
title: Modular Lisp import and export
type: concept
tags: [cl-mpm, studio, roadmap, presets, modularity, lisp, import-export]
sources: ["docs/MODULAR_LISP_IO.md", "docs/AI_HANDOVER.md", "https://github.com/hadrianJavas12/MPM/issues/5"]
updated: 2026-10-14
---

# Modular Lisp import/export and complete preset manager

**Status: v1 MVP implemented on the unmerged feature branch `feat/studio-modular-lisp-presets`. Advanced modules remain planned.** User requires that CL-MPM
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

## Implementation update — 2026-10-14

Implemented strict, non-executing declarative Lisp interchange in
`studio/public/preset-modules.js`. Available v1 modules:
`geometry`, `materials`, `solver`, `output` and
`constitutive-source`. One, selected, or all modules can be exported
as versioned `.lisp` data and re-imported through a preview panel.

The UI offers **Merge** (only provided keys) or **Replace** (reset imported
module only) and an explicit Apply/Cancel flow. A full preset includes
an inert hex-encoded UTF-8 copy of the custom source. The exporter for
**runnable** `simulation.lisp` is a separate existing feature. Import
never invokes SBCL or evaluates Common Lisp. Unrecognized legacy scripts
are refused. See `studio/PRESETS.md` and
`docs/EXECUTION_PLAN_MODULAR_PRESETS.md`.

Validation: new Node test cases authored, syntax and isolated V8 checks
performed. Hosted CI still blocked by account billing; no full Windows
SBCL or browser/physics verification. The boundary/loading/phases,
multi-material and advanced output modules are future milestones.

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

The earlier PR #4 included custom constitutive-source import/export and
**run script export** only. The new stacked feature branch implements the
first declarative modular I/O and importable full-preset MVP; it is not merged. Track delivery in [Issue #5](https://github.com/hadrianJavas12/MPM/issues/5)
and [Design Spec](https://github.com/hadrianJavas12/MPM/blob/feat/studio-custom-constitutive-lisp-export/docs/MODULAR_LISP_IO.md).

Related notes: [[cl-mpm-studio]], [[studio-custom-models]],
[[studio-geometry-material]], [[studio-verification-2026-10-14]].
