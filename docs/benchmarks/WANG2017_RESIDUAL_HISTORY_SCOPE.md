# Residual-strength history scope: diagnosis and controlled repair

## Actual failure

The 100 mm endpoint trial on source `3caa6be` exited native/worker 1 on
24 October 2026 at 15:55:34 WIB, before its wall budget. Its last saved output
is frame 90: 9 s, 90 mm and 30,960 accepted loading updates. The failure manifest
records 31,092 updates, including later unsaved work. The capsule does not
identify the exact failed solver time or particle ID.

One frozen replay of this new capsule reproduces the signed-history guard:
`0.03187108863369348 -> 0.03187108746386819`. The decrease exceeds the existing
`1e-13` roundoff allowance, but both states lie beyond the residual breakpoint
`0.02`. Cohesion, friction and dilation are exactly unchanged: 15 kPa, 35° and 0°.
The pure return is a unique admissible hydrostatic-apex solution; there are no
admissible regular roots. History residual is zero and maximum yield residual
is `3.64e-12 Pa`. Plastic work and volume increments are positive. Thus the
failure is a conservative history-scope exclusion, not strength recovery or a
missing return root. Full-particle rollback was not executed by that pure replay.

The failed run still does not establish a landslide: reaction peaks at
644.162 kN/m at 6.1 s, then drops 7.12% to 598.325 kN/m at 9 s. Residual strength
is reached, but no free upper-slope mass crosses the original toe. The saved
91-state audit and negative media are retained in
[`apex-100mm-001-failed`](../evidence/wang2017-soil2-2026-10-24/apex-100mm-001-failed/README.md).

The 0–60 mm prefix comparison remains **FAIL** under the pre-existing canonical
pointwise tolerances (`atol=1e-8`, `rtol=1e-7`, time `1e-10`). Three fields fail:
near-zero yield residual (maximum difference `1.656e-5 Pa`), shear stress
(`3.315e-6 Pa`) and roundoff-scale accepted-decrease flags (130 rows). Position,
reaction, Ep, kps and cohesion pass. Field-scale stress diagnostics do not replace
that pointwise failure. No tolerance is relaxed or historical evidence rewritten.

## Explicit opt-in policy

`particle-wang2017-soil2-apex-residual` adds a named history scope to the existing
apex model. The original strict and original apex classes retain their guard.
The new variant is `composite-apex-residual`, with metadata
`historyPolicy=residual-plateau-only`.

For a decrease beyond the unchanged roundoff allowance, acceptance requires:

1. Both old and new tensor-derived coordinates lie at or above the residual
   tail, derived from the fixed law's breakpoints.
2. All law values at the two coordinates are exactly equal, with no added
   boundary or strength-equality tolerance.

The actual signed tensor/history is retained, including its decrease. There is
no irreversible maximum, stress clamp, preferred root, strength reduction or
parameter adjustment. Softening/recovery transitions remain rejected. Point
projection, apex flow, elasticity, transport, contact and solver equations stay
unchanged. This widens the declared admissible history scope; it is not an exact
finite-strain convention uniquely prescribed by Wang.

This check constrains accepted endpoints. It does not prove that an arbitrarily
large internal path stays on the plateau. The captured increment is tiny and
far from the breakpoint; general pathwise behavior still needs step-sensitivity
and a separately justified integration convention. No scientific validation is
inferred from this bounded repair.

## Verification before a fresh run

Windows native integration: two input/adapter groups, the 18 strict native
regression groups, and eight new output groups all exit 0. The latter execute
exactly two genuine USF updates with 25 MPs, two VTKs, 50 material and four
contact rows. Those two VTKs and two CSVs are byte-identical to the retained
original-apex elastic control. This microcase does not exercise plastic failure.

Focused frozen controls exercise the new policy and actual native plastic
calls. Attempt 001 retains exit 1: 12 groups pass, while a constructor assertion
incorrectly expected degrees from an API returning radians. The missing group
alone passes in attempt 002, exit 0, with zero point/native calls; the 12 passing
groups are not repeated. These are 13 distinct groups across two attempts,
not a single 13-PASS process. Exact executed sources and failures are retained.
One final blank line was removed from the current test after execution for Git
whitespace checking; executable forms are unchanged, without a numerical rerun.

The new declarative case is
`cases/benchmarks/wang2017-soil2-apex-residual-100mm.lisp`. Its numerical inputs
match the failed 100 mm case: 0.01 m/s to 100 mm in 10 s, 101 saved frames,
45,000 update cap, same material strengths, geometry, mesh, BC, damping,
timestep and penalty. Only the explicit material/history-policy metadata differ.
A fresh run is required; VTK is not a full-state restart. Its common saved
prefix must be compared against the failed run, with unchanged tolerances and
byte identity reported where applicable. Native completion will still not
establish coherent landslide, free run-out, or quantitative paper agreement.
