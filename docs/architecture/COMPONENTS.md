# Simulation and Material Component Contracts

Authority: [migration specification](CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md) and [folder ownership](FOLDER_OWNERSHIP.md).

## Ownership split from historical `framework/components/`

During P1, P3, and P4, the mixed component definitions previously grouped under `framework/components/` were separated into their canonical simulation, material, and measurement owners while retaining reloadable forwarding shims under `framework/components/` for historical `LOAD` callers:

| Historical path | Canonical installed owner(s) | Responsibility |
| --- | --- | --- |
| `framework/components/specifications.lisp` | `src/simulation/components/base.lisp`, `materials/core/definition.lisp`, `src/simulation/components/specifications.lisp` | Base component class (`component-specification`), material specification contract (`material-specification`, `material-particle-class`, `material-particle-initargs`, `material-diagnostics`), and geometry/boundary/loading/solver specifications |
| `framework/components/materials.lisp` | `materials/adapters/native.lisp` | Native material construction factory (`make-material-specification`, `:von-mises`, `:elastic`, `:mohr-coulomb`, `:native`) |
| `framework/components/diagnostics.lisp` | `materials/core/diagnostics-interface.lisp`, `materials/diagnostics/native.lisp`, `src/measurements/material-output.lisp` | Diagnostics protocol generics, native VM/MC/elastic run-local diagnostic adapters, and generic simulation output helpers |
| `framework/components/geometry.lisp` | `src/simulation/components/geometry.lisp` | `geometry-filter` clipping callback generic and validation method |
| `framework/components/README.md` | `docs/architecture/COMPONENTS.md`, `materials/DIAGNOSTICS.md` | Component and material diagnostics contract documentation |

Normal ASDF systems (`cl-mpm-framework.asd`) load the canonical owner files directly, once.

## Material construction, state, and diagnostics contract

Construction and measurement are separate:
- `material-particle-class` and `material-particle-initargs` select a real native particle class and initialization arguments.
- `material-diagnostics` returns a run-local adapter for interpreting that particle's state.
- Neither layer installs a global constitutive override; new constitutive equations belong on a dedicated native particle class.

Automatic adapters cover native Von Mises (`particle-vm`), Mohr-Coulomb (`particle-mc`, excluding Drucker-Prager), and native linear elastic (`particle-elastic`) particles. The public `:elastic` option retains its historical VM-with-plasticity-off behavior; an explicit native linear-elastic class uses the elastic diagnostics adapter.

| Protocol | Purpose |
| --- | --- |
| `diagnostics-particle-type` | Compatible native particle type |
| `diagnostics-modes` | Explicitly supported scenario modes |
| `diagnostics-conventions` | Manifest definitions for stress, state, and yield |
| `diagnostics-fields` | Model-specific `(name unit reduction accessor definition)` descriptors |
| `diagnostics-legacy-values` | VM legacy values, or two `NIL` values when unavailable |
| `material-state` / `validate-material-state` | Read-only diagnostic values and state checks |
| `configure-material-output` | Idempotent per-simulation output setup |

For complete adapter, output meaning, and extension rules, see [materials/DIAGNOSTICS.md](../../materials/DIAGNOSTICS.md) and [materials/README.md](../../materials/README.md).
