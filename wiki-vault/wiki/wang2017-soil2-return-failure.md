---
title: Wang Soil2 coupled-return failure
type: synthesis
tags: [wang2017, soil2, constitutive-failure, native-windows]
sources: [docs/benchmarks/WANG2017_SOIL2_FAILURE.md, docs/testing.md]
updated: 2026-10-24
---

# Wang Soil2 coupled-return failure

Subsequent checkpoint: [[wang2017-apex-flow]] now passes its isolated native,
regression and actual two-step output gates. It is a declared separate material,
not a repair/reclassification of the strict failed experiment described here.

[[wang2017-soil2-native]] fullfast010001 source621146b ended native/worker1
at08:26:52WIB, before wall budget.58actual states end5.7s/57mm/19608updates;
the manifest19820 includes later unsaved work. Capsule time/particle ID were
not recorded, so this is last SAVED displacement rather than exact failure time.

The captured strict zero-dilation/signed-tensor softening return has no
admissible solution. Old-strength mean is still0.40894Pa below its apex bound,
but all positive coupled face/edge roots require excessive softening for fixed
mean. Independent apex history also differs from the required coordinate by
1.5143e-6 versus1e-13 tolerance. It is neither history guard nor multi-root.
One exact frozen native replay reproduces the expected rejection; diagnostic
exit0 does not mean a successful slope.271original sources plus new driver272
and actual copiedDLL are verified. Initial replay harness name collision is
retained with zero actual capsule calls; no constitutive algorithm changed.

Saved F/J/Ep/law/contact/mass/ID checks hold. Paperkps reaches0.016084896,
minimum cohesion17.9363kPa; no free upper-slope mass crosses the original toe.
The fastest saved particle moves upward.58exact shared settlements versus
Soil1 give final reaction−3.3061%, not convergence or a verified failure band.
The14.5s playback shows58real states at4fps, scale1, INCOMPLETE label, full decode0.

All348recorded geometric strip gaps are nonnegative. Positive reconstructed
mean tension is near free surfaces, not sustained recorded upward-pulling
contacts. A unilateral platen is therefore not a demonstrated correction.
The nearest Ep signature suggests MP627 but is an inference, not exact capsule ID.

[[wang2017-apex-and-rate-study]] describes standard additional tensile/apex
conventions and original C++ behavior. A parameter-free explicit hydrostatic
apex-flow extension is under review, with full strain/history/transaction/work
consistency and coexisting-root checks required. It is not enabled and would
be a declared new opt-in model. Rankine tension cutoff needs a tensile-strength
assumption absent from the paper inputs. No hidden clamp or strength/psi tuning
is justified by this failure; no new slope starts before the next model gate.
