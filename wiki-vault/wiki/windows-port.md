---
title: Windows port
type: concept
tags: [windows, toolchain]
sources: ["[[refactor-2026-10-14]]", "[[studio-verification-2026-10-14]]", docs/windows-setup.md]
updated: 2026-10-14
---

# Windows port

Native Windows (no WSL). History: Gemini Flash made it run with hardcoded paths (`D:\MPM`, user profile dirs), duplicated DLLs and scripts at the repo root; refactored on 2026-10-14 (see [[refactor-2026-10-14]]). The pre-refactor state is branch `backup/gemini-windows-port`.

## Layout
- `windows/`: `setup.ps1`, `cl-mpm.cmd` (REPL / script launcher), `init.lisp`, `env.cmd`, `make-video.cmd`, `build-kirchoff.cmd`.
- `toolchain/` (git-ignored): Quicklisp and OpenBLAS (single `libopenblas.dll`).
- Overrides: `CL_MPM_SBCL`, `CL_MPM_GNUPLOT`, `CL_MPM_FFMPEG`, `CL_MPM_HEAP_MB`, `windows/env.local.cmd`.

## Gotchas
- WinGet `Links\gnuplot.exe` alias fails from SBCL (STATUS_DLL_NOT_FOUND); use the real package dir.
- gnuplot writes PNGs asynchronously; the runner waits for each file.
- MPI is a serial stand-in: [[serial-mpi-standin]]. Dependency fixes: [[magicl-patches]].
- jonathan parses JSON decimals as single-floats; the studio config rationalizes them.
- Quicklisp setup now writes a temporary bootstrap source and disables SBCL
  user/system init files. This avoids PowerShell quote handling and `.sbclrc`
  trying to use CFFI before installation. Fresh install into a path with spaces
  passed on PowerShell 5.1 in the native continuation.
- Binary particle VTK headers and doubles now use one octet stream; separate
  append handles corrupted their ordering on Windows. Native smoke checks every
  binary block and 36 finite scalar arrays.
- PNG completion checks signature/IEND after removing an old target; timeout
  becomes a reported plotting failure instead of silent missing output.

Current native toolchain evidence and actual browser/export parity:
[[studio-verification-2026-10-14]]. Executables were reused and checkout-local
Quicklisp/OpenBLAS copied from the existing installation; the fresh Quicklisp
bootstrap was tested independently. Numerical calibration remains separate.

Docs: `docs/windows-setup.md`. Parent: [[cl-mpm]].
