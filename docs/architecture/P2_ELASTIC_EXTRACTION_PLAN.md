# P2 elastic ownership extraction — conditional plan

Date: 2026-10-16, Asia/Jakarta. Planning basis: P1 implementation `3cd172e`,
with `src/particle.lisp`, `src/constitutive.lisp`, `src/cpp.lisp` and their native
ASDF dependencies inspected directly. **NOT APPROVED / NOT IMPLEMENTED.**
P1 focused validation is running; no P2 production edit, native test, solver job
or binary build is authorized by this document. Do not deploy P2 before P1's
required full regressions and snapshot/provenance acceptance.

## Scope and invariants

Move existing elastic definitions to root `materials/`, without adding a model,
registry, algorithm, parameter, class, subclass relationship or numerical feature.
Keep every original `cl-mpm/particle` and `cl-mpm/constitutive` symbol, slot,
initarg, accessor, method qualifier and exact defining form. In particular keep
`:elastic-approxmation`, `particle-elastic-truesdale` and `:plane-strain` unchanged.
`src/models/elastic.lisp` is a package-only stub, not the implementation to move.
Preserve legacy source paths and ASDF system/component identities with explicit
relative paths and forwarding loaders that normal ASDF does not also evaluate.

This is two conditional checkpoints: **P2a formulas only**, then separately
reviewed **P2b class/state and response extraction**. P2a is partial elastic
ownership, not completion of P2/G1. The material-state extraction is substantially
larger than moving five constitutive functions and must not be smuggled into it.

## Existing order and dependencies

`cl-mpm.asd:97–126,245–254` currently establishes:

```text
magicl/utils/fastmaths → cl-mpm/constitutive (src/constitutive.lisp)
                     → cl-mpm/ext (src/cpp.lisp)
constitutive/ext/mesh → cl-mpm/particle:
                       src/particle.lisp → models/plastic → models/concrete
```

Arrows mean prerequisite before consumer. `cl-mpm/constitutive` does not depend
on particles, damage, setup, framework or a simulation scenario. `cl-mpm/ext`
already consumes its formulas; retaining that lower position avoids a cycle.
The native bridge, DLL search path, ABI, wrappers, fallback behavior and binary
remain unchanged throughout P2. Formula availability precedes native loading.

Within `particle.lisp`, the significant original evaluation sequence is:
base package/cache/particle → elastic classes/helpers → base initialization →
elastic initialization → fluid/viscous/thermal classes → generic constructor →
elastic constructor → stiffness generic → elastic stiffness → constitutive
generic → elastic response/variants → sibling responses → generic objective
helpers → damage classes → loadstep/energy contracts and methods.

VM/MC in `models/plastic.lisp:46,73` inherit `particle-elastic`; damage subclasses
in `models/damage.lisp:67` and finite viscoelastic state in `models/visco.lisp:328`
also require it. Particle viscoelastic/viscoplastic classes are declared at
509/517, before the later generic protocols; fluid is a sibling of elastic.
`models/concrete.lisp:10` has a forward-referenced `particle-elastic-damage`
superclass supplied later by `cl-mpm/damage`. Preserve that existing relationship;
do not add `particle → damage`, because damage already depends on particle/core.

## P2a: five formulas, with original evaluation order

Proposed actual target files, created only after approval:

| Target | Exact original forms/responsibility |
| --- | --- |
| `src/constitutive/package.lisp` | `src/constitutive.lisp:1–16`: existing package/exports, `in-package`, optimization declaration; no new namespace. |
| `materials/models/elastic/linear-elastic/constitutive.lisp` | Functions `linear-elastic-matrix` 20–32; `linear-elastic-principal-matrix` 34–42; `linear-elastic-matrix-ps` 44–56; `linear-elastic-mat` 58–70; `linear-elastic` 75–77 with its ftype declaration 72–74. |
| `src/constitutive/legacy-models.lisp` | Remaining original forms from 79 onward, in original order, including mixed numerical helpers and other models. This is temporary ownership debt, not a claim that those laws belong permanently in the engine. |
| `src/constitutive.lisp` | Historical source-path loader for package → elastic formulas → remaining forms. |

Retain `cl-mpm/constitutive` as the same serial system; add file components in
that order and preserve its historical `src/constitutive` component ID for the
remainder with `:pathname`. Normal ASDF must not also load the historical shim.
No new material subsystem is required. Each compiled fragment must receive the
same original package and optimization declaration; read-time settings must
exist before reading `#.cl-mpm/settings:*optimise-setting*`.
Do not change the tensor multiply, allocate/in-place result behavior, matrix
ordering or plane-stress/plane-strain formulas. Particle files remain untouched
at this checkpoint, so their class/evaluation sequence remains exactly intact.

## P2b: intact CLOS definitions, not a slot redesign

A complete elastic class move cannot simply remove the elastic definitions and
load a new file after the old particle monolith: viscous subclasses already
inherit those classes, and plastic classes load immediately afterwards.
Loading the elastic family first also fails because its base class/package and
generic protocols are currently embedded in that monolith. Preserve the exact
sequence using the following proposed serial fragments; **this larger split is
conditional and requires a fresh approval/manifest before any edit**.

All ranges below are from unchanged `src/particle.lisp`. Include the original
associated ftype/inline declarations and source comments in frozen extraction
manifests; repeat the original file optimization preamble for each compilation.

| Order | Original forms | Proposed target |
| --- | --- | --- |
| 1 | Package, node cache/helpers 1–53; `particle` 67–369 | `src/particle/base.lisp` |
| 2 | `particle-elastic` 380–403, `particle-linear-elastic` 405–407; modulus aliases/computation/update helpers 409–445; `(setf mp-E/mp-nu)` after methods 447–450 | `materials/models/elastic/hencky/state.lisp` |
| 3 | Domain setter 452–453; `initialize-instance`/`reinitialize-instance` on `particle` 455–483 | `src/particle/initialization.lisp` |
| 4 | Elastic initialization after method 485–489; approximation setter after method 490–491 | `materials/models/elastic/hencky/initialization.lisp` |
| 5 | `particle-fluid`, `particle-viscoelastic`, `particle-viscoplastic`, `particle-thermal` 493–551 | `src/particle/legacy-sibling-state.lisp` (temporary mixed owner) |
| 6 | `make-particle` 570–583 | `src/particle/construction.lisp` |
| 7 | `make-particle-elastic` 595–600 | `materials/models/elastic/hencky/construction.lisp` |
| 8 | `estimate-stiffness` generic 602–603 | `src/particle/stiffness-interface.lisp` |
| 9 | `estimate-stiffness-hencky` 605–609; elastic/linear methods 611–615; declaration and `estimate-log-enhancement` 617–637 | `materials/models/elastic/hencky/stiffness.lisp` |
| 10 | `constitutive-model` generic 640–643 | `src/particle/constitutive-interface.lisp` |
| 11 | Constitutive method specialized on `particle-elastic` 645–651 | `materials/models/elastic/hencky/constitutive.lisp` |
| 12 | Classes `particle-elastic-{inc,jaumann,truesdale,logspin}` and their constitutive methods 654–749 | `materials/models/elastic/objective-variants.lisp` |
| 13 | Fluid, viscoelastic, viscoplastic constitutive methods 751–812 | `src/particle/legacy-sibling-response.lisp` (temporary model ownership debt) |
| 14 | Original forms 814–1122 unchanged | `src/particle/legacy-tail.lisp` (mixed engine/damage owner, deferred) |

Preserve the existing `cl-mpm/particle` system as the ordered aggregation of
these files, followed by exactly the existing plastic and concrete components.
Keep `src/particle.lisp` as a historical source-path loader for this same order;
normal ASDF uses the fragments directly. No family depends on the full particle
umbrella that contains that family. These are file components under the existing
system, not a new circular set of ASDF systems or an independently loadable model
API. A later subsystem design must depend on a true lower particle protocol,
not `cl-mpm/particle` recursively; it needs separate review.

The fragmentation is the cost of retaining exact evaluation order. If judged
too large, stop after P2a; do not reorder all base/material state implicitly.
Consolidating fragments or creating independently loadable material systems is
outside this plan until dependency/evaluation changes have their own evidence.

## What remains engine-owned or deferred

The complete `particle` definition stays intact, including legacy damage slots
294–309 and modulus fields 287–293; no slot migration or new mixin is proposed.
Generic particle allocation, lifecycle and dispatch contracts remain engine
responsibilities. Objective helpers `assemble-vorticity-matrix`, `objectify-stress*`
824–909 and `matrix-sqrt` 913–923 remain generic engine/numerical code in the
deferred tail. The original methods precede those helper definitions today;
retain that order and resolve functions normally at call time.

The deferred tail includes `particle-damage-fundemental`/`particle-damage`
932–1035 and the damage-specialized loadstep method 1090–1115, alongside generic
loadstep/energy contracts 1039–1088,1120–1122. Do not promote that mixed tail to
the final engine contract without its own split review. Fluid/viscous state and
responses remain explicitly pending their family checkpoints; the thermal field
contract is generic. Do not move them into elastic merely because they share a
source file or elastic ancestor.

## Gates before either extraction can be accepted

1. **Precondition:** P1 full deterministic VM 2D/3D and serial Joss results, focused
   contracts and copied-source guards accepted; retain the known parallel-Joss
   failure as a failure. Refresh current branch/HEAD/live status before editing.
2. Approve source hashes/individual forms and target paths in the migration
   matrix. Freeze every executed source, inputs, ASDF definitions and DLL hashes;
   snapshot collectors must include all new fragments and prove resolved paths
   stay in their frozen tree. Historical evidence must remain untouched.
3. Prove complete defining-form/declaration coverage, exact bodies and once-only
   evaluation; preserve class objects, CPL/slots/initargs and generic/method
   signatures, including old source loaders and fresh-process legacy ASDF names.
4. Run Windows SBCL material-ownership normal/legacy checks, framework 10,
   material diagnostics 9, config 10, and Node check/tests; test relevant actual
   elastic constructors/stiffness/setter methods and sibling VM/MC construction.
5. Execute bounded native VM/MC/Joss controls, then unchanged full VM 2D/3D and
   serial Joss regressions for each approved numerical-source checkpoint. Compare
   the required CSV/VTK hashes/tolerances; preserve backend identity, class names,
   output order, failures and negative evidence. No new scientific validation is
   established by equivalent structural relocation.

Current status: plan drafted; P2a/P2b implementation and every P2 verification
listed above are **NOT_RUN**. This document authorizes no production migration.
