---
title: CL-MPM architecture
type: concept
tags: [architecture, mpm, asdf]
sources: ["[[refactor-2026-10-14]]", docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md, docs/AI_HANDOVER.md]
updated: 2026-10-16
---

# CL-MPM architecture

Time step (`cl-mpm:update-sim`): P2G → nodal momentum update with BCs → G2P and particle motion → constitutive update (Hencky/Kirchhoff, optional C++ `kirchoff.dll`) → optional non-local damage → adaptive dt.

`src/` directories: `core`, `models`, `damage`, `bc`, `solvers`, `dynamic-relaxation`, `ssa`, `mpi`. ASDF systems live in `cl-mpm.asd`.

Platform switches: `:win32` ⇒ `:cl-mpm-no-mpi` ⇒ serial [[serial-mpi-standin]]; expokit skipped. Dependencies are patched, see [[magicl-patches]].

Full text: `docs/architecture.md`. Parent: [[cl-mpm]].

## Migration target, 2026-10-16

P0 inventory is complete: 884 captured tracked paths exactly once, 104 native
ASDF registrations and 11 passing audit-integrity checks. Only two hash-bound
P1 source extractions are approved; 882 semantic reviews remain pending.
P0 was pushed as `6f15148` before moves. The matrix and hash-bound approvals are
immutable pre-extraction evidence; do not regenerate them after moves. See
`docs/architecture/FILE_MIGRATION_MATRIX.json` and the execution log for scope.

P1 production extraction `3cd172e` was pushed before tests: component contracts
now live in `src/simulation/components/{base,specifications}.lisp`, the material
definition in `materials/core/definition.lisp`, and the native factory in
`materials/adapters/native.lisp`. Sixteen defining forms and the whole factory
file retain exact bytes; class/package symbols, ASDF IDs and old path shims remain.
Focused contracts, normal/legacy loaders and snapshot escape checks pass; bounded
VM 27-update/MC two-update controls have strict two-state PASS with CSV/positions
zero. MC cliff VTKs match exactly; its unavailable gnuplot PNG is not a plot PASS.
The initial ownership/SBCL-tail and snapshot-registry fixture failures are retained;
only tests/fixtures changed. P1 is PROVISIONAL, G1 PARTIAL, full G3 NOT_RUN/preparing.

The user supplied `docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md`
as the primary migration reference. The complete target remains pending beyond P1.
`codex/material-architecture-migration` starts from the `7c399fb` checkpoint of
[[reusable-simulation-framework]]. P0/G0 requires a complete actual-file matrix,
ASDF/load/Windows/Studio/caller map and form-level ownership for mixed source
before any code moves. The specification's 884-file remote inventory does not
cover untracked local work or prove that semantic audit complete.

Root `materials/` is the final owner of material models, model state, evolution
and diagnostics. A material definition is a parameter/provenance profile, not
a constitutive solver; evolution belongs within its model. Shared utilities need
real cross-model reuse. Generic engine/numerics/orchestration remain in `src/`,
reusable procedures belong in `scenarios/`, and `cases/` composes components.
Material code must not depend on scenarios or Studio; generic solvers call
constitutive protocols without embedding model laws or creating ASDF cycles.

Preserve package/class identity, native backend, equations, algorithms, defaults
and numerical results. `framework/` remains temporary compatibility until G5
proves all active callers/entry points have transitioned. P2 is plan only; P2–P6
are NOT_RUN. Saved exact VM 2D/3D and
serial Joss controls are baseline evidence; four-worker FAIL and loaded-provenance
limits remain explicit. [[mc-hardening-softening-study]] physics integration is
deferred until migration gates, then requires a separate experimental branch.

Studio extends the existing particle law through a dedicated CLOS subclass
and shared loader/stress guard, preserving the core solver. See
[[studio-custom-models]] and [[studio-verification-2026-10-14]].
