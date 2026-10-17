# CL-MPM folder ownership

Authority: [migration specification](CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md).
Current source checkpoint: P0–P6 and Section 2/5 physical folder alignment complete on `codex/material-architecture-migration`, 2026-10-17 (`5d6a5cf`). Physical owners match the Section 2 target tree;
historical package/class symbols and ASDF system names remain. Remaining
integration gates are stated separately from installed source ownership.

| Responsibility | Installed owner | Boundary |
| --- | --- | --- |
| Base particle/cache/common slots | `src/core/particle-base.lisp`, `particle-protocols.lisp` | Common stress/strain/F/mass/position and generic lifecycle stay engine-owned |
| Constitutive state/laws/evolution | Root `materials/core/`, `materials/models/`, `materials/cl-mpm-materials.asd` | Families own equations/history; 49 P2 owner files + linear-elastic package owner installed |
| Profiles/factories | `materials/core/definition.lisp`, `materials/definitions/`, `materials/adapters/` | Existing selection/construction, separate from integration |
| Model diagnostics | `materials/core/diagnostics-interface.lisp`, `materials/diagnostics/` | Model conventions/fields; no universal rollback API |
| Generic measurements/output | `src/measurements/`, `src/output/`, `src/output/plotting/` | Mechanisms consume model descriptors |
| Config/composition/lifecycle | `src/simulation/config/`, `components/`, `compatibility/`, `lifecycle.lisp` | Run-local assembly; no return mapping |
| Scenario procedures | Root `scenarios/{triaxial,cliff,joss,direct-shear}/` | Geometry, loading, boundaries, stages and measurements |
| Tensor/integration/bridge helpers | `src/numerics/{tensors,fastmaths,linear-algebra,integration,native-bridge,error-handling,eigen}/` | Includes relocated fastmaths and native bridge; material formulas stay with their families |
| Solvers | `src/solvers/{explicit,implicit,dynamic-relaxation,linear-systems}/` | Explicit (`usf`, `usl`, `musl`), implicit, dynamic-relaxation, and matrix-free linear solver |
| Discretization/transfer/boundaries/formulations/stabilization | `src/discretization/`, `src/transfer/`, `src/boundaries/`, `src/formulations/{ssa,octree,standard-mpm}/`, `src/stabilization/` | Engine mesh/shape/splitting/ghost, P2G/G2P/forces, BCs, SSA/octree, and aggregate stabilization |
| Nonlocal damage/communication | `src/damage/{nonlocal,eigenerosion,solver,fracture}/`, `src/parallel/{mpi,serial,workers}/` | Engine transport and scheduling with typed material hooks |
| Recipes/platform | `cases/{triaxial,cliff,benchmarks,direct-shear}/`, `scripts/`, `windows/` | Compose supported SI components; freeze selected source/DLL bytes |
| Native kernels/binaries | `libs/` | Retained ABI/build boundary; bindings in `materials/backends/cpp/` |
| Research/evidence/dependencies | `research/`, `docs/evidence/`, `deps/`, historical roots | Preserve provenance, licenses, failed runs, examples and raw sources |

Following explicit user direction on 2026-10-17, the physical workspace layout was aligned with Section 2 and Section 5 of `CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md` (`5d6a5cf`): legacy `framework/`, `src/models/`, and root `src/` forwarding shims were retired (`120/120` mapped owners present in `FILE_MIGRATION_RESULT.json`), `src/` is organized into the 15 Section 2 engine subdirectories, and `cases/` is organized into `cases/{triaxial,cliff,benchmarks,direct-shear}/` (with automatic flat-path resolution in `scripts/lisp/native-source-snapshot.lisp`). Normal ASDF loads owner files directly from root `cl-mpm.asd`, `cl-mpm-framework.asd`, and `materials/cl-mpm-materials.asd`.

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
