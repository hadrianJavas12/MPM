# Windows setup

CL-MPM runs natively on Windows 10/11 (x64) with SBCL. No WSL is required.

## 1. One-time setup
```bat
powershell -ExecutionPolicy Bypass -File windows\setup.ps1
```
The script is idempotent. It:

1. checks (and, via `winget`, installs) **SBCL**, **Node.js** (Studio only), **gnuplot** (PNG frames) and **ffmpeg** (video);
2. installs **Quicklisp** into `toolchain\quicklisp`;
3. downloads **OpenBLAS** into `toolchain\openblas` (BLAS/LAPACK DLL used by MAGICL).

Options: `-SkipWinget` (only report missing tools), `-BuildKirchoff` (also compile `libs\kirchoff.dll`).

## 2. Verify
```bat
windows\cl-mpm.cmd scripts\smoke-test.lisp
```
It builds the README quick-start problem, runs it and asserts the particles settle. The first
run compiles everything and can take several minutes; later runs start in seconds.

## 3. Launchers (all in `windows\`)
| File | Purpose |
|---|---|
| `cl-mpm.cmd` | `cl-mpm.cmd` = REPL; `cl-mpm.cmd script.lisp [args]` = run a script and exit |
| `init.lisp` | Loaded by the launcher: Quicklisp, ASDF search paths, DLL search paths |
| `env.cmd` | Finds sbcl / gnuplot / ffmpeg and extends `PATH` |
| `make-video.cmd` | `make-video.cmd [frames-dir] [fps] [out.mp4]` — PNG frames to MP4 |
| `build-kirchoff.cmd` | Compile the optional C++ kernel with MinGW + Eigen |
| `setup.ps1` | The one-time setup above |

## 4. Configuration
Override tool locations with environment variables, or put `set` lines in
`windows\env.local.cmd` (git-ignored):

| Variable | Meaning | Default |
|---|---|---|
| `CL_MPM_SBCL` | Full path to `sbcl.exe` | `PATH`, then `Program Files` |
| `CL_MPM_GNUPLOT` | Directory with `gnuplot.exe` | WinGet package dir, then `Program Files` |
| `CL_MPM_FFMPEG` | Directory with `ffmpeg.exe` | `PATH`, then WinGet package dir |
| `CL_MPM_HEAP_MB` | SBCL dynamic space size | `4000` |

> The WinGet alias `...\WinGet\Links\gnuplot.exe` cannot start gnuplot from SBCL (DLL not found),
> which is why `env.cmd` prefers the real install directory.

## 5. What is different from Linux
- **MPI is disabled.** `:cl-mpm-no-mpi` is enabled automatically on Windows and `cl-mpm/mpi` is a
  serial stand-in (`src/mpi/serial.lisp`). Multithreading (lparallel) works as usual.
- **expokit** (matrix exponential) is not built; the code that used `magicl:expm` is commented out.
- Patched copies of MAGICL / vgplot are vendored in `deps/` (see [development.md](development.md)).
