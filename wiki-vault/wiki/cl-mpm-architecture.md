---
title: CL-MPM architecture
type: concept
tags: [architecture, mpm, asdf]
sources: [[[refactor-2026-10-14]]]
updated: 2026-10-14
---

# CL-MPM architecture

Time step (`cl-mpm:update-sim`): P2G → nodal momentum update with BCs → G2P and particle motion → constitutive update (Hencky/Kirchhoff, optional C++ `kirchoff.dll`) → optional non-local damage → adaptive dt.

`src/` directories: `core`, `models`, `damage`, `bc`, `solvers`, `dynamic-relaxation`, `ssa`, `mpi`. ASDF systems live in `cl-mpm.asd`.

Platform switches: `:win32` ⇒ `:cl-mpm-no-mpi` ⇒ serial [[serial-mpi-standin]]; expokit skipped. Dependencies are patched, see [[magicl-patches]].

Full text: `docs/architecture.md`. Parent: [[cl-mpm]].
