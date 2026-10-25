# Proposed opt-in perfect MC composite apex

25 October 2026. **Design only; production implementation and tests NOT_RUN.**
This is a new constitutive experiment following the strict SRF1.6 failure,
not a successful completion or repair of that original physical law.

## Actual failure and reason

The captured trial has mean Kirchhoff stress27574.643436Pa. Its Cauchy-strength
apex bound is `pA=J*c*cot(phi)=27483.866984Pa`: an excess90.776452Pa. All six
regular psi0 flow directions have zero trace. Isotropic elastic correction
therefore preserves mean stress. Summing all six yield inequalities requires
`p<=pA`, so a regular return cannot satisfy this actual state. The original
rejection is correct within that constitutive scope, independently of searching
more roots. The original sources, capsule and single replay remain evidence.

## Separate model and restricted domain

Create an explicit optional model, tentatively
`cl-mpm/models/mc-composite-apex:particle-mc-composite-apex`. Restrict its first
implementation to constant perfect-plastic Cauchy cohesion/friction,phi>0,
regular psi=0. Reject evolving laws or other dilation conventions. Preserve
the original model and strict projector as the default.

The extra mode is `fA=p-pA<=0`, `gA=p`, active at the hydrostatic apex. This
adds positive plastic volume; it is a constitutive assumption, not unchanged
zero-dilation MC at every stress state. It introduces no new strength fitting
parameter. The earlier Wang composite-apex experiment is an algebraic precedent,
not a Soil2 law to load or hardcode into this perfect-plastic material.

For isotropic elasticity `G=E/(2(1+nu))`, `K=E/(3(1-2nu))`, an apex candidate is:

```
d_i = (trial_i - pTrial)/(2G)
q   = (pTrial - pA)/K
deltaEp_i = d_i + q/3
returnedTau_i = pA
kappaNext = kappaOld + existingJ2Increment(deltaEp)
```

Require q>=0, finite values, six-plane yield admissibility, full elastic
compliance, nonnegative shear transfer multipliers and the additional apex
multiplier q. Check `trace(deltaEp)=q`, `work=pA*q` and nonnegative elastic
energy release beyond plastic work. Preserve actual increments; no stress-only
reset, max-history replacement or exception-triggered clamp is acceptable.

For this constant-strength/psi0 restriction, when `pTrial>pA` the trace proof
excludes exact regular roots. Numerical acceptance needs a stronger bound:
if each of six planes is allowed the EXISTING stress tolerance `tol`, summing
their inequalities gives `pTrial-pA<=tol/(2*sin(phi))`. Preserve the exact old
elastic screen first. Use the analytic apex branch only when the mean excess
is strictly larger than this existing-tolerance bound. Delegate the remaining
domain, including equality and the tiny positive cap band, to the unchanged
strict projector with all its rejection/ambiguity behavior. If that delegated
band rejects, retain the rejection; do not silently select an apex afterward.
This conservative numerical scope is explicit, not a widened tolerance or
exception-triggered fallback. Test the equality and both sides of the bound.
Do not extend this proof silently to evolving laws.

## Software and verification gates

1. Review this proof and scope before production edits; keep the old strict
   model, numerical constants and failure evidence unchanged.
2. Add a small generic particle-projection dispatch hook to the existing owned
   constitutive transaction; its default method calls the strict projector.
   The new particle specializes the hook. Reuse the existing state, rollback,
   elastic reconstruction, J2 history, plastic-volume and work bookkeeping.
   Do not copy the whole constitutive method or replace global functions.
3. Keep model code under root materials/, optional ASDF loading, and a dedicated
   diagnostic adapter that clearly records the apex convention/activation,
   separate multiplier lambdaA=q, accumulated volume and plastic work. Prefer
   a derived projection structure whose scalar apex fields survive the existing
   copy-structure/owned-array transaction; verify copying/rollback explicitly.
   A post-commit current-minus-committed value of zero must not hide last-return
   flow. No UI changes.
4. Run relevant default native/point regressions and a bounded byte comparison
   because the dispatch path changes. No old full solver is required. Freeze
   every new executed source/DLL before testing.
5. Test the new model analytically: actual failed-state inputs, pure hydrostatic
   tension, deviatoric apex, all principal permutations, elastic and regular
   identity, transition continuity/unchanged tolerances, unsupported laws,
   work/compliance/volume/J2 identities and owned native rollback/state.
6. Verify a few genuine MPM updates with new diagnostics in CSV/VTK and an
   independent saved-data check before a new full slope run. New saved-data
   auditing must identify the composite model rather than label it strict MC.

## Next experiment, conditional on all gates

Keep SRF1.6/geometry/grid/boundaries/2s gravity ramp/6s duration/dtScale/PPC/
mass/damping unchanged. The ONLY new physical convention is this explicitly
declared material flow. Do not launch the old SRF2.0 screen as a workaround for
an incomplete1.6 result. Freeze a separate new case/contract before execution,
compare the retained strict saved prefix honestly, and inspect coherent mass,
localisation and runout using the same physical-metre observer. If a valid
coarse slide occurs, confirm that SAME material/factor on h0.5.

Completion, colour, volume-flow activation or a solver rejection alone cannot
prove landslide. These assumed materials and adapted/fixed-base geometry remain
uncalibrated; a valid numerical experiment is not field or paper validation.
