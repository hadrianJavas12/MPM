# After the coarse SSR pair: recommended next study

25 October 2026, Asia/Jakarta. Read-only scientific design review at
`8d8b544d4e79d31d76f6d94c1304b883ba431b4e`, branch
`codex/unnotched-gravity-benchmark`. Live main remains `9e97e001`.
**Conditional plan only: geometry/static cross-check and refined runs NOT_RUN.**
No new literature search, test, material call, solver, process check or case was
executed for this note. The SRF1 result is pending; its already launched control
must be reviewed and compared before selecting another full simulation.

## Recommendation

**Close the pair, then check the exact geometry and independent static stability
before spending roughly two hours on h=0.5 m.** Refinement is a reasonable
subsequent diagnostic, but it cannot establish why this declared adaptation
differs from a paper whose complete polygon has not been visually verified.

The completed SRF1.40 run is already meaningful negative evidence: 61 states
reach 6 s with intact IDs/mass and admissible MC stresses, but maximum displacement
is only 12.083 mm. Its free-cohort centroid advances only 0.196 mm horizontally
and descends 0.0995 mm during the 2–6 s hold. Kinetic energy peaks at 7.099 J/m
at 1.8 s and finishes at 0.0589 J/m. No predeclared moving component or toe-crossing
mass appears. This is a settling/near-stationary response, not a slow landslide
that is established merely by extending duration.

## Cheap gate before another full run

1. Finish the SRF1/SRF1.40 comparison using identical saved times, physical
   observation region and whole/hold windows. If both settle, preserve that
   outcome. If the nominal baseline develops unexpected motion, investigate
   that disagreement before refining or changing any loading.
2. Record the actual static problem without a reproduction shortcut: polygon
   `(0,0),(32,0),(12,10),(0,10)`, no foundation, left/right x rollers, bottom x/y
   fixed, zero pore pressure, unit thickness. Confirm the source dimension
   correspondence and what is still unverified. The already specified ratios
   are `c/(gamma*H)=0.05`, crest/H=1.2 and face projection/H=2, with phi=20°.
   Matching these ratios does not prove that the full Xie geometry/boundary
   problem is identical. Do not silently add foundation soil or change the bed.
3. Obtain an inexpensive **independent static diagnostic for that exact polygon**
   before treating 1.40 as definitely supercritical. A dry circular-slip
   simplified-Bishop calculation is a practical first cross-check: freeze the
   circle/entry/exit search family before evaluating it, keep slip paths within
   the soil and above the fixed base, use the same family for both reduced
   strengths, and report search/slice refinement (for example 200 then 400
   slices) and any optimum at a search boundary. An unrestricted search or
   equilibrium method requires its own implementation checks; no static result
   is asserted by this note. Circular-slip LEM is an approximate diagnostic,
   not validation of a nonassociated finite-strain MPM path or calibrated
   runout. If it predicts stability at 1.40, a different geometry/reference
   interpretation is more immediately relevant than another MPM movie. If it
   predicts a credible near-critical mechanism, refinement can test numerical
   over-stiffness/localisation resolution without weakening the material.

The literature trail already records the classical 1.35–1.40 bracket and
locking/formulation differences; it does not establish that bracket for our
coarse explicit adaptation. See [primary SSR notes](strength-reduction-primary.md)
and [recipe audit](recipe-implementation-audit.md). Retrieving a complete source
figure later would be useful; no retrieval was attempted during this review.

## Conditional refinement preregistration

If the completed pair and cheap gate justify a resolution experiment, freeze a
new study contract **before** creating/running it:

| Item | Prespecified comparison |
| --- | --- |
| Physical problem | Same polygon/domain, gravity, density, E/nu, perfect Cauchy MC, SRF1.40, psi=0 and exact essential boundaries. No notch, driver, seed, added contact or strength search. |
| Numerical change | h=1 m to 0.5 m; retain 2 MPs per axis per cell, USF/FLIP, Fbar=false, damping=0 and mass scale=1. |
| Time | Keep 2 s smooth gravity ramp, 6 s total, 61 states at the same times and dtScale=0.2. Since stable dt falls with h, this is **coupled spatial/time refinement**, not isolated mesh convergence. |
| Budget | Expected MPs 880→3520 and updates about 7740→15480, giving roughly 8× material-update work. The completed launch-to-native interval was about 15.4 min; approximately 2 h is a planning estimate, not a completion promise. Retain the 3 h wall budget and honest incomplete status. |
| Integrity | Unchanged source-backed constitutive tolerances, source/DLL proof, full F/J/mass/ID/law/CSV–VTK checks. Native completion remains separate from motion/failure evidence. |
| Result | Compare centroid/displacement/velocity distributions, KE and plastic localisation over the same physical region and saved times. Report both positive and negative outcomes; do not raise SRF or extend duration after an unsatisfactory movie. |

**Freeze the observer in metres for the cross-mesh comparison.** The existing
contract deliberately uses h in its cohort cutoff, adjacency, displacement
thresholds and toe offset. Blindly rerunning it at h=0.5 changes both the soil
resolution and the success detector: cutoff 2→1 m, horizontal threshold
0.25→0.125 m, downslope threshold 0.5→0.25 m and toe offset 0.5→0.25 m. That is
not an equivalent comparison and must not manufacture a success claim.

Keep the original contract/results untouched. A new refinement comparison
should additionally preregister the coarse physical observer for **both** meshes:
initial x>2 m and y>2 m; initial-centre adjacency <=1.01 m; dx>=0.25 m and
downslope displacement>=0.5 m; connected moving mass >=10% of that cohort;
positive-dx mass fraction >=75%; the same component's mass-weighted vx>0.001 m/s
through every saved state of some 1 s interval; and the separate >=1% initial
total mass criterion beyond x=32.5 m. Preserve the 0–6 s and saved-2 s-referenced
2–6 s windows. Any h-scaled native diagnostic can also be reported, clearly
separately. IDs are not transferable between meshes: compare initial physical
regions and mass-weighted distributions/common spatial bins, not matched ID
numbers or isolated peak kappa values.

Fixed-bottom influence and small particle-domain overlap remain limitations.
Neither a refined onset nor agreement with an approximate static factor would
certify a Coulomb-bed runout prediction, mesh objectivity or exact paper
reproduction. A moving mass and its spatial failure mechanism still require
actual evidence. **Goal remains unachieved; no new run was launched for this review.**

## Existing evidence used

- [Study contract](../../references/unnotched-mc-ssr/contract.json).
- `output/unnotched-gravity-2026-10-25/srf1p4-002/review-001/physical-spatial-review.json`
  and the already inspected scale1 PNG; no second audit/render was performed.
- [Primary SSR references and claim boundaries](strength-reduction-primary.md).
- [Existing engine limitations](engine-fit.md).
