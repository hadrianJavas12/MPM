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
| `:triaxial` spatial MPM | `:von-mises`, `:elastic`, compatible `:native` VM, MC or linear-elastic class | `:rectangle` (2D), `:cylinder` (3D) | `:confinement` / `:compression` | `:explicit` |
| `:cliff` | `:chalk`, `:von-mises`, `:elastic`, compatible `:native` | `:cliff` | `:rollers` / `:gravity` | `:explicit` |
| `:joss` | `:joss` dedicated DP/chalk class | `:joss` dedicated shape/base | `:rollers` / `:gravity` | `:staged` |

The elastic triaxial adapter uses the existing VM particle with plasticity off,
preserving its diagnostic state slots. Other models require a compatible
material diagnostics adapter and fail clearly instead of using VM yield formulas.
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

Diagnostics/state conventions are a separate protocol; see
[the material interface](components/README.md). Automatic `:native` adapters
support spatial MPM. Homogeneous trial/rollback is available only for the known
legacy VM constructors until an explicit state capability is provided.

Triaxial geometry accepts a per-case `:filter` function `(x y z) -> boolean`
within its rectangle/cylinder bounding dimensions. Private builders also accept
explicit particle/geometry callbacks. Add a `compile-scenario` / `execute-scenario`
method for experiments with different assembly or measurement requirements.

## Regression scope

The initial implementation was committed before post-refactoring native validation.
Engine equations are unchanged. Full before/after native runs have these results:

- **Triaxial 2D passes:** all 51 VTKs are byte-identical and every CSV difference
  is zero.
- **Joss strict regression fails:** both runs completed 40 s, but saved 176 versus
  191 physical states; common-time field diagnostics also exceed the pointwise
  `atol=1e-8`, `rtol=1e-7` tolerances. Final position-component difference reaches
  0.0811648 m, RMS 0.00234568 m.

Joss damage onset times agree (lower region 4 s, upper 7.5 s), and final run-out
edges are close (31.01589046 / 31.01587968 m). Initial-top-particle mean y is
8.17637462 / 8.17579450 m. Final-domain IoU 0.99667193 describes numerical shape
agreement; it is not physical accuracy and does not override the strict failure.
Cause investigation and overall acceptance remain pending. The user authorized
a checkpoint commit/push while the paired single-worker controls run; the final
PR remains pending. No physics change was used to force agreement. See the
[detailed validation status](../docs/REUSABLE_FRAMEWORK.md#hasil-validasi-saat-ini).
Scientific validity is distinct from regression.

The separate one-worker control completed and passed exactly: 191 physical
states, 193 VTKs per run including initial/equilibrium, and complete CSVs are
identical. Its executed after snapshot is `41403f4`, audited against original
`c749d32`; the completion-time status HEAD is not its source identity.
See [the serial-control report](../research/reports/M0_SERIAL_REGRESSION.md).
The four-worker failure remains. Current generic-diagnostic changes require
their own 2D/3D regression before the M0 framework gate is complete.

The 2D specimen is **plane strain with unit thickness**, not an axisymmetric
cylinder: it retains 3D constitutive stress while fixing out-of-plane deformation.
Its projected triaxial q and J2-invariant q differ; it cannot be required to have
the same projected curve as the earlier 3D axisymmetric loading example.
