---
title: Vendored dependency patches
type: concept
tags: [magicl, vgplot, dependencies]
sources: ["[[refactor-2026-10-14]]"]
updated: 2026-10-14
---

# Vendored dependency patches (`deps/`)

- **MAGICL** (`Ionsto/magicl`): `(:windows ...)` clauses in `load-libs.lisp` (blas, lapack); `conjf` defcfun commented out; `cffi-libffi` dropped from the `.asd`; **hand-written `%DSYEV`/`%SSYEV`** appended to `src/bindings/lapack-cffi.lisp` because the generated bindings lack them and `magicl:self-adjoint-eig` (damage principal stresses) fails with "function NIL is undefined".
- **vgplot** (`Ionsto/vgplot`): backslash/quoting fixes in `print-plot`.
- **swank.live**: no-op `update-swank` stand-in.
- expokit skipped on Windows (`magicl:expm` only used in commented-out code).

Related: [[windows-port]]. Table in `docs/development.md`.
