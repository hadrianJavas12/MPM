# Material construction, state and diagnostics

Construction and measurement are separate. `material-particle-class` and
`material-particle-initargs` select a real native particle. `material-diagnostics`
returns a run-local adapter for interpreting its state. Neither layer installs a
global constitutive override. New equations belong on a dedicated native class.

Automatic adapters cover VM, MC (excluding DP) and native linear elastic particles.
The public `:elastic` option retains its historical VM-with-plasticity-off behavior;
an explicit native linear-elastic class uses the elastic diagnostics adapter.

## Adapter contract

| Protocol | Purpose |
| --- | --- |
| `diagnostics-particle-type` | Compatible native particle type |
| `diagnostics-modes` | Explicitly supported scenario modes |
| `diagnostics-conventions` | Manifest definitions for stress, state and yield |
| `diagnostics-fields` | Model-specific `(name unit reduction accessor definition)` descriptors |
| `diagnostics-legacy-values` | VM legacy values, or two NIL values when unavailable |
| `material-state` / `validate-material-state` | Read-only diagnostic values and state checks |
| `configure-material-output` | Idempotent per-simulation output setup |

Descriptors use `:mean` (volume-weighted) or `:max`; accessors return finite
numeric scalars. Names must be unique and must not replace native scalar,
vector or tensor outputs such as mass, position or domain size. Descriptor and
particle/mode validation precedes output configuration. `material-state` is
not a complete constitutive trial/commit/rollback snapshot.

Known public VM/elastic constructors retain legacy homogeneous mode. Automatic
`:native` VM adapters, including bare VM particles with custom history arguments,
are spatial-only. MC/linear-elastic homogeneous modes require full trial/copy/
rollback support before they can be enabled. Custom callbacks in unsupported
controls mode reject instead of being ignored.

## Output meaning

Common stress invariants, geometry, mass, volume and finite-state measurements do
not imply a VM yield criterion. In MC runs the legacy CSV `plastic_strain` and
`max_yield_excess` columns are blank and listed unavailable. Named MC values go
to `material-diagnostics.csv` and native VTK output, including accumulated native
plastic strain, current c/phi/psi, corrected yield residual and stored trial f.

The native MC diagnostic evaluates signed Kirchhoff yield independently from
the corrected stress: `tau=J*sigma_Cauchy`,
`f=k*tau_max-tau_min-2*c*sqrt(k)`, `k=(1+sin(phi))/(1-sin(phi))`.
The stored native yield-function value is the trial value and is labelled
separately. Angles use radians. The native accumulator is 1.5 times conventional
equivalent plastic strain; it has not been equated to a PDF strain coordinate.

The current native MC apex implementation is singular at phi=0. The adapter
rejects that plastic state explicitly; it does not change the raw reference
table or silently floor friction. Dedicated H/HS mechanics and zero-friction
corner/apex verification remain M2 work.

## Checks and extension sequence

`tests/material-diagnostics.lisp` covers adapter/state validation, independent
analytic MC stress states, reserved output names, unsupported history modes and
a bounded actual MC solver run. `tests/config-contracts.lisp` covers strict JSON,
valid parameter ranges and rejection before run output. Complete legacy VM
2D/3D regression is a separate acceptance gate.

To add a model: define its native particle and integration, provide construction
metadata, specialize `material-diagnostics` with explicit state conventions,
then verify that model's point response and material-specific output before
enabling full scenario modes. Do not inherit VM solely to obtain its slots.
