# Development

## Checks before committing
```bat
windows\cl-mpm.cmd scripts\smoke-test.lisp        :: library + numerics
node --check studio\server.js                     :: server syntax
windows\cl-mpm.cmd studio\lisp\run.lisp           :: Studio runner with defaults (slow) or pass a small config
```
A small Studio config for a quick run: `{"maxSteps":3,"substeps":5,"meshSize":10,"mpsPerCell":1}`.

## Patches to vendored dependencies (`deps/`)
| Where | Change | Why |
|---|---|---|
| `deps/magicl/src/extensions/{blas,lapack}/load-libs.lisp` | `(:windows ...)` library clauses | Find `libopenblas.dll` |
| `deps/magicl/src/extensions/common/cffi-types.lisp` | `conjf` defcfun commented out | Not provided by OpenBLAS on Windows |
| `deps/magicl/magicl.asd` | `cffi-libffi` removed | Not available on Windows |
| `deps/magicl/src/bindings/lapack-cffi.lisp` | Hand-written `%DSYEV` / `%SSYEV` | Missing in the generated bindings; needed by `self-adjoint-eig` (damage) |
| `deps/vgplot/vgplot.lisp` | Backslash / quoting fixes in `print-plot` | Windows paths |
| `deps/swank.live/` | No-op `swank.live:update-swank` | Quicklisp has no such system |

Upstream sources: `github.com/Ionsto/magicl`, `github.com/Ionsto/vgplot`.

## Other Windows-specific changes
- `cl-mpm.asd`: `:cl-mpm-no-mpi` feature and guards; `examples/chalk` depends on `cl-mpm/models/chalk`.
- `src/mpi/serial.lisp`: serial stand-in for `cl-mpm/mpi` (`mpi-sum` is the identity, domain predicates return T, point-to-point exchange signals `mpi-unavailable`).
- `examples/chalk/chalk.lisp`: removed initargs that are not slots of `particle-chalk-delayed`.
- `libs/kirchoff.dll`: statically linked MinGW build (`windows\build-kirchoff.cmd`).

The state before the refactor is preserved in the git branch `backup/gemini-windows-port`.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Quicklisp not found" / missing OpenBLAS | Run `windows\setup.ps1` |
| `Unable to load foreign library libopenblas` | Check `toolchain\openblas\bin\libopenblas.dll` exists |
| No PNG frames, "Plotting disabled" in the log | gnuplot missing; set `CL_MPM_GNUPLOT` to its `bin` directory |
| Heap exhausted | `set CL_MPM_HEAP_MB=8000` |
| First run takes minutes | It compiles all systems; fasls are cached afterwards |
| Studio won't start | Node.js ≥ 18 is required; change the port with `STUDIO_PORT` |
| `Git commit INVALID` message | Harmless; the upstream commit hook file is not generated |
