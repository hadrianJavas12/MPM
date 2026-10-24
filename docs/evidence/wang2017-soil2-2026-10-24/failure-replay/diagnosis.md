# Actual Soil2 failure: coupled softening return has no admissible solution

The Windows native replay reproduced the exact retained rejection **once**,
using all271 files from the failed run's pre-load snapshot plus a new diagnostic
driver. Native replay exit0 means the expected rejection was reproduced; it does
not turn the failed slope run into a successful simulation. No solver step,
material parameter, production equation or tolerance was changed.

The original run saved loading states through5.7s/57mm. That is the last saved
frame, not the exact rejected substep time. Its failure reason is neither the
monotonic-history guard nor multiple-root ambiguity.

For zero dilation each MC plastic flow direction has zero trace. Isotropic
elasticity therefore leaves the returned Kirchhoff mean equal to the trial mean.
Summing the MC yield inequalities gives the necessary bound

`mean(tau) <= J*c(kps)*cot(phi)`.

The actual trial mean is25187.121534136833Pa; at oldkps=.016529047726561334
the bound is25187.530471637343Pa. Therefore the OLD state does not exceed the
apex mean bound. The issue is the additional cohesion loss required by the
coupled return. Along c=30000-750000*kps, fixed mean permits only
`kps <= .016529428794191926`, a remaining increase of3.81067630593e-7.

All nonsingular sorted-frame active cases were evaluated with the exact existing
production primitives and all real quadratic roots. The positive history roots
satisfy the unsquared norm equation, but are inadmissible:

| Active planes | Positive kps root | Maximum yield excess (Pa) | Further rejection |
| --- | --- | --- | --- |
| [1] | .016531145506297758 |18.6908678451 | ordering and negative plastic work |
| [0,1] | .016530992706548266 |3.23248680781 | ordering and negative plastic work |
| [1,3] | .016531014310861247 |4.82649236395 | ordering, negative multiplier and negative work |

All three positive roots exceed the fixed-mean maximum. The stress tolerance is
1.25222803826e-6Pa; these are substantive violations. The other quadratic roots
are negative kps, which cannot equal a tensor norm. There is no positive
history-decreasing root among these face/edge branches. At residual cohesion15kPa
the same necessary mean bound is exceeded by3724.3958822754284Pa, so the residual
tail cannot supply an admissible solution either.

## Independent apex compatibility check

Rank deficiency of a three-plane zero-dilation system alone would not establish
that no coupled apex solution exists. At an apex, returned stress must instead
equal the fixed mean on all three axes. Its unique principal plastic increment is

`(trial - mean)/(2G) = (2.23014323146e-6, -5.60032472617e-7, -1.67011075885e-6)`.

Mapping that increment through the captured trial eigenbasis and adding the
captured rotated Ep requires `kps=.016530943069873974`. But MC apex compatibility
requires `kps=.016529428794191926`. The mismatch1.51427568205e-6 is far above the
history tolerance1e-13. Thus the singular fixed-k implementation is not hiding an
admissible coupled apex solution for this input.

`candidate-admissibility.json` retains every coefficient, root, unsquared residual,
multiplier, yield value, ordering/work check, residual-tail coordinate and apex
certificate. `replay-result.json` records the one actual replay call and unchanged
capsule hash. Source/provenance before and after identify the actual copied DLL.

No implementation fix is justified by this capsule. It demonstrates failure of
this discrete signed-tensor softening/zero-dilation return at this captured input,
not proof that all smaller-step trajectories or the paper's FEM model fail.
Any tensile/apex completion, alternative history interpretation or integration
continuation must be specified and validated explicitly. Changing dilation,
strength, a history maximum, or tolerances merely to complete the slope is not a
supported resolution.

The first diagnostic harness attempt001 failed before any capsule replay because
its helper name collided with COMMON-LISP:BOOLEAN. Its log, frozen sources and
zero-call failure record remain intact; only the new driver name was repaired in
fresh attempt002. No constitutive source was changed.
