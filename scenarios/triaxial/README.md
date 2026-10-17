# Native triaxial scenario modules

The reusable API composes material and geometry descriptors, then calls
`cl-mpm/calibration/triaxial:run-config`. The historical entry point
`calibration/triaxial.lisp` remains a small compatibility loader.

| Module | Responsibility |
| --- | --- |
| `config.lisp`, `src/simulation/config/legacy-triaxial-values.lisp` | Input access and defaults |
| `src/numerics/legacy-tensors.lisp`, `src/measurements/legacy-*.lisp` | Shared tensor and measurement conventions |
| `materials/adapters/triaxial.lisp`, `legacy-triaxial.lisp` | Native constructor/prestress and retained material-state helpers |
| `geometry.lisp` | Mesh, particle distribution and run-local factory/filter callbacks |
| `src/boundaries/pressure/isotropic.lisp` | Dedicated isotropic traction boundary class |
| `measurements.lisp` | Native field invariants, aggregate diagnostics and VTK/CSV frames |
| `mpm.lisp` | Spatial MPM loading and time stepping |
| `homogeneous.lisp` | Constitutive-point comparator and explicitly affine visualization |
| `controls.lisp` | Analytical and hydrostatic verification controls |
| `runner.lisp` | Run lifecycle, dynamic measurement context and manifest |

`run-config(config, directory, :particle-factory factory, :geometry-filter filter)`
accepts per-run extension functions. `factory(config, origin, size, counts, clip)`
returns a vector of native particles; `filter(x, y, z)` returns a clipping boolean.
Callbacks do not install or replace global engine methods. The automatic diagnostic adapters support VM, MC (excluding DP) and native
linear elasticity; the historical elastic demonstrator
uses the same native class with plasticity disabled. Unsupported particle classes
fail before time stepping, rather than silently producing invalid measurements.

Default `spatialDimensions=3` retains the original cylinder construction and
numerics. `spatialDimensions=2` means a rectangular **plane-strain** specimen with
unit out-of-plane thickness, a native 2D grid and full 3D constitutive tensors.
It is not axisymmetric and does not represent the original physical cylinder.
`q_j2_kpa` remains the invariant used for VM yield; `deviatoric_stress_kpa` is the
historical triaxial projection, which differs under plane strain. The lateral CSV
diagnostic averages `sigma_xx` and `sigma_zz`; it is not a direct cell-pressure
error measure in 2D. Homogeneous and analytical control modes require dimension 3.

The long 2D regression uses `mpsPerCell=2`: the first one-particle-per-cell attempt
hit the engine's existing GIMP domain-size removal criterion during lateral
expansion and failed mass conservation. The failed attempt is retained as evidence;
the invariant and engine removal policy were not weakened to obtain a passing run.
