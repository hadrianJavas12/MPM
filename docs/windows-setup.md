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

Quicklisp installation uses a temporary Lisp bootstrap file rather than a
quoted `--eval` expression. SBCL starts with `--no-userinit --no-sysinit` for
this installation so an existing `.sbclrc` cannot load project dependencies
before Quicklisp is ready. A fresh installation into a path containing spaces
was verified on Windows PowerShell 5.1; see [the Windows verification report](windows-verification-2026-10-14.md).

## 2. Verify
```bat
windows\cl-mpm.cmd scripts\smoke-test.lisp
windows\cl-mpm.cmd scripts\studio-custom-smoke.lisp
windows\cl-mpm.cmd scripts\studio-plot-smoke.lisp
```
The first test runs the README quick-start problem and checks finite particle
positions, velocities and stresses, positive finite timestep and downward
motion of the mean position. It does not establish equilibrium. The custom
test compares the built-in chalk law with its custom delegate and checks
binary VTK output; the plot test exercises successful and failed PNG output.
The first run compiles everything and can take several minutes; later runs
start in seconds. Exact results and tool versions: [Windows verification](windows-verification-2026-10-14.md).

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
