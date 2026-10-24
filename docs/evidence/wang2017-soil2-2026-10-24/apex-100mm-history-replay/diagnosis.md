# Actual composite-apex history-scope rejection

One Windows-native replay, exit0, actual capsule replay calls1, actual variant
dispatch calls1; zero MPM updates. Source3caa6bea5d447be34c8bd1104311f1aa34b57986.
All275 actual failed-run source files were copied unchanged, plus one new driver.
All276 source hashes match before/after. The actual copied kirchoff.dll mapping
was verified by GetModuleHandleW/GetModuleFileNameW before/after; SHA256
57c4c9a6cedb1ade1202914074dab942afc2f15abb114637619ca3cb5d9f074f.
Original capsule SHA2563ad314d3416df31122a2a628056b847cbe46e687cb89c90b349964ee892da926.
No failed-run evidence or production source was changed.

## Reproduced cause

The unique accepted pure projection is HYDROSTATIC-APEX. All ordinary regular
candidate branches were enumerated: zero admissible regular roots. The native
adapter then rejects kps0.03187108863369348 ->0.03187108746386819,
delta−1.169825285252113e−9, exceeding its1e−13 monotonic-scope tolerance.
Rotated oldkps0.03187108863369347 matches the committed value to roundoff.
This is a real signed-tensor norm decrease, not transport-roundoff, an absent
return root, multiroot ambiguity, timeout, or a denominator/apex failure.

Both old/new strengths are EXACTLY cohesion15000Pa, phi0.6108652381980153rad
(35deg), psi0rad. Both coordinates exceed the residual onset0.02. Therefore
this particular transition does not increase any strength parameter. The
current blanket monotonic-norm guard excludes it even on a flat residual law.
The tensor-norm coordinate can decrease under nonproportional increments while
the independent additive J2 grows; no maximum-history replacement is needed to
explain this state. The accumulated signed-tensor definition is the current
interpretation of [Wang2017 Eq5–6](https://doi.org/10.1007/s11629-016-3951-1),
with the separately declared incremental-polar transport approximation.

Projection diagnostics: tau=21646.557995733045Pa in all principal directions;
unsquared history residual0; maximum MC residual3.63798e−12Pa;
plastic work+0.004953389208998423Pa (Kirchhoff), Cauchy proxy+0.004902053892478047Pa;
plastic volumetric increment+2.2883033921443711e−7;
independent J2 increment+3.5276291130274547e−7. Detailed tensors, multipliers,
all quadratic/tail candidates and exact inputs are retained in JSON. Positive
point work and admissibility do not establish global energy or slope validity.

## Recommendation before any code change

An explicit OPTIONAL residual-only signed-history scope is defensible for this
same fixed curve: allow norm decrease only if oldkps>=0.02 AND newkps>=0.02 AND
all old/new law values (cohesion, friction, dilation) are exactly equal. Keep the
strict model/default1e−13 guard unchanged; reject every transition entering the
softening interval or increasing any strength. Preserve the actual signed Ep
and coordinate, with no max, clamp, strength/rate/dilation tuning or tolerance
change. This is a disclosed scope extension, not a claim that Wang prescribes
this finite-strain history convention or that any slope must collapse.

Before applying it to a new slope run, require focused frozen native controls:
actual captured projection allowed only by opt-in residual scope; strict replay
still rejects; softening/history-strength increase still rejects; threshold
crossing rejects; equal residual strengths pass; positive work/volume/J2 and
literal state retention; deep snapshot/copy/loadstep/reset/rollback; capsule
policy and replay dispatch. Do not rerun the old strict actual capsule or broad
old controls absent a relevant change. A new actual-input control must be
counted explicitly, not labelled another replay of this diagnostic attempt.

## Rollback limitation

This replay has no particle state and does NOT prove full-MPM rollback for the
actual failed step. The immutable input file and frozen sources match before/
after. Static failed-source inspection shows the history guard before every
material write; the existing outer update-stress around method restores its
registered snapshot on error. Prior synthetic transaction controls are separate
evidence. No second actual constitutive call was made to inflate this claim.
The failure capsule has no full-solver time/particle ID; last saved9s/90mm is
not the exact rejected-step time or displacement.
