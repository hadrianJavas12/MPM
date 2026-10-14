# Architecture

## What CL-MPM is
A material point method (MPM) code in Common Lisp (SBCL only: it uses SIMD intrinsics). Material
points carry mass, stress and history variables and move through a fixed background mesh of nodes.

## One time step
`cl-mpm:update-sim` runs the scheme of the simulation class (USF, USL or MUSL):

1. **P2G** – map mass, momentum and internal/external force from particles to nodes using GIMP shape functions.
2. **Nodal update** – solve momentum with explicit time integration (damping, mass scaling); apply boundary conditions (including non-conforming virtual-stress and penalty contact).
3. **G2P** – map velocity/acceleration back to particles, move them, update the deformation gradient.
4. **Constitutive update** – strain increment (Hencky / Kirchhoff, optionally via the C++ `kirchoff.dll`), then the particle's model (elastic, von Mises, Mohr–Coulomb, Drucker–Prager, ...).
5. **Damage** (optional) – non-local continuum damage over a local length; the `chalk` models use delayed damage.
6. The timestep is adapted from the wave speed (`estimate-elastic-dt`).

## Source layout (`src/`)
| Directory | Content |
|---|---|
| `core/` | Mesh, simulation classes, shape functions, P2G/G2P, update schemes, `utils`, `fastmaths` |
| `models/` | Constitutive models and `particle-*` classes (elastic, vm, chalk, ...) |
| `damage/` | Non-local damage and stress-criterion code |
| `bc/` | Boundary conditions (fixed, virtual stress, penalty contact) |
| `solvers/` | Implicit / quasi-static solvers |
| `dynamic-relaxation/` | Dynamic-relaxation quasi-static solver |
| `ssa/` | Shallow-shelf style ice models |
| `mpi/` | `cl-mpm/mpi` — real MPI classes (Linux) or `serial.lisp` stand-in |
| `*.lisp` at top level | Setup helpers, plotter, output (VTK/CSV), C++ bindings |

`cl-mpm.asd` defines the ASDF systems (`cl-mpm`, `cl-mpm/setup`, `cl-mpm/plotter`, `cl-mpm/output`, `cl-mpm/models/*`, `cl-mpm/examples/*`, ...). `cl-mpm-tests.asd` defines the tests.

## Platform switches
| Feature | Effect |
|---|---|
| `:win32` (SBCL) | Adds `:cl-mpm-no-mpi`; skips `magicl/ext-expokit` |
| `:cl-mpm-no-mpi` | Uses the serial `cl-mpm/mpi`; the `dynamic-relaxation-mpi` system and its connection are not defined |

Linux behaviour is unchanged: all changes are guarded by these features.

## Windows layer (outside `src/`)
`windows/` (launchers and setup), `deps/` (patched MAGICL/vgplot, swank.live stand-in), `toolchain/` (downloaded binaries), `studio/` (UI) — see [development.md](development.md).
