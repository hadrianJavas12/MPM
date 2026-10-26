# Optional composite-apex arithmetic and failure capture

26 October 2026, `codex/unnotched-mc-composite-apex`. This repair concerns
numerical evaluation of the already declared perfect-Cauchy `g_A=p` model.
It does not introduce a different strength, flow law, root, or tolerance.

## Actual failed run and what is unavailable

Fine run `srf1p6-composite-h05-001`, source `a07eb8f8`, exits native/worker1
at13:06:10WIB. It saves53 states through5.2s; attempted time5.27147981362577
and13590 updates include later unsaved work. The error combines compliance,
flow, yield and work checks, but supplies no failed predicate or trial capsule.
The exact failed trial and full-MP rollback replay are **unavailable**.
The trailing `NIL` is empty condition details, not a named predicate.

The FIRST prepared partial variant audit/render exits0: saved integrity and
variant checks pass,287 retained sources and stored DLL provenance agree.
NativeComplete remains false. Root inspects the actual scale1 PNG: an upper
wedge moves downslope above a localized plastic band. No toe runout is seen.
The53-frame video is INCOMPLETE0–5.2s,4fps/13.25s playback, no interpolation,
full decode0. Completion and scientific verification remain false. The
complete-pair comparator must keep rejecting this incomplete native result.

## One independent synthetic witness

The frozen `synthetic-roundoff-witness-001` executes exactly one unchanged
optional production-projector call and zero MPM/native-constitutive updates.
It returns native0 because it reproduces the preregistered rejection. It is
**synthetic, not an actual failed-trial replay**. The protocol and original
source are committed at `017f00ab`; old sources remain immutable in output.

With nonzero cap and a near-hydrostatic binary64 trial, all exact rational
identities hold. The old floating implementation passes seven named checks
and fails only work identity:

| Quantity | Observed value |
| --- | ---: |
| Sum of computed deviatoric plastic increment | -9.458744893459788e-20 |
| Signed work-identity error, Pa | -2.598768793772218e-15 |
| Existing work allowance, Pa | 2.0739050051842244e-18 |
| Existing stress allowance, Pa | 1.2747477432661654e-6 |
| Compliance error, Pa | 3.637978807091713e-12 |
| Volume-identity error in stress units, Pa | 7.882287390180198e-12 |

For the old `d_i=(t_i-roundedMean)/(2G)`, trace roundoff `delta=sum(d)`
contributes approximately `p*delta` to work error. Its scale follows the large
hydrostatic stress, while the work allowance follows the tiny plastic flow.
The existing near-cap controls with zero cap cannot expose this nonzero-p
amplification. This proves a false-rejection class; it does not establish which
predicate rejected the missing actual fine-run trial.

## Reviewed scope of the repair

For distinct axes i,j,k, use the algebraically equal expression
`d_i=((t_i-t_j)+(t_i-t_k))/(6G)`. Shared pair differences avoid cancellation
against a large rounded mean. All axes use the same formula; no component is
forced to close the trace. Independent source review finds the algebra correct.
Keep the existing mean, cap, q, branch screen, shear representation, compliance,
yield, work and energy checks and every acceptance tolerance unchanged.

The reference for a focused exact-rational work check must explicitly use the
unchanged binary64 q. A fully exact-mean q is a different rounding reference;
report that discrepancy separately instead of claiming arbitrary-precision
agreement of the entire return.

Add failure-only owned diagnostics at the two analytic failure sites. A new
optional schema and explicit variant must bind trial/E/nu/J/law/history plus
named measured residuals and limits. Preserve original reason/details and
termination if capture fails. Existing strict/Wang projector sources and strict
replay dispatch remain unchanged; strict replay must reject this distinct
schema. No capsule can recover the older missing state.

## Verification gate before a fresh attempt

New focused finite point controls must test the witness, six permutations,
nonzero-cap/deviator/J variation, ownership and unchanged checks. Rerun the
existing optional15-control regression because its arithmetic changed; do not
repeat unrelated historical gates. Capture controls must test optional schema,
JSON ownership/replay and preservation of the original failure on capture
errors, including native transaction rollback. Retain every failed attempt.
At this source checkpoint these repair controls are **NOT_RUN**.

A fresh full run is justified only after these relevant gates close and its
new source/runtime are frozen. It starts from the original initial state, with
the sameSRF1.6, mesh0.5, material and all other physical/numerical inputs.
Do not restart identically, extend duration, change strength/psi/geometry or
relax checks to obtain collapse. Any resulting motion remains subject to the
registered physical observer, spatial review and fixed-base/space-time limits.
