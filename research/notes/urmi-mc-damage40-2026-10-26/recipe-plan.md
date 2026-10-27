# Source-only recipe contract: drained equilibrium to undrained strength damage

## Superseding implementation decision27October, before any MPM recipe result

The initial proposal below is retained as design history, not the executable
contract. Owned point961c17a8/transfer946dbce7 gates now pass. The transfer
uses reviewed scratch clones and ONE atomic all-particle vector swap, preserving
logical IDs by order rather than original object identity. Full native dt0
material return on each clone is part of the declared instantaneous switch;
compliance-change and plastic-release energy proxies are separated. Nothing
is reset to fake equilibrium or erase accumulated native history.

Before the first MPM gate, freeze exact recipe constants: damping
0.4*sqrt(Ed/rho)/h in1/s, RF<=1e-4 and free-nodal
RK=KE_free/(free_nodal_mass*abs(g)*10m)<=1e-8, nonzero denominator required.
Require consecutive qualifying checks spanning at least1native second after
the gravity ramp, then >=1s and >=100updates undamped with EVERY check passing.
Preparation cap60000updates AND20native seconds; dynamic target60s/301frames,
max200000updates. No velocities/stress/history/nativeclock reset. Failure
preserves the result and stops without strength/geometry/tolerance tuning.
Current recipe/pipeline/full slope still NOT_RUN; this paragraph supersedes
the earlier numerical proposal below rather than rewriting past evidence.

27 October 2026. Branch `codex/urmi-mc-damage-slope40`; plan only. No new
scenario/runner, transfer implementation, test or solver execution is implied.
The [material plan](constitutive-plan.md) is a separate prerequisite. This is
an Urmi-inspired parameter/history adaptation, not the paper's calibrated
three-dimensional history, pore-pressure solution or failure-time prediction.

## Fixed proposed case and phases

- Domain60x20m; straight40degree face, relief10m above a4m foundation; crest
  x12m, toe x23.9175359259421m, no notch/upper vertical face. Foundation spans
  the domain and uses the same evolving soil, with no Joss protected cohort.
  Sample a full grid-aligned rectangle and clip its surface at
  `4+max(0,10-tan(40deg)*max(0,x-12))`; record actual sampled mass/geometry.
  Do not require the non-grid-aligned toe itself to be a grid extent.
- h0.5m,2MPs per cell axis, one worker, USF/FLIP, mass scale1, Fbar/splitting/
  removal/ghosts disabled. Left/right x rollers, bottom x/y fixed, top free;
  the bottom remains a numerical boundary, not a calibrated frictional bed.
- Fix g=-9.80665m/s2 and density=17000/9.80665kg/m3 to represent17kN/m3.
  Drained G4.05MPa,nu0.33,E10.773MPa,c3700Pa,phi30.6degrees; propose psi0
  as an explicit numerical assumption requiring review, not a paper inference.
  Plasticity is active from the zero-stress/zero-velocity origin onward;
  drained strength is constant and damage inactive.
- Smoothstep gravity ramp2s, then full-gravity drained hold. Preregister
  preparation viscous damping `0.75*cp_drained/h` in the engine's1/s convention;
  dynamic damping0. Use dt=0.2*the actual native stable estimate in both phases.
  Preparation is capped at20s and200000updates; the total attempt also has a
  12h wall deadline, which is a bound rather than an ETA. Failure stops this
  case without strength/geometry/tolerance tuning.
- After accepted equilibrium and the atomic switch below, request60s dynamic
  time. Keep native time/history continuous; record separate preparation and
  dynamic clocks (`dynamic_time=native_time-transfer_time`), with no velocity,
  displacement, F, stress or history reset. Save both original and transfer
  positions for honest motion measurements. Undrained G remains4.05MPa,
  nu0.45,E11.745MPa,phi=psi=0 and the reviewed40.5kPa strength-damage law.

## Preregister equilibrium acceptance

Measure physical undamped forces at the `update-node-forces :after` location
before essential BCs erase constrained components. Use a new owned **serial**
reduction over active nodes/in-plane free DOFs, identified from `node-bcs`:

`RF=sqrt(sum_free((f_internal+f_external)^2)/sum_free(f_external^2))`.

Mask BOTH sums; a zero/nonfinite denominator fails rather than receiving an
arbitrary floor. The existing `scenarios/slope-descent/geometry.lisp` diagnostic
is a code-path reference only: its denominator includes constrained DOFs and
its shared threaded accumulation must not be copied unchanged.

Measure free-DOF nodal KE after velocity BC application, before G2P, and
`RK=KE_free/(initial_mass*abs(g)*10m)`. Require RF<=1e-3 and RK<=1e-8 at ten
consecutive0.1s checks after the ramp. Also require finite positive mass/volume/
J, unchanged particle IDs/count and mass relative error<=1e-12, and the
existing native material admissibility checks. Then remove preparation damping
and require the same thresholds throughout a further1s hold, without zeroing
velocities. Any failure resets the consecutive count; preparation caps still
apply. The label "equilibrium" is permitted only after these measured checks;
220 fixed elastic updates do not satisfy this contract.

## Atomic all-particle transfer, pending a reviewed material API

Use the same particle objects throughout. Require a phase-aware optional
particle/transfer API which validates the drained phase before construction;
the current undrained point class alone is not evidence of that interface.
Do not use unproved `change-class`, particle reconstruction or generic
`reinitialize-instance` to perform the transition.

1. At an accepted load-step boundary, freeze an all-MP before signature and
   deep `mc-evolution:snapshot-particle` records, including committed baselines.
   Preserve positions, domains, masses/current/reference volumes, F/J, Cauchy
   stress, cumulative kappa, plastic volume/work and native equivalent-history
   fields. Save per-MP `kappa_origin=kappa_committed=kappa` as a *new offset*,
   not a replacement history. Existing foundation particles follow this too.
2. Prepare every prospective result on owned scratch values before changing
   any live MP. Shift the reviewed cohesion table by each origin, retaining
   an explicit constant prefix from global kappa0 to that origin (deduplicate
   zero origin); preserve the native monotone global kappa coordinate. The
   material factory must retain the actual peak origin, including origin0,
   without changing the public builder's defaults. Initially strength=sup,D=0.
3. With preserved J and sigma, set tau=J*sigma and reconstruct the complete
   engineering-Voigt elastic Hencky vector by **new3D isotropic compliance**:
   `eps_ii=(tau_ii-nu_u*(tau_jj+tau_kk))/E_u`,
   `gamma_ij=tau_ij/G_u`. Do not impose a new eps_zz=0: elastic out-of-plane
   strain can balance prior plastic strain under total plane strain. Preserve
   the native shear ordering `(xx,yy,zz,yz,xz,xy)` and stress/strain conversion
   distinction; no fabricated deformation or principal vectors are needed.
4. Stage E/nu, law/strength/phi/psi, the owned phase/origin, tau and reconstructed
   `mp-strain`, `mp-strain-n`, `mp-trial-elastic-strain` together. Refresh
   elastic matrix, tangent stiffness, p-modulus0 and deformation-corrected
   current p-modulus through the actual native setters/estimators. Preserve
   F/F0, volume/volume-n and physical geometry. Clear only a proved stale
   drained projection/iteration diagnostic, replacing its yield residual by
   the independently evaluated new-law residual; do not zero plastic history
   or invent a plastic increment. Log every intentionally changed slot.
5. Validate every prospective MP and all invariants, then commit all MPs while
   the simulation is paused. Record a new complete committed baseline using
   the reviewed native load-step path. On any error restore **all** original
   snapshots, owned slots, baselines and simulation clock/damping metadata;
   stop, retaining the original error. Audit snapshot coverage before relying
   on it: current MC transaction slots omit physical position/domain data, so
   transfer must never mutate those. Add phase/origin to transaction slots.
6. Recompute stable dt from the refreshed stiffness before advancing. The next
   native USF step resets/remaps the grid; never evaluate mixed drained/
   undrained particle forces or reuse stale grid diagnostics as a new state.

Stress outside the new undrained surface is recorded, not projected away by
the transfer. Its relaxation belongs to the first real accepted native update;
strict failure/multiple-root rejection remains authoritative. Preserving stress
while changing compliance changes elastic energy: report the before/after
`0.5*sum(V*sigma:engineering_elastic_strain)` proxy and its separate *material
switch* difference. Preserve native plastic-work totals; do not count the
difference as plastic dissipation, fracture energy or a closed energy budget.

## Required gates and source references

Before any large initialization, a **new point-transfer gate** must cover
nonzero drained kappa/work and nonidentity positive-J F, full shear/normal
stress, origin0/nonzero origin, new compliance reconstruction, finite caches,
admissible-stress zero-increment reproduction, explicitly overstrength
first-return behavior, commit/reset and forced failure at a late MP proving
whole-cohort rollback. Include appropriate J/face/edge controls; the material's
local Tresca slope argument is not a guarantee for every positive J. Only then
implement an owned scenario and a bounded native equilibrium/transfer gate;
full60s remains NOT_RUN until those gates actually pass.

Relevant code: `src/core/stress-update.lisp:update-strain-kirchoff` reads
strain-n before the stress return; `src/core/particle-protocols.lisp` defines
native commit/reset; `materials/models/elastic/particle.lisp` defines E/nu
setters, elastic/tangent caches and stiffness estimators;
`materials/models/plastic/mohr-coulomb-evolution/{state,material}.lisp` owns
deep transactions, strength/history and Kirchhoff return;
`src/core/simulation-base.lisp:update-stiffness-mps` and
`src/geometry/setup.lisp:estimate-elastic-dt` consume current stiffness;
`src/solvers/explicit/usf.lisp` fixes force/BC/KE/commit ordering. Reuse the
frozen-source CLI/provenance machinery with a new exact scenario; the current
gravity-slope compiler's perfect-law/zero-foundation contract is not this case.
