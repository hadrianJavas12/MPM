# CL-MPM Studio: Modular Lisp Preset Import/Export

**Implemented on feature branch `feat/studio-modular-lisp-presets`, not merged into `main`.** This
feature handles *configuration modules*, not general Common Lisp programs.
It does **not** add missing physics editors for boundary conditions, loads,
dynamic phases, or multi-material zones.

## How to use in the browser

Open **Import / Export Modul .lisp & Preset** in the left-side Studio panel.

1. Select **Geometry**, **Materials**, **Solver**, **Output**, and/or
   **Custom Lisp source** for export.
2. Choose **Export Modul Terpilih** for exactly those modules, or
   **Export Preset Lengkap** to download every currently supported module
   in one file.
3. To import, select a supported `.lisp` file. Studio stages its contents
   and shows the module names and **before -> after** differences. For a full
   or multi-module file, turn on **Import hanya modul yang dicentang** and
   select which declared modules to apply; unchecked modules are ignored.
4. Choose **Merge** (only fields explicitly present in imported modules
   change) or **Replace** (missing fields of imported modules reset to their
   schema defaults). **Other modules are never reset.**
5. Click **Terapkan Import** to commit the staged changes to the UI, or
   **Batalkan** to discard them. If the current UI has changed since the
   preview, repeat the preview before applying.
6. Only a separate simulation run executes physics. Imported custom-model
   source remains inert until a user opts in to local execution explicitly.

Existing **Export simulation.lisp** continues to create a *runnable*
simulation script. The new exported `full-studio-preset.lisp` is instead a
**data file importable by Studio**. Do **not** launch declarative preset
files using SBCL.

## Module ownership (v1)

| Module ID | Owned schema keys |
| --- | --- |
| `geometry` | shelfHeight, shelfAspect, cliffSlope, undercut, notchHeight, notchDepth, notchShape, notchTipFraction, soilBoundary |
| `materials` | density, E, nu, frictionAngle, cohesion, dilatancyAngle, nonlocalLength, ductility, initiationStress, delayTime, enablePlasticity, enableDamage, constitutiveModel |
| `solver` | meshSize, mpsPerCell, maxSteps, substeps, workers |
| `output` | plotMode |
| `constitutive-source` | Source bytes from the custom Lisp editor, **not executable** during import |

The legacy Studio schema remains the source of truth for SI units, numeric
limits, enum values and defaults, and `studio/public/config.js` handles
normalization of UI configuration. Source belongs to a separate module and
is preserved when not selected.

## Portable declarative syntax

The v1 format is intentionally a **restricted, line-oriented Lisp-shaped
data format**, not arbitrary Common Lisp.

Example `geometry.lisp`:

```lisp
;;;; CL-MPM Studio declarative module v1 (inert data)
(studio-module :version 1 :id :geometry)
(param :shelfHeight 100d0)
(param :soilBoundary 0d0)
(param :notchShape :triangle)
(end-module)
```

When the user imports the example in **Merge** mode, only those three keys
change; all remaining Geometry fields and all material/solver/output
settings are preserved. In **Replace** mode, other Geometry keys reset to
schema defaults, but unrelated modules still remain intact.

Example two-module bundle:

```lisp
(studio-preset :version 1)
(studio-module :version 1 :id :geometry)
(param :shelfHeight 100d0)
(end-module)
(studio-module :version 1 :id :solver)
(param :workers 4)
(end-module)
(end-preset)
```

A complete export includes **all five module IDs**, preserving SI-valued
settings and source. The `constitutive-source` module stores source bytes
as a UTF-8 hexadecimal string in `(source-hex "...")`: it can be restored
exactly without executing code. For human-editable custom model code, use
the existing **Export custom-model.lisp** editor action.

The import parser accepts only exact versioned module/preset headers,
`(param :key value)`, `(source-hex "...")`, and closing forms. It
rejects other Lisp forms, reader macros, duplicate IDs/keys, unknown
module-owned keys, non-finite/out-of-range numbers and invalid enum
values. It never calls `load`, `eval` or a Lisp reader.

## Dependency and safety rules

- A configuration selecting `constitutiveModel = custom` must have
  corresponding nonempty source in the staged result, or import is rejected.
- Source code is always replaced as one unit when its module is imported
  (there is no safe code-level merge).
- Source limit: **32 KiB**; preset-file limit: **128 KiB**.
- Import is **browser-only, non-executing**. This is a parser of a safe,
  limited interchange format, not a sandbox for Common Lisp.
- Running actual custom source remains protected by the default-deny local
  opt-in described in [CUSTOM_MODELS.md](CUSTOM_MODELS.md).
- The format is v1 and is a new contract; arbitrary legacy `.lisp` is
  intentionally **not** auto-detected or executed.

## Testing, limitations and roadmap

The Node regression tests are in `studio/test/preset-modules.test.js`.
Run `cd studio && npm run check && npm test`. They cover selective import from a full file, partial/module
isolation, merge/replace, all-module Unicode source round-trip, malicious
reader syntax, bounds and staged rollback. GitHub Actions is currently
blocked by an account billing issue; its failure must not be conflated with
a failing test suite. A limited JS-isolate verification is reported in the
AI handover; complete browser automation and Windows SBCL/physics validation
have not yet been performed.

Modules for Boundary Conditions, Loading, Simulation Phases, freeform
geometry, multi-material zones, advanced outputs and multi-file ZIP
bundling **remain future work**. See [the broader design](../docs/MODULAR_LISP_IO.md)
and [issue #5](https://github.com/hadrianJavas12/MPM/issues/5).
