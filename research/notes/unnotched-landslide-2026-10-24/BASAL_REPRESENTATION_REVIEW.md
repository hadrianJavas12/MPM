# Basal representation diagnostic: source review

26 October 2026. Technical review permits the first read-only diagnostic;
no production algorithm or physical input is changed. Execution is NOT_RUN
at this source checkpoint.

Hash-bound sources:

- `tests/benchmarks/gravity-basal-representation.lisp`:
  `89226a5e4cb750cd86f6f34c556348940e701ba1b1bd66e89dec343d964943e3`
- `research/references/unnotched-mc-ssr/basal-representation-contract.json`:
  `4fc3612add56ec073c4197e3608066928fcde7131e0a49b5a6af111156096b0b`

Root and an independent source reviewer find no blocking issue. The fixture
uses the native GIMP iterator's weights and non-Fbar signed gradients, unions
actual component masks correctly (Common Lisp zero is true), and distinguishes
constrained weights, signed gradients and absolute-gradient norms. Constant
and general affine reproduction are checked on full support; separate analytic
floor-crossing limits test the raw truncated basis. Actual initial MPs,
full-support controls and hypothetical probes are separate. Forbidden-call
traps and before/after actual-particle state checks guard the read-only scope.

Interpretation requirements:

1. Hypothetical probes include domains crossing the floor. They are explicitly
   non-admissible as actual initial MPs. Their partition loss does not establish
   an engine defect or loss of partition for actual particles.
2. Grid nodes sampled by hypothetical fields may be inactive in a real dynamic
   solution. This measures interpolation space, not a native velocity solution,
   best approximation, stress update or attainable trajectory.
3. The chosen cap field is already zero on the fixed base. A zero raw-minus-
   masked difference does not disprove near-base smearing or constitutive
   locking. Pointwise errors include finite-domain and nodal sampling effects.
4. The retained formal circle has negative normal forces; no physical/global
   FoS, corrected circle search or automatic authorization for a long run follows.

First invocation, fresh directory only:

```powershell
.\windows\cl-mpm.cmd tests\benchmarks\gravity-basal-representation.lisp `
  output\mc-composite-apex-2026-10-26\basal-representation-001
```

Retain every failure and exact executed sources/runtime. No old tests, MPM
updates, constitutive calls, static search, rendering or solver run is repeated.
