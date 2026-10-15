# Modular Lisp I/O and full preset portability

**Status: SPECIFICATION ONLY — NOT IMPLEMENTED.** User requirement recorded on 2026-10-14. Existing custom-model .lisp source import/export and runnable simulation.lisp export are separate from the new *selective* module import/export feature.

## Product principle

CL-MPM Studio must support BOTH GUI-assisted configuration and reproducible Lisp-driven workflows. Users can import or export **one module, multiple selected modules, or one complete simulation preset** without copying unrelated settings or manually assembling many files. Imports must never silently overwrite non-selected settings, execute code, or change the physical solver configuration without preview and confirmation.

## Requested modules and readiness

| Module | Examples of portable configuration | Studio status |
| --- | --- | --- |
| geometry | height, slope, overhang, notch shape/depth, eventually custom profile | Existing scalar UI; selective Lisp I/O pending |
| materials | E, nu, density, friction, cohesion, dilation, damage parameters, zone assignment | Single material controls; per-module I/O and multi-material pending |
| constitutive-source | custom CLOS method source with metadata | Existing editor and raw .lisp import/export; module registry pending |
| boundary-conditions | fixed, rollers, prescribed displacement/velocity, region mapping | Engine exists; UI/portable module pending |
| loading | gravity, traction/pressure, contact, staged loads | Fixed gravity in Studio; module pending |
| solver | method, dt, damping, mass scaling, shape function, CPU workers | Some controls exist; advanced settings/module pending |
| simulation-phases | gravity settle, relaxation, erosion/accelerate, collapse, stopping criteria | Not exposed; numerical validation required |
| output | VTK, CSV, PNG, video, probes, contour fields, metadata | VTK/PNG/video partly exist; portable settings pending |
| full-preset | all chosen modules + constitutive code + manifest/dependencies | Generated runner exists; importable bundle/preset pending |

**Engine capabilities are not the same as implemented Studio UI features.**

## UI acceptance workflows

**Import one module:** Open the Geometry/Material/etc tab, choose Import .lisp, identify and validate its declared module, show old/new values and conflicts, choose Merge (only present supported fields) or Replace (module defaults for missing fields), then Confirm. Unselected modules MUST remain unchanged. Example: importing geometry.lisp cannot reset E, damage, CPU workers or pressure loads.

**Import multiple modules:** Choose specific files/module types, preview each change as a combined transaction, detect references between modules, apply atomically only if all are valid. Rejection/cancellation leaves the project unchanged.

**Export one module:** From any module tab use Export .lisp. The generated file must be deterministic, readable, versioned, contain the required module identity and units, and be portable to another compatible Studio instance.

**Export selected modules:** The user picks geometry + material, etc. Export each as an independent .lisp or grouped bundle with declared dependencies, without exporting unrelated modules.

**Import/export whole preset:** One action saves/restores the *complete* simulation configuration, module versions and custom source file dependencies. Use a documented manifest plus one or more .lisp files; a ZIP containing .lisp files and a safe JSON manifest is acceptable if needed for reproducibility. A full preset is separate from merely downloading a runnable simulation.lisp script; users must be able to IMPORT it back into the UI.

**Expected convenience:** Import, Export, Copy source, Save preset and a Before/After preview should be available from consistent module controls; show merge/replace and validation errors clearly.

## Versioned file format and safety

Do **not** evaluate, LOAD, or blindly READ arbitrary imported Lisp. Common Lisp reader macros (including read-time evaluation) can run code; reading a file is not proof of safety. A general Lisp script is not safely partitionable into modules by regex. Implement a **versioned declarative configuration subset**, parsed as inert data via a purpose-built parser or carefully audited safe reader that rejects unsupported reader forms and arbitrary evaluation.

- Required metadata: format/version, module ID, schema version, units, dependencies and provenance.
- Each module owns an explicit allowlist of keys. The current canonical schema is studio/schema.json and shared normalizer is studio/public/config.js.
- Enforce types, bounds, units, enums, cross-module dependencies, and default behaviour (including zero and false).
- Distinguish declarative config from executable constitutive-source. Imported executable text stays inert until separate, explicit, local-only execution opt-in; current security gates are operational safeguards, **not a sandbox**.
- Unsupported/legacy .lisp inputs are source-only previews or safely rejected; do not guess module identity by executing the file.
- Export for CLI may generate executable Lisp using existing CL-MPM APIs, but import/export configuration must remain a separate non-executing path.
- An incomplete/missing custom method or reference dependency must block full preset apply; never silently omit it.

## Architecture proposal (not yet built)

Provide a shared Module Registry so schema mappings do not diverge between app.js, server.js, model-workspace.js and scenario.lisp. Pure APIs to design:

- listModules() -> IDs, dependencies, owned keys
- importModule(source) -> validated *inert* data + warnings
- previewImport(project, modules, mode) -> diff/conflicts
- applyModulesAtomically(project, modules, mode) -> next project
- exportModule(id, project) -> versioned .lisp representation
- exportPreset(project) / importPreset(bundle) -> complete portable state

Do not put a permissive code evaluator in the web server. Imported state is staged until user confirmation. Preserve provenance and undo ability.

## Minimum test matrix

- Geometry-only import leaves material/solver/output strictly unchanged.
- Merge keeps missing fields; replace resets only target-module fields.
- Import two modules applies atomically and rejects conflicts with no partial write.
- Export -> import yields equivalent normalized values with SI units, enum, zero, false and numeric precision preserved.
- Import/export complete preset reproduces module metadata and bundled custom source dependencies.
- Malicious Lisp reader directives cannot execute during import; no untrusted script auto-execution.
- Exported custom model can be downloaded without execution; execution still requires explicit trusted local approval.
- UI/import/export data parity verified; test actual SBCL physics separately before claiming scientific correctness.

## Delivery roadmap

**P0**: establish green full-engine verification for existing Studio.

**P1a**: module registry, inert Lisp format and parser, geometry/material/solver/output per-module I/O, before/after diff, merge/replace, atomic apply, tests.

**P1b**: selected-module and full-preset bundle import/export with manifest, version checks and round-trip tests.

**P1c**: custom constitutive source dependencies and future boundary/loading/phases adapters, only after numerical interfaces are verified.

**P2**: multi-material, polygon/freeform geometry, advanced boundary/load/phase/output editors and physics benchmarks.

## Source and completion status

Requested by the user in the 2026-10-14 development discussion: allow GUI as well as partial .lisp import/export and full preset import/export. As of this specification, **only custom source import/export and generated complete run script export exist**. See studio/CUSTOM_MODELS.md. The general selective I/O and whole-preset **import** do not exist. Update docs/AI_HANDOVER.md and Obsidian/LLM Wiki as work progresses.
