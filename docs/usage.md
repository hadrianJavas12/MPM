# Usage

All commands are run from the repository root.

## REPL
```bat
windows\cl-mpm.cmd
```
```lisp
(ql:quickload :cl-mpm)
(ql:quickload :cl-mpm/setup)
```
Then follow the tutorial in the [README](../README.md#tutorial---quick-start). It is also available as an
executable script with an assertion: `scripts/smoke-test.lisp`.

## Scripts
```bat
windows\cl-mpm.cmd path\to\script.lisp arg1 arg2
```
Inside a script, `cl-user::cl-mpm-script-args` returns the arguments and `cl-user::*cl-mpm-root*`
the repository root.

## Examples
Each folder in `examples/` is a problem set-up (`chalk`, `damage`, `ice`, `penalty`, ...). Systems
are registered in `cl-mpm.asd` as `cl-mpm/examples/<name>`:
```lisp
(ql:quickload :cl-mpm/examples/chalk)
```
Most examples define `setup` and `run` functions; read the head of each file for its entry point.
Examples that need MPI (`cl-mpm/dynamic-relaxation-mpi`, real `cl-mpm/mpi`) are Linux only.

## Output
| Output | How | Viewer |
|---|---|---|
| VTK | `cl-mpm/output:save-vtk-mesh`, `save-vtk` | ParaView (open `sim_..vtk` as a sequence) |
| Live plot / PNG | `cl-mpm/plotter:simple-plot`, then `vgplot:print-plot` | gnuplot |
| Video | `windows\make-video.cmd frames 15 out.mp4` | any player |

## Useful settings
- Threads: `(cl-mpm/utils:set-workers 4)`.
- Heap: `set CL_MPM_HEAP_MB=8000` before launching.
- Debug a threaded section serially: `(setf cl-mpm/utils::*workers-nesting* t)` runs `omp` in the main thread, giving real backtraces.
