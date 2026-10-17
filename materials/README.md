# Native material ownership

Root `materials/` owns relocated material definitions, constitutive models,
state/evolution, diagnostics and integration adapters. P2 installed 49 owner
files; the [compact map](../docs/architecture/P2_COMPACT_MIGRATION.json) records
their exact source forms and load prerequisites. Historical CLOS symbols remain
in `cl-mpm/particle`, `cl-mpm/constitutive` and `cl-mpm/framework`.

| Area | Responsibility |
| --- | --- |
| `core/definition.lisp` | Existing material component and profile/options selection |
| `core/plastic-state.lisp` | Shared legacy plastic state and lifecycle |
| `models/` | Constitutive classes, stress updates and family evolution laws |
| `adapters/` | Native factories, triaxial translation, chalk construction and damage output |
| `diagnostics/` | Model conventions, named fields, native MC residual and chalk measurements |
| `backends/cpp/legacy-transaction.lisp` | Preserved atomic native-library success/fallback transaction |

General tensors and integration helpers live in `src/numerics/`. Common particle
stress/strain/F/mass/position slots remain engine-owned. The
[model catalog](../docs/architecture/MODEL_CATALOG.md) maps classes to owners.

## Selecting components

The existing `cl-mpm/framework` API composes `make-material`, `make-geometry`,
`make-boundary`, `make-loading` and `make-solver` through `make-simulation`.
For example, a triaxial material component can select native MC:

```lisp
(make-material :native
 :particle-class 'cl-mpm/particle::particle-mc
 :youngs-modulus 20d6 :poisson-ratio 0.2d0 :density 1800d0
 :initargs (list :phi (/ pi 6d0) :psi 0d0 :c 6d3 :softening 0d0))
```

These illustrative SI inputs are not a calibrated profile. MC retains its own
ancestry and does not inherit VM. Legacy `:elastic` constructs `particle-vm`
with plasticity disabled; `:native` with `particle-elastic` selects the separate
actual elastic class. Triaxial supports rectangle/cylinder geometry with
confinement/compression. Cliff/Joss retain their own component combinations.
See [existing cases](../cases/) and [ownership rules](../docs/architecture/FOLDER_OWNERSHIP.md).

## Maintenance and evidence

Preserve symbols, ancestry, slots/initargs, method specializers, backend choice
and units. Profiles/construction are separate from constitutive integration.
No validated profile database, universal trial/commit/rollback protocol or
dedicated MC H/HS integrator was added. Unsupported modes must fail explicitly.

All 20 fresh Windows family catalogs across P2 A–D matched baseline bytes,
including final checkpoint `f9ba947`. This verifies native loading and
class/slot/method metadata, not numerical or scientific validation.
The atomic mixed C++ block, inherited damage/ice overrides and concrete forward
class remain [explicit exceptions](../docs/architecture/MODEL_CATALOG.md).
Native kernels/DLLs stay in `libs/`; old source paths remain forwarding loaders.
The canonical headless ASDF declaration is root `cl-mpm-framework.asd`
(P4-F implementation `436b561`; final validation is incomplete).
See the maintained [diagnostic contract](DIAGNOSTICS.md). Full G3 completion is not claimed.
The cancelled full Joss serial run must stay cancelled.
