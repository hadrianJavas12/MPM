# Perfect-MC false edge candidate: independent numerical diagnosis

Date: 2026-10-24, Asia/Jakarta. Scope: read-only algebra from the first actual
unnotched SRF1.40 failure capsule. No Lisp projector replay, solver update,
constitutive change, parameter change or revised tolerance was executed here.
The separately owned single native replay remains a different evidence item.

## Exact source identity

- Capsule: `output/unnotched-gravity-2026-10-24/srf1p4-001/mc-integration-failure.json`,
  SHA256 `d0fa089970adf81178ca486f00423d53e0dffa98ba963823e822037e6e5f15bb`.
- Executed frozen projector: `output/unnotched-gravity-2026-10-24/srf1p4-001/source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp`,
  SHA256 `01c73c007726118fa40908cb7de929b8d17900c94b1f2fe3596d7afe81b2ce79`.
- Capsule gives E=100 MPa, nu=0.3, J=0.9994429892631845,
  c=7142.857142857143 Pa Cauchy, phi=14.57307514751742 degrees, psi=0,
  constant perfect plasticity and old kappa=0.000028098409018042926.
- Last saved frame is0.9 s; the failed attempted time is about0.980934788 s.
  This note does not assign the capsule a particle ID or treat saved VTK as a
  complete restart checkpoint.

## Closed-form face/edge calculation

Sort the supplied principal Kirchhoff stresses, preserving the eigenvalue
permutation for eventual caller coordinates:

```
t = [-32893.52608312133, -32901.247161468484, -73496.70798211521] Pa
G = E/(2*(1+nu)) = 38461538.461538464 Pa
s = sin(phi)
q = 2*J*c*cos(phi) = 13818.406108398893 Pa
```

In the executed six-plane ordering, face1 is pair(0,2), and face3 is pair(1,2).
Their yield normals are n1=(1+s,0,s-1), n3=(0,1+s,s-1), while their psi=0
flow vectors are m1=(1,0,-1), m3=(0,1,-1). Both flows have zero trace, so the
bulk modulus drops out exactly. Define f1=n1.t-q and f3=n3.t-q. The edge system
is the following ordinary2x2 linear problem, with no nonlinear history search:

```
A = 4G
B = 2G*(1-s)
[A B; B A] * [lambda1; lambda3] = [f1; f3]
```

The face-only solution lambdaF=f1/A is positive. Its stress correction is
`tauF=t-2G*lambdaF*m1`. Independently evaluated using NumPy linear algebra:

- lambdaF = approximately1.00373014e-7;
- tauF = approximately[-32901.24708416,-32901.24716147,-73488.98698107] Pa;
- sorted gap tauF0-tauF1 = approximately7.73e-5 Pa, positive;
- inactive face3 residual rho=f3-B*lambdaF = approximately-9.67547458e-5 Pa;
- face1 residual is approximately1.46e-11 Pa;
- other five-plane inequalities are satisfied, and plastic work is positive.

Now eliminate lambda1 from the edge system:

```
S = A-B^2/A > 0
lambda3 = rho/S
lambda1 = (f1-B*lambda3)/A
```

For0<=phi<90 degrees and psi=0, the displayed Schur complement is positive.
The sign of lambda3 therefore equals the sign of the inactive residual at the
face return. Here rho is strictly negative by about56 times the existing
stress tolerance. The proposed two-plane edge requires a negative plastic
multiplier and is physically inadmissible under the declared flow rule:

- edge lambda3 = approximately-7.31303101e-13;
- edge lambda1 = approximately1.00373287e-7;
- edge tau = approximately[-32901.24710521,-32901.24710521,-73488.98701628] Pa;
- maximum difference from the valid face stress = approximately5.6254e-5 Pa.

The other regular edge basis(0,1) has a much larger negative multiplier
(approximately-0.00032454) and negative plastic work. Three independent
psi=0 flow directions cannot span a hydrostatic direction: the3x3 apex bases
are rank deficient. This establishes the valid regular face, without choosing
between two genuinely nonnegative perfect-MC solutions.

The sign was additionally checked by70-digit Decimal arithmetic on the fixed
binary double inputs/G/sin(phi)/strength constants. This is a high-precision
linear calculation, not a high-precision trigonometric or native replay claim.
It preserves the negative edge multiplier and positive face sorting gap; the
approximately1e-4 Pa inactive residual is far above floating arithmetic noise
in operations on approximately1e5 Pa stresses.

## Why the implementation rejects the actual run

The current admissibility predicate permits every multiplier down to-1e-12,
an absolute dimensionless strain-like allowance. That admits the above negative
edge multiplier at E=100 MPa, despite its stress consequence. Existing
stress tolerance is1e-6+1e-11*max(abs(trial))=1.734967079821152e-6 Pa.
The negative flow alone contributes about5.6254e-5 Pa in principal stress and
1.12508e-4 Pa in a plane residual, respectively32 and65 times that tolerance.

Both candidates otherwise satisfy the executed residual/sorting/history/work
checks. Their stresses differ by more than the existing duplicate bound
16*stressTolerance=2.7759473277138432e-5 Pa, so both are retained as distinct
roots and the honest ambiguity guard rejects the step. Increasing duplicate
tolerance, picking a face preferentially, or clamping the negative multiplier
would conceal the complementarity defect instead of resolving it.

## Recommended numerical remedy, not yet implemented by this diagnosis

Keep the current stress/history/duplicate tolerances and material parameters.
Tighten the nonnegative-multiplier criterion using a dimensionally consistent
backward-error budget, evaluated for every active basis. One conservative
additional condition is:

```
sum over negative lambda_i of
  abs(lambda_i) * max(norm_inf(D*m_i), max_j(abs(n_j . D*m_i)))
  <= existing stressTolerance
```

Retain the old absolute multiplier limit as an additional upper bound, so this
only tightens admissibility. The sum of absolute contributions prevents
cancellation from hiding individually negative flow. No actual multiplier or
stress is clamped or altered: an inconsistent candidate is rejected. The bound
has stress units, scales automatically with elastic modulus and dilation, and
uses the existing stress error budget. The same formula applies to all
principal permutations; J affects the Cauchy-strength offset rather than
introducing an arbitrary stiffness-specific multiplier threshold.

A still stricter alternative is a certified sign test for perfect-law linear
systems using interval/backward-error bounds. For the displayed psi=0 edge,
the Schur residual rho supplies a direct sign criterion: a resolvably negative
rho and positiveS prove the edge inadmissible. Near-zero signs must be judged
against arithmetic error and the unchanged stress tolerance, with genuinely
ambiguous cases still rejected. Do not assert a mathematically exact sign from
an arbitrary unscaled floating epsilon.

Required scoped regression evidence before another full attempt:

1. The separately retained actual capsule must admit the unique nonnegative
   face without changing its law or inputs; full source/outputs retained.
2. Boundary fixtures on both sides of the face/edge transition: valid face,
   exact zero edge multiplier, positive edge multiplier, and resolvably negative
   edge multiplier. Check residuals, sorting, work and complementary signs.
3. Equivalent stiffness/unit scalings and J values, both canonical edges and
   all six principal permutations. A fixed strain tolerance must not determine
   which mathematically valid branch is accepted.
4. Preserve legitimate multiple-root rejection for evolving/nonlinear laws;
   do not turn a newly filtered false root into blanket uniqueness claims.
5. Verify unchanged input arrays/particle rollback and unchanged legacy default
   behavior within existing tolerances; genuine bounded native MPM afterward.

This diagnosis identifies a numerical admissibility issue. It does not prove
that the coarse gravity/SSR adaptation will exhibit a verified landslide or
quantitatively correct runout after repair.
