# M2 dedicated MC H/HS return-mapping design

Date: 2026-10-16. **Design only: no constitutive implementation or solver run.**
Repository HEAD observed during review: `843eba21378668f2087a878979486b896a017ede`.
Live remote refresh found framework at that commit and main at `efd0358`.
M0 contracts/regression remain a separate gate. Implementation belongs on the
experimental branch root creates after the M0 checkpoint; main is unchanged.

## 1. Native contracts and reasons for a dedicated implementation

The existing [MC method](../../src/models/plastic.lisp#L328) forms trial stress
from elastic strain, calls the native return map, updates the shared scalar
plastic accumulator, and then changes cohesion/friction by exponential
softening. Its outer loop executes once (`:361`); the strength update at
`:404–416` is therefore not a coupled final-yield solve. Preserve it unchanged.

The [C++ adapter](../../src/cpp.lisp#L244) mutates the supplied elastic-strain
array. A missing foreign library selects the [Lisp fallback](../../src/cpp.lisp#L300),
so backend provenance matters. Both implementations construct the apex using
`sigc/(k-1)`: [C++](../../libs/src/constitutive.h#L230),
[Lisp](../../src/constitutive.lisp#L890). At zero friction this expression is
undefined, including `0/0` for zero cohesion. This is source-level evidence;
no new negative-control execution was performed or claimed.

The native stored yield value is the trial value, not the final residual:
[C++ return](../../libs/src/constitutive.h#L305),
[Lisp return](../../src/constitutive.lisp#L1031). Generic plastic loadstep
[reset/commit](../../src/models/plastic.lisp#L421) covers the scalar accumulator,
not a complete evolving strength/history transaction.

Use a new optional Lisp package/system, proposed under
`research/models/mc-hhs/`, with a dedicated `particle-elastic` +
`particle-plastic` descendant and explicit H/HS subclasses or variant records.
Its method must not call the legacy MC return or modify `particle-mc`, VM,
global stress-update methods, or the DLL. Framework adapters select the class,
state diagnostics and exports only. An opt-in source-freezing path must copy
and load this optional system and its laws before running; a live-source load
from a case file would invalidate the existing copied-source provenance claim.

## 2. Explicit stress, strain and law conventions

Native stress is tension-positive. Let `J=det(F)>0`, `tau=J*sigma` and
`p=-tr(sigma)/3`; report Cauchy `q=sqrt(3*J2(dev sigma))` separately from the
triaxial axial-minus-mean-lateral projection. The engine's
[stress update](../../src/core/stress-update.lisp#L284) expects a returned
Kirchhoff stress, copies it, then divides by J for Cauchy output. Return **tau**
exactly once; do not pre-divide the constitutive result.

Require finite `E>0`, `-1<nu<0.5`, positive density, `c>=0`, nonnegative kappa,
and `0<=psi<=phi<pi/2` for the initial supported family. Reject out-of-range
inputs rather than clamping them; negative dilation is a separate extension.
The friction/cohesion references are effective-strength inputs, whereas the
present engine has no pore-pressure calculation. Any spatial experiment must
declare its total-stress surrogate/effective-stress idealization and cannot
claim a full CU path merely by using those numbers.

For isotropic elasticity, in the trial principal basis:

\[
 D=2G I+(K-2G/3)\mathbf1\mathbf1^T,\qquad
 \tau^{tr}=D\epsilon_e^{tr},\quad G=E/[2(1+\nu)],\ K=E/[3(1-2\nu)].
\]

The proposed reference convention is **Cauchy cohesion in Pa**. At the fixed
kinematic endpoint use `eta=J` below. An explicitly named Kirchhoff-strength
compatibility option would use `eta=1`; it is a different constitutive choice
at `J != 1`, not an automatic conversion or legacy-equivalence claim. For the
residual-soil pair `c=0`, these choices have the same yield admissibility;
Zhan's nonzero cohesion requires the choice to be recorded and tested.
This choice needs implementation review before activation.

Define the new dimensionless accumulated equivalent plastic strain by

\[
 \kappa_{n+1}=\kappa_n+h(b),\quad
 h(b)=\sqrt{\tfrac23}\|\operatorname{dev}b\|_F,\quad
 b=\Delta\epsilon^p=\epsilon_e^{tr}-\epsilon_e^{new}.
\]

Accumulate this norm **per accepted constitutive subincrement**, not the norm
of the total historical tensor, not total axial strain, and not the sum of
individual active-plane norms. The latter would depend on a nonunique
multiplier representation at corners. Native principal plastic increments
use `sqrt(3/2)||dev b||`, hence the native scalar equals **1.5 times** this
equivalent increment for the same b; see
[native formula](../../libs/src/constitutive.h#L283).

Itasca's documented shear parameter uses `||dev b||/sqrt(2)` on its shear
correction, giving `Delta kappa_Itasca=(sqrt(3)/2)*Delta kappa_eq` under that
same tensor interpretation. Its documentation also updates strength after
stress correction, so the proposed coupled algorithm below is deliberately
not a claim of FLAC algorithmic identity.
([Itasca SSoft, equations 1–6 and implementation procedure](https://docs.itascacg.com/itasca950/common/models/ssoft/doc/modelssoft.html))

The source slides' deviatoric-plastic-strain label and x20 note do not identify
an exact tensor convention. Initial experiment configuration must declare
`table_coordinate = kappa_eq` as an **illustrative mapping assumption**, or
supply a separately documented mapping. No inferred 1.5, 2 or x20 multiplier
is applied to source coordinates. Keep the M1 reference files immutable.

Strain Voigt entries have engineering shears; stress entries have tensor
shears: [Lisp strain conversion](../../src/utils.lisp#L521),
[C++ separate conversions](../../libs/src/utils.h#L61).
Use explicit conversions and full tensor norms; passing stress through the
strain converter halves shear and changes eigenvalues. This is an incremental
elastic logarithmic-strain correction compatible with the engine's kinematics,
not yet a verified finite-strain multiplicative plasticity formulation. Store
scalar accumulated shear/volume measures and the current plastic increment;
do not call an untransported sum of spatial tensors an objective finite-strain
plastic history. Rigid-rotation tests are mandatory.

## 3. Shared mechanics and H/HS law table

Both variants use the same elasticity, initialization, pressure, dilation,
algorithm, tolerances and pre-peak laws. The only primary treatment is the
post-peak law. Interpolate **angle versus coordinate** piecewise linearly in
degrees, convert to radians at the constitutive interface; interpolation of
`tan(phi)` would be a different law. Require unique increasing coordinates,
finite values and declared endpoint behavior.

| Item | H | HS |
| --- | --- | --- |
| Reference pre-peak `(kappa, phi_deg)` | `(0,0), (0.0068,27.10), (0.037,33.99)` | Identical |
| Post-peak | Clamp phi at 33.99 deg | Linear through `(0.1,27.62), (0.2,16.34)` |
| Beyond final point | Peak plateau | Clamp last value |
| Cohesion, residual-soil pair | 0 Pa | 0 Pa |
| Baseline dilation | 0 deg | 0 deg |
| Initial coordinate | 0 | 0 |

Do not initialize H using HS's residual endpoint or skip H's pre-peak branch.
Alternative positive initial friction/cohesion is a separate declared
illustrative experiment applied equally to H and HS. Preserve the raw
zero/zero table as the primary reference data. Zhan laws form a different
dataset and case family; pressure-dependent elasticity would require its own
explicit integration choice, not reuse of this fixed-D derivation unchanged.

## 4. Six-plane formulation and coupled local solve

The following is the proposed project derivation. Work in one trial principal
basis without repeatedly reordering the returned components. For every ordered
pair `i != j` (six planes), define

\[
 n_{ij}=(1+\sin\phi)e_i-(1-\sin\phi)e_j,\qquad
 F_{ij}=n_{ij}^T\tau-2\eta c\cos\phi\le0,
\]
\[
 m_{ij}=(1+\sin\psi)e_i-(1-\sin\psi)e_j,\quad
 b=\sum_a\lambda_a m_a,\quad \tau=\tau^{tr}-Db,
\]
\[
 \lambda_a\ge0,\quad F_a\le0,\quad\lambda_aF_a=0.
\]

This unscaled yield expression equals the existing
`k*tau_max-tau_min-2*eta*c*sqrt(k)` times `(1-sin(phi))`, and avoids dividing
by `k-1`. The potential differs from the yield normal when `psi != phi`.
The sign and friction/dilation split agree with the documented MC convention;
a tensile cutoff is a separate model choice.
([Itasca MC, equations 4–10](https://docs.itascacg.com/itasca950/common/models/mohr/doc/modelmohr.html))

All strength and flow coefficients in the accepted solution are evaluated at
**kappa_new**, not at kappa_old followed by an unchecked property update.
For an active set A, let N contain the active row normals, M the active flow
columns, and `s=2*eta*c*cos(phi)`. At a candidate kappa:

\[
 A(\kappa)=NDM,\quad
 A\lambda=N\tau^{tr}-s\mathbf1,\quad
 R(\kappa)=\kappa-\kappa_n-h(M\lambda)=0.
\]

Practical bounded algorithm:

1. Deep-copy the committed state, trial elastic strain, F/J and immutable law
   identity. If all six trial F values at kappa_n are admissible, return the
   elastic candidate with unchanged kappa. A surface point with zero increment
   does not acquire plastic strain merely because F equals zero.
2. Split the kappa search into table segments, including the plateau. Enumerate
   face/edge/vertex active sets (at most 63 subsets) and test dependent-plane
   cases explicitly. Warm-starting from the previous active set is an
   optimization only; never accept the first approximate candidate blindly.
3. On each smooth segment solve the fixed-kappa linear system with
   rank-revealing factorization; derive b and R. Use safeguarded root finding
   with segment limits and active-set validity events. Newton derivatives must
   include c', phi' and, if allowed, psi'; the simpler fixed-psi baseline is
   preferred. A root outside its segment or with negative multipliers is invalid.
4. Recompute all six F values and the plastic-strain constraint from the
   candidate. Verify equilibrium correction, nonnegative multipliers, active
   equalities, inactive inequalities, finite state and elastic strain/stress
   reconstruction. Reconstruct the full tensor using the original eigenvectors.
5. Rank deficiency is expected at Tresca limits and repeated eigenvalues.
   Reduce to independent flow directions and establish existence of
   nonnegative original multipliers. A minimum-norm/pseudoinverse result alone
   is not a complementarity proof. Equivalent multiplier representations are
   acceptable only when they produce the same stress, b and kappa. Check all
   dependent yield planes afterwards.
6. If several distinct admissible candidates remain, or no bounded solve
   converges, retry smaller constitutive subincrements from the untouched
   committed snapshot, preserving the prescribed total kinematic path. Locate
   table knots/peak transitions as events. Use explicit caps on iterations and
   subdivisions; record these in output. Failure after the cap is an explicit
   material failure, with no partial state commit.
7. Softening may lose uniqueness. Continue from the previous accepted
   incremental branch and require step-refinement convergence; report multiple
   roots rather than selecting by enumeration order, minimum stress, or the
   preferred collapse trend. No uniqueness theorem is claimed for this HS law.

For a differentiable segment, the yield sensitivity needed by a coupled
Jacobian is explicit:

\[
 \partial_\kappa F_{ij}
 =\cos\phi\,\phi'(\tau_i+\tau_j)
 -2\eta(c'\cos\phi-c\sin\phi\,\phi').
\]

At knots use a one-sided/semismooth treatment with final residual checks.
Define separate, unit-bearing constitutive stress, strain, multiplier and
rank tolerances before implementation and log them. Stress residual scaling
must use a declared Pa scale; it must not silently permit different physics
at different confining pressures. Existing regression tolerances stay intact.

MOOSE's official implementation separates plane, edge and tip return paths;
its specialized fast return is documented for isotropic elasticity and fixed
dilation. It is a useful independent algorithm/test reference, not code to
copy into a differently defined kappa law.
([MOOSE user object](https://mooseframework.inl.gov/source/userobjects/SolidMechanicsPlasticMohrCoulombMulti.html),
[official return-map source](https://mooseframework.inl.gov/docs/doxygen/modules/SolidMechanicsPlasticMohrCoulombMulti_8C_source.html))

Sysala and Cermak provide a primary treatment of nonsmooth face/edge/apex
returns. Their stated assumptions include positive cohesion and friction/
dilation angles and nondecreasing hardening. Their existence/uniqueness
results therefore do **not** establish our zero-angle, zero-cohesion,
friction-evolution or softening cases.
([paper, version 3, sections 3–4](https://arxiv.org/html/1508.07435v3))

## 5. Zero friction, zero cohesion and the non-associated apex

At `phi=0`, the six planes are `tau_i-tau_j-2*eta*c <= 0`: the Tresca limit,
with a hydrostatic cylinder rather than a finite MC apex. For baseline
`psi=0`, use the same exact traceless directions `e_i-e_j`. No cotangent,
angle epsilon or apex division is needed. At `phi=c=0`, admissibility reduces
to equal principal stresses; remove trial deviatoric stress while preserving
the trial mean. A hardening table that begins at this point must still solve
the coupled final-phi equations: returning to zero shear using old phi and
then increasing phi is not the intended algorithm. Under compressive mean
stress a coupled solution may exist; this is a hypothesis to verify, not a
reason to replace the raw point.

For `phi>0`, a hydrostatic apex satisfies
`tau_apex=eta*c*cot(phi)`. Since `tr(m_a)=2*sin(psi)`,

\[
 \operatorname{mean}(\tau)=\operatorname{mean}(\tau^{tr})
 -2K\sin\psi\sum_a\lambda_a.
\]

Thus with `psi=0` the mean cannot change. For fixed strength, a hydrostatic
tensile trial mean above the apex cannot be corrected by these MC shear
directions. If strength evolves, first test the full coupled admissibility
problem; the `c=0`, positive-friction, tensile-mean case remains incompatible.
Do not force an isotropic stress projection or replace psi by a positive
number. Return an explicit unsupported-state condition containing trial mean,
current strengths, kappa, active set and residuals. Subdivision cannot repair
a constitutively impossible state by itself.

A separately declared Rankine tensile cutoff/cap could add its own yield
surfaces, potential, strength, state and complementarity equations, identically
for H and HS. It is an additional physical model, not a silent apex repair.
No tensile strength has been supplied for the residual-soil pair, so this is
outside the first implementation. Positive-dilation/associated apex returns
are accepted only if the complete equations and nonnegative multipliers pass.

## 6. Transaction, diagnostics and acceptance boundary

The pure point integrator takes an immutable committed state and trial
kinematics, and returns a candidate plus status. It must not mutate MP arrays,
law tables or committed history while trying roots/active sets/subincrements.
Only a fully accepted result publishes elastic strain, tau, kappa, strength,
plastic increment, volumetric plastic measure and diagnostics together.
Strength can be derived from kappa plus immutable law identity; if cached,
it must be checked against that law at commit and restored on rollback.

Provide dedicated deep snapshot/restore/copy and `new-loadstep-mp`/
`reset-loadstep-mp` methods; call the base kinematic methods in a specified
order. Repeated trial evaluation from the same committed state must give the
same candidate, independent of failed trials. Whole-step rollback also needs
stress/strain/F/volume and solver-owned state: a material snapshot alone does
not promise simulation-level retry. Check the actual solver commit lifecycle
([USL](../../src/solvers/usl.lisp#L68), [base commit](../../src/particle.lisp#L1067)).
Keep generic homogeneous/controls disabled until their trial code uses these
complete hooks; the current VM-only restoration is insufficient.

Export actual class/variant, stress measure, table-coordinate mapping, current
c/phi/psi, committed/trial kappa, corrected maximum and per-plane residuals,
plastic increment, active planes, iteration/subdivision counts, law/source
hashes, units and conventions. Keep legacy VM-only CSV fields unavailable.
Use the positive elastic CFL modulus initially; a softened tangent is not a
safe replacement timestep bound without separate verification. Track plastic
work and elastic energy; do not infer guaranteed total energy closure or
hardening free-energy consistency from a small yield residual alone.

## 7. Required test matrix before spatial comparative runs

Two **unexecuted analytical fixtures**, chosen for implementation tests rather
than transcribed material data:

- Tresca: `E=24 MPa`, `nu=0.2`, hence `G=10 MPa`; J=1,
  `phi=psi=0`, `c=10 kPa`, and trial principal stress
  `(-20,-80,-50) kPa` in a fixed axis order. The exact return is
  `(-40,-60,-50) kPa`, `b=(0.001,-0.001,0)` and
  `Delta kappa_eq=0.002/sqrt(3)`. Mean stress stays -50 kPa and the maximum
  principal difference is 20 kPa. This exercises phi=0 without apex division.
- Impossible zero-dilation apex: J=1, fixed `c=0`, `phi=30 deg`, `psi=0`,
  and `tau_trial=10 kPa*I`. Every yield plane has F=10 kPa, while every
  allowed plastic correction is traceless. Expect explicit unsupported-state
  failure and unchanged committed state, rather than a projection to zero.

| Group | Required cases and invariant |
| --- | --- |
| Elastic | Hydrostatic compression, unload/reload and small shear; unchanged kappa, exact elastic response, positive J/volume. |
| Stress measure | J=1 and J!=1, c=0 and c>0; independently evaluate Cauchy and Kirchhoff residuals with declared cohesion measure. |
| Smooth faces | Known principal trial state with constant c/phi/psi; analytic lambda=F_trial/(n^T D m), all six inequalities. |
| Corners | Both triaxial compression/extension edges, repeated eigenvalues, principal permutations and random rotations; same tensor answer and kappa. |
| Degenerate limits | phi=0,c>0 Tresca; phi=c=0; near-zero angles/cohesion; rank deficiency without parameter floors or NaNs. |
| Apex | Associated/positive-dilation admissible cases; psi=0 incompatible tensile mean must reject with untouched committed state; no hidden tensile cap. |
| Coupled laws | H/HS identical before peak; exact knots, peak continuity, H plateau, HS residual clamp; corrected yield after strength evolution. |
| Raw initialization | c=phi=kappa=0 under 100/200 kPa confinement plus deviatoric loading; establish coupled solvability, step convergence and declared strain mapping. |
| Transactions | Trial A, failed B, repeat A; deep rollback and cross-particle copies; no aliasing of arrays/tables; rejection leaves all committed bytes intact. |
| Integration | Bounded point driver first, then bounded spatial MC, native 3D triaxial, and legacy VM/MC regressions with exact executed-source provenance. |
| Sensitivity | Constitutive subdivision/timestep and, later, mesh/MP size; local post-peak softening has no established mesh objectivity. |

This report adds no passing constitutive-test claim. Root owns the branch,
implementation approval/checkpoint and broader regression sequence. A native
zero-friction negative control, if still useful beyond the existing guard
test, should be proposed as a bounded diagnostic before execution. No fitting,
slide-curve digitization, new DLL, pore-pressure model or scientific validation
is included here.
