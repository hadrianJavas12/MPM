---
title: Serial MPI stand-in
type: concept
tags: [mpi, windows]
sources: ["[[refactor-2026-10-14]]"]
updated: 2026-10-14
---

# Serial MPI stand-in

`src/mpi/serial.lisp` defines package `cl-mpm/mpi` for builds with feature `:cl-mpm-no-mpi` (automatic on `:win32`). It provides the `mpm-sim-mpi*` classes, `mpi-sum` (identity), `in-computational-domain` (always T), `domain-decompose`, `make-mpi-ser`, and signals `mpi-unavailable` for real exchanges. The real MPI systems (`cl-mpm/dynamic-relaxation-mpi`, real `cl-mpm/mpi`) stay Linux-only.

Part of [[windows-port]]; see [[cl-mpm-architecture]].
