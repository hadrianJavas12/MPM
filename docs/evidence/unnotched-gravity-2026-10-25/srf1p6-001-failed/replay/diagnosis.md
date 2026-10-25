# SRF 1.6: original strict MC failure replay

The original frozen projector reproduced the captured rejection once, with one
principal call, zero MPM updates and native exit 0 for the expected-rejection
control. This is negative simulation evidence, not a completed landslide run.
No production code, model parameter or tolerance changed during the replay.

The executed helper is `source/case.lisp`; its SHA256 is
`67412ce7182fb12deca0a5b5b461f73c202d2d099f79da34354a81e5a168e73b`.
The adjacent `srf1p6-failure-replay-001-command.json` records the actual command;
the helper's inherited header comment names its older harness template.

## Actual result and source proof

- Capsule SHA256: `d557e0d82e1f1a2dd11e4365db0794076ea6397b6eab1257caec0ad101f6ef17`.
- All 283 copied files match their manifest and before/after hashes.
- All 281 shared failed-run sources match their executed failed-run bytes.
- The mapped native DLL was verified before and after with
  `GetModuleHandleW/GetModuleFileNameW`; SHA256
  `57c4c9a6cedb1ade1202914074dab942afc2f15abb114637619ca3cb5d9f074f`.
- Six active frames were observed. Three three-plane systems returned singular;
  face/edge candidates retained the trial mean and failed admissibility.
- The four full candidate observations include actual repeated solver calls;
  they are not four distinct physical roots. The two unchanged-admissibility
  predicate calls both rejected. The negative-multiplier filter was not reached.
- All temporary observation wrappers were restored and capsule bytes unchanged.
- Whole-particle/MPM rollback: **NOT_EXECUTED**. The capsule lacks that full state.

## Why there is no regular zero-dilation return

The supplied trial mean Kirchhoff stress is 27,574.643436065642 Pa.
For the actual supplied J, the MC apex mean bound is
J c cot(phi) = 27,483.866984069227 Pa. The excess is
90.77645199641483 Pa; the unchanged stress tolerance implies only
0.000002881505839243264 Pa of necessary mean allowance.

Each of the six regular psi=0 flow vectors has zero trace. Their plastic
increment therefore preserves the trial mean under the actual isotropic
elastic compliance. Meanwhile the sum of the six MC plane residuals is
12 sin(phi) [p - J c cot(phi)] = 241.6264830941653 Pa. If every plane were
admissible, their sum could be at most 0.000007669919969764285 Pa.
Thus no regular psi=0 return can meet the existing tolerance, independently of
root-search implementation. This is an inherited tensile/apex closure limit,
not evidence that the earlier negative-multiplier fix failed.

An isotropic apex return would require positive plastic volume strain
1.0893174239569781e-6 and would have final-stress plastic work
0.02993865518346253 Pa. Those are hypothetical algebraic values only.
Positive work does not authorize that volumetric flow under strict psi=0.
An apex flow or tensile treatment must be a separately declared constitutive
model with its own gates; silently clamping stress would change the physics.

The exact numbers, all observed calls and unchanged input data are retained in
`tensile-apex-math.json` and `replay-result.json`. The replay-source verification
is read-only and does not execute another constitutive call.
