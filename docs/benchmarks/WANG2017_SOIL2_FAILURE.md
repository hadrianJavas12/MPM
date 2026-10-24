# Soil2 fast010: retained failure and next constitutive gate

24October2026, Windows native. Source621146b; branch
`codex/wang2017-soil2-landslide`. This document records a negative result,
not a completed landslide or paper validation.

## Actual outcome

Native and WMI worker exited1 at08:26:52WIB, before the wall budget. Gravity
converged at3400updates. The last58saved states cover0–5.7s/0–57mm;
frame57 has19608accepted loading updates. The failure manifest reports19820,
which includes later unsaved work. Exact rejected substep time/particle ID was
not captured. Do not label57mm as its exact failure displacement.

All915saved IDs remain stable. The saved F/J/Ep/cohesion/contact identities,
finite fields and masses are consistent. Minimum actual J is0.987137313;
maximum saved paperkps0.016084896 gives minimum cohesion17.936328kPa.
Roundoff-only last-step history decreases down to−2.17e-18 are far below the
declared1e-13 rejection threshold; saved-frame history never decreases.

This is not coherent landslide evidence. Among509free MPs originally above the
base, centroid motion is approximately+1.969mm horizontally and−17.827mm
vertically. No free upper-slope mass crosses the original toe. The fastest
particle moves upward. At58exact common saved settlements versus Soil1, final
reaction is628.164498 versus649.642362kN/m (−3.3061%); maximum position-field
difference is2.52254mm. These observations are not rate/mesh convergence or a
closed mechanical energy balance.

## Exact failed-point certificate

The actual capsule has trial principal Kirchhoff stresses
25160.399761995257/25178.161014574966/25222.80382584027Pa,
J1.0018908194640175 and committed kps0.016529047726561334. Its failure is
**no admissible coupled signed-history return**, not history guard/multiple roots.
One Windows frozen replay reproduces that rejection. Replay exit0 means the
expected rejection was reproduced, not that the slope simulation passed.

Zero-dilation shear flow has zero trace, so isotropic elasticity preserves the
trial mean. MC admissibility requires

`mean(tau) <= J*c(kps)*cot(phi)`.

At old cohesion17603.214205079Pa the bound is25187.530471637Pa, which is
0.408937501Pa ABOVE the trial mean25187.121534137Pa. The old Soil1 diagnosis
of an already-exceeded bound does not apply to this capsule. Softening instead
requires checking the bound at the returned history. At fixed mean it permits
only kps≤0.016529428794191926.

| Active case | Positive history root | Maximum yield excess |
| --- | ---: | ---: |
| Face[1] |0.016531145506297758 |18.6908678451Pa |
| Edge[0,1] |0.016530992706548266 |3.23248680781Pa |
| Edge[1,3] |0.016531014310861247 |4.82649236395Pa |

All exceed the feasible history maximum and fail additional ordering/work or
multiplier conditions; stress tolerance is1.25222803826e-6Pa. Other quadratic
roots are negative coordinates, not tensor norms. Residual15kPa cohesion also
fails the fixed-mean bound by3724.395882275Pa.

Singularity of a three-plane psi0 solve alone is insufficient evidence. The
unique hydrostatic fixed-mean return has deviatoric plastic increment
`(trial-mean)/(2G)`. Captured Q/rotatedEp imply kps0.016530943069873974,
whereas apex consistency requires0.016529428794191926. The difference
1.51427568205e-6 exceeds history tolerance1e-13. A missing singular solve is
therefore not hiding an admissible apex for this input. This certificate does
not prove all smaller-step trajectories or paper FEM paths would fail.

## Boundary evidence and remaining uncertainty

All348SAVED per-contact geometric gaps are nonnegative:0–1.113586842mm.
The saved data do not show a sustained upward-pulling displacement spring.
Actual assembled force uses a predicted-corner increment; unsaved individual
tractions are not reconstructable. Last geometric spring energy208.2404J/m
and signed command work19216.3369J/m are observations, not energy closure.

Reconstructed full mean Kirchhoff tension is positive in19last-saved MPs, all
within1m of their original free surface and none driven or within1m of driven
centres. The closest saved Ep signature suggests ID627 near the inclined free
face, but capsule ID/time are absent: this is an inference, not identification.
A compression-only platen would be a new boundary experiment, not a fix
established by these saved contact observations.

## Next model gate, before any new slope attempt

The strict model and failed raw/source evidence remain unchanged. Do not lower
strength, change psi, select a convenient root or relax tolerances to complete it.
The existing [apex review](WANG2017_APEX_REVIEW.md) explains why original C++
and commercial implementations can use an additional volumetric apex convention.
[Itasca's primary model documentation](https://docs.itascacg.com/itasca950/common/models/mohr/doc/modelmohr.html)
explicitly distinguishes shear/tensile flow and documents apex correction.
This is support for stating an extension, not proof that Wang prescribed it.

The parameter-free candidate under review adds an explicit hydrostatic apex
surface `fA=p-J*c(kps)*cot(phi)` with volumetric potential `gA=p`, alongside
the zero-dilation shear modes. Its hydrostatic correction must be a consistent
plastic strain/state/elastic-compliance calculation, not an unrecorded stress
reset. The deviatoric plastic correction determines signed tensor history;
the volumetric part follows the derived apex stress and cannot change that
deviatoric norm. Require nonnegative multipliers, admissibility, work/state
consistency, owned transactions and objective transport. Enumerate possible
coexisting smooth/edge/apex roots; no exception-driven arbitrary apex preference.
An independent review must establish a defensible branch rule before enabling it.
This would be a separate explicit opt-in material, not unchanged pure-shear psi0
physics or an exact paper claim. The next slope must wait until this constitutive
gate has passed.

A different standard extension is MC plus a tensile Rankine surface. It adds a
tensile-strength assumption not given by the available Wang inputs;0kPa would
be an assumption, not a recovered paper datum. It is not enabled here. Neither
option guarantees a landslide. Physical validity still needs mesh/rate/boundary
and reference-curve studies after a complete actual run.
