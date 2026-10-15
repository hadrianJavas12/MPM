# Development

## Checks before committing
Run the automated checks first:

```bat
cd studio
npm run check
set STUDIO_REQUIRE_SBCL_TESTS=1
npm test
cd ..
```

SBCL must be on PATH or set with `STUDIO_TEST_SBCL`. Contract tests use explicit
dependency stubs and need no Quicklisp. See [testing.md](testing.md) for scope.

```bat
windows\cl-mpm.cmd scripts\smoke-test.lisp        :: library + numerics
windows\cl-mpm.cmd scripts\studio-custom-smoke.lisp :: real-engine built-in/delegate comparison
windows\cl-mpm.cmd scripts\studio-plot-smoke.lisp   :: actual gnuplot PNG success/failure
node --check studio\server.js                     :: server syntax
windows\cl-mpm.cmd studio\lisp\run.lisp           :: Studio runner with defaults (slow) or pass a small config
```
A small Studio config for a quick run: `{"maxSteps":3,"substeps":5,"meshSize":10,"mpsPerCell":1}`.

For a custom delegate, export both Lisp files into the same directory and run
`simulation.lisp` with the Windows launcher. Preserve the UI output in a
separate directory, then compare it with the exported run:

```bat
node scripts\verify-studio-output.js output\studio output\studio-export 3
```

This checker reads the repository particle writer's binary layout, rejects
non-finite/truncated/missing scalar arrays, checks positive mass and compares
VTK/PNG bytes. It is not a general VTK reader or a physical benchmark.
See [testing](testing.md) and [captured Windows results](windows-verification-2026-10-14.md).

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
- `windows/setup.ps1`: Quicklisp bootstraps through a temporary source file with
  user/system SBCL init disabled; this avoids PowerShell argument quoting and
  premature dependency loads from `.sbclrc`.
- `src/output.lisp`: particle binary VTK declarations and payload share one
  octet stream. Two append handles corrupted their ordering on Windows; this
  output fix leaves the solver's numerical update unchanged.
- `studio/lisp/runner.lisp`: PNG export removes an old target, waits for a
  readable signature and IEND trailer, and reports timeout. The runner's
  existing handler logs plotting failures rather than silently accepting a
  missing or partial frame.

The state before the refactor is preserved in the git branch `backup/gemini-windows-port`.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Quicklisp not found" / missing OpenBLAS | Run `windows\setup.ps1` |
| `Unable to load foreign library libopenblas` | Check `toolchain\openblas\bin\libopenblas.dll` exists |
| No PNG frames, "Plotting disabled" in the log | gnuplot missing; set `CL_MPM_GNUPLOT` to its `bin` directory |
| `gnuplot did not write a complete readable PNG` | Check the output directory is writable and gnuplot works; repeat `scripts\studio-plot-smoke.lisp` |
| Heap exhausted | `set CL_MPM_HEAP_MB=8000` |
| First run takes minutes | It compiles all systems; fasls are cached afterwards |
| Studio won't start | Node.js ≥ 18 is required; change the port with `STUDIO_PORT` |
| `Git commit INVALID` message | Harmless; the upstream commit hook file is not generated |
