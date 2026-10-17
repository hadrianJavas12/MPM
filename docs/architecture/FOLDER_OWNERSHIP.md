# CL-MPM folder ownership

Authority: [migration specification](CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md).
Current source checkpoint: P2 A–D and P4D, 2026-10-16. Physical owners changed;
historical package/class symbols and ASDF system names remain. Remaining
integration gates are stated separately from installed source ownership.

| Responsibility | Installed owner | Boundary |
| --- | --- | --- |
| Base particle/cache/common slots | `src/core/particle-base.lisp`, `particle-protocols.lisp` | Common stress/strain/F/mass/position and generic lifecycle stay engine-owned |
| Constitutive state/laws/evolution | Root `materials/core/`, `materials/models/` | Families own equations/history; 49 P2 owner files installed |
| Profiles/factories | `materials/core/definition.lisp`, `materials/adapters/` | Existing selection/construction, separate from integration |
| Model diagnostics | `materials/core/diagnostics-interface.lisp`, `materials/diagnostics/` | Model conventions/fields; no universal rollback API |
| Generic measurements/output | `src/measurements/`, `src/output/` | Mechanisms consume model descriptors |
| Config/composition/lifecycle | `src/simulation/config/`, `components/`, `lifecycle.lisp` | Run-local assembly; no return mapping |
| Scenario procedures | Root `scenarios/{triaxial,cliff,joss}/` | Geometry, loading, boundaries, stages and measurements |
| Tensor/integration/bridge helpers | `src/numerics/` | Includes relocated fastmaths; material formulas stay with their families |
| Linear solver | `src/solvers/linear-systems.lisp` | Existing matrix-free implementation; explicit solvers remain `src/solvers/` |
| Nonlocal damage/communication | `src/damage/`, `src/damage/nonlocal/`, `src/parallel/` | Engine transport and scheduling with typed material hooks |
| Recipes/platform | `cases/`, `scripts/`, `windows/` | Compose supported SI components; freeze selected source/DLL bytes |
| Native kernels/binaries | `libs/` | Retained ABI/build boundary; bindings in `materials/backends/cpp/` |
| Research/evidence/dependencies | `research/`, `docs/evidence/`, `deps/`, historical roots | Preserve provenance, licenses, failed runs, examples and raw sources |

`framework/` and moved historical `src/` paths provide forwarding loaders.
Normal ASDF loads owner files directly, once. The canonical headless declaration
is root `cl-mpm-framework.asd` at P4-F implementation `436b561`; final validation
is incomplete. Compatibility paths must remain until their callers and
gates pass; this page does not claim `framework/` has been removed.

## Maintainer contracts

1. A material definition/profile identifies model, units, parameters and provenance.
   Its constitutive model owns updates/state; evolution belongs with the family.
   Research proposals are not validated profiles.
2. Preserve CLOS identity, ancestry, slots/initargs, signatures and native dispatch.
   MC stays independent of VM. Legacy `:elastic` keeps VM with plasticity disabled;
   actual native elasticity is a separate selection.
3. Scenarios compose engine/material interfaces. Material files do not acquire
   scenario algorithms; construction/config coupling belongs to explicit adapters.
4. Generic numerics do not acquire model equations. The atomic C++ transaction
   remains a documented mixed exception, not a clean-separation claim.
5. Preserve intact shared damage state, the later damage setter, optional ice
   pressure-degradation override and concrete forward-class behavior. Repairing
   them requires a separately reviewed behavior change.
6. Keep SI inputs and explicit legacy conversions consistent. Unsupported modes
   fail explicitly. No universal trial/commit/rollback or dedicated MC H/HS physics
   was introduced by structural extraction.
7. Cases compose `make-simulation` from material, geometry, boundary, loading and
   solver components. Triaxial accepts rectangle/cylinder geometry and supported
   VM/elastic/native selections; cliff/Joss keep their supported combinations.
8. Trusted case/custom Lisp executes as local OS code. Preserve existing opt-in
   safeguards; profile selection and file extensions do not provide a sandbox.

The [P0 matrix](FILE_MIGRATION_MATRIX.json) is an immutable starting capture.
The [compact P2 map](P2_COMPACT_MIGRATION.json) records exact forms and deliberate
definition-order changes; the 109-fragment alternative was not applied.
Twenty native family catalogs passed with baseline byte equality. They establish
loading/CLOS metadata compatibility, not full numerical G3 or scientific validation.
The full Joss serial run remains cancelled; preserve its status and negative evidence.

See [material API](../../materials/README.md), [model catalog](MODEL_CATALOG.md),
[dependency rules](DEPENDENCY_RULES.md) and [execution log](MIGRATION_EXECUTION_LOG.md).
