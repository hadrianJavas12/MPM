# Native simulation framework

`cl-mpm-framework` composes existing native CL-MPM components without loading
the Studio system or starting a web server. Constitutive equations remain in
`src/`; the framework owns experiment construction, loading, phases and output.

## Run a case on Windows

```powershell
Set-Location D:\MPM
$runDir = Join-Path 'D:\MPM\output' ('framework-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\triaxial-clay-2d.lisp $runDir
```

Other cases: `triaxial-clay-3d.lisp`, `joss-collapse.lisp`, `cliff.lisp`.
The launcher requires a new/empty output directory and executes a copied
framework/case/input snapshot. A case file is trusted executable Common Lisp.
Native engine sources, compiled dependencies and DLLs are separate provenance.

## Composition and units

See the short files in `cases/`. Each assigns a simulation assembled from
material, geometry, boundary, loading and solver objects. Public geometry uses
metres, stress uses Pa, density uses kg/m³, time uses seconds and target strain
is a fraction (`0.10d0` = 10%). Backend JSON retains its existing units.

| Scenario | Material | Geometry | Boundary / loading | Solver |
| --- | --- | --- | --- | --- |
| `:triaxial` | `:von-mises`, `:elastic`, compatible `:native` VM subclass | `:rectangle` (2D), `:cylinder` (3D) | `:confinement` / `:compression` | `:explicit` |
| `:cliff` | `:chalk`, `:von-mises`, `:elastic`, compatible `:native` | `:cliff` | `:rollers` / `:gravity` | `:explicit` |
| `:joss` | `:joss` dedicated DP/chalk class | `:joss` dedicated shape/base | `:rollers` / `:gravity` | `:staged` |

The elastic triaxial adapter uses the existing VM particle with plasticity off,
preserving its diagnostic state slots. General incompatible models require a
measurement adapter, and fail clearly instead of silently using VM diagnostics.
The Joss recipe preserves its dedicated material, protected base and phase rules;
it rejects arbitrary substitutions that would invalidate that recipe.

## Module ownership

- `config/`: shared canonical parameter validation; no web runtime.
- `components/`: material/geometry extension contracts and component descriptors.
- `simulation.lisp`: composition dispatch and output lifecycle.
- `materials/chalk.lisp`: existing ordinary/reference chalk constructors and
  methods on dedicated reference classes.
- `scenarios/cliff/`, `scenarios/joss/`, `scenarios/triaxial/`: small modules
  for assembly, geometry, boundaries, measurements, phases and output.
- `output/`: existing optional plot writer; VTK/CSV remain native solver output.
- Existing `calibration/triaxial.lisp` and `studio/lisp/` entry points delegate
  to these modules for backwards compatibility. No UI source is changed.

## Extend a material or geometry

An existing native class can be selected per case using
`make-material :native :particle-class 'your-dedicated-class :initargs (...)`
with consistent `:youngs-modulus`, `:poisson-ratio`, `:density` metadata.
The material protocol is `material-particle-class` and
`material-particle-initargs`; specialize these generics for a new material
component when needed. Existing CLOS constitutive methods belong on the new
particle class, avoiding replacement of a shared engine method.

Triaxial geometry accepts a per-case `:filter` function `(x y z) -> boolean`
within its rectangle/cylinder bounding dimensions. Private builders also accept
explicit particle/geometry callbacks. Add a `compile-scenario` / `execute-scenario`
method for experiments with different assembly or measurement requirements.

## Regression scope

Refactoring preserves numerical expressions and old defaults. The implementation
checkpoint is committed before post-refactoring native validation. Full 2D
before/after compression and full Joss collapse are compared independently from
their saved VTK and CSV arrays. Scientific validity is distinct from regression.

The 2D specimen is **plane strain with unit thickness**, not an axisymmetric
cylinder: it retains 3D constitutive stress while fixing out-of-plane deformation.
Its projected triaxial q and J2-invariant q differ; it cannot be required to have
the same projected curve as the earlier 3D axisymmetric loading example.
