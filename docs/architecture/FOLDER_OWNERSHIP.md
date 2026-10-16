# CL-MPM folder ownership

Authority: [the supplied migration specification](CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md).
This document distinguishes the current implementation from the target. Empty
blueprint folders and unimplemented model names are not shipped capabilities.

## Current checkpoint

The architecture branch starts at `7c399fb` on 2026-10-16. The engine is in
`src/`; the existing composition API and scenario modules are in `framework/`.
`materials/`, `scenarios/` and engine orchestration ownership will be introduced
in tested stages. Existing packages and ASDF system names remain public contracts.
The [complete migration matrix](FILE_MIGRATION_MATRIX.json) captures the starting
tracked tree; newly added files are identified separately from that frozen tree.

| Responsibility | Current implementation | Target owner |
| --- | --- | --- |
| Base particle/mesh and MPM protocols | `src/particle.lisp`, `src/core/`, other native modules | `src/`; split model-specific forms after inspection |
| Constitutive implementations/history/evolution | Mixed `src/particle.lisp`, `src/constitutive.lisp`, `src/models/`, parts of damage/native bridge | Root `materials/models/<family>/<model>/` |
| Material profiles | Component parameters and research proposals | `materials/definitions/` for explicit reusable profiles; research assumptions stay in `research/` |
| Material construction/diagnostics | `framework/components/materials.lisp`, `diagnostics.lisp` | `materials/core/`, `materials/adapters/`, model-specific diagnostics |
| General assembly/configuration/run lifecycle | `framework/components/`, `framework/simulation.lisp` | `src/simulation/` |
| Scenario geometry/boundaries/stages/measurements | `framework/scenarios/` | `scenarios/` |
| Generic tensors/numerical primitives | `src/utils.lisp`, `fastmaths.lisp`, parts of constitutive/native bridge | `src/numerics/` only where a useful separation is demonstrated |
| Generic damage transport/nonlocal/solver | `src/damage/` | Engine `src/damage/`; material laws move individually |
| Case recipes | Four short `cases/*.lisp` files | Scenario groups under `cases/`, old paths retained during transition |
| CLI/platform | `scripts/`, `windows/`, calibration adapters | Retain entry points; update loading/snapshots with direct regression |
| Historical evidence/dependencies/UI | Existing corresponding roots | Preserve; UI feature work excluded |

## Material concepts

- A **material definition** identifies a profile, units, parameters, model and
  provenance. It does not solve a constitutive equation.
- A **constitutive model** owns its yield/flow/integrator and model-specific
  state. Base position/mass/F and generic particle mechanics remain engine-owned.
- An **evolution law** belongs inside its model, including its strain convention,
  hardening/softening history and trial/commit/rollback requirements.
- **Diagnostics** identify the actual model and stress/strain measures. Unsupported
  fields remain unavailable; MC results never acquire VM formulas by inheritance.
- `materials/shared/` requires demonstrated reuse across models. Generic tensor
  algebra belongs to the engine numerical layer, not an arbitrary material family.

Physical ownership changes do not require renaming existing CLOS symbols. In
particular, `cl-mpm/particle::particle-mc` must retain its identity and ancestry.
No new evolution law or registry entry is treated as verified by folder creation.

## Migration decisions

1. Keep the current solver as the numerical baseline. Copy/extract complete
   top-level forms without editing their numerical expressions.
2. Preserve ASDF load order and legacy umbrella systems. Do not introduce
   `particle -> damage` to repair the existing concrete forward superclass;
   damage already depends on particle.
3. Keep `framework/` as a temporary compatibility surface until every active
   caller, standalone calibration loader and frozen-source runner is migrated.
4. Keep native DLL selection/fallback behavior intact. The mixed bridge requires
   its own audit, not a move based on its filename.
5. Keep UI schema compatibility and headless loading separate. Schema relocation
   needs a canonical owner plus compatibility tests; duplicating it is insufficient.
6. Preserve every failed run, original example, raw source and personal setting.
   No deletion is authorized solely because a text search finds no caller.
7. MC H/HS numerical development remains a separate experimental branch/gate.

See [dependency contracts](DEPENDENCY_RULES.md),
[semantic material review](MATERIAL_OWNERSHIP_AUDIT.md) and
[execution/gate log](MIGRATION_EXECUTION_LOG.md).
