# Urmi-inspired MC strength damage, 40-degree slope

Human request26October, resumed27October2026. Branch
`codex/urmi-mc-damage-slope40` starts from `c2cd4069`.
The user explicitly chooses to retain soil MC, develop damage, and use a model
like Urmi. This supersedes the provisional Joss choice. The unused Joss work
is preserved on `codex/slope40-damage`; its4s/full runs never started.

## Constitutive choice and primary source

The immutable local paper `docs/Prediction of retrogressive landslide in
sensitive clays.pdf`, SHA256
`3f6aa9f5ba914564df3031aa8d6853ffef91b045a433446126e49316c150785a`, uses
MC with undrained phi0/Tresca and strength softening. It does not define a
stiffness-damage scalar. The old `make-urmi-evolution-law` is a generalized
adaptation, not literal piecewise Eq2; do not reuse its name as verification.

Use S1 reference values: G4.05MPa, weight17kN/m3, undrained nu.45 and derived
E11.745MPa; sup40.5kPa, intermediate suR3.8475kPa, remolded sur1kPa;
gamma_p.01, gamma_R1.8, gamma_r9.477, beta105 for the paper's h.5m calibration.
Drained c3.7kPa/phi30.6deg/nu.33, same-G derived E10.773MPa is a declared
elastic assumption. New geometry/history/normalization do not inherit the
paper's field calibration or dissipated energy.

The new field is constitutive strength degradation
`D_s=1-su/sup`, with `c=su`, phi=psi0 and unchanged elastic stiffness in the
undrained phase. D_s runs from0 to1-1000/40500=0.975308642; residual strength
is deliberate, not a numerical stress clamp. It is not crack opening or the
old Joss damage variable.

The literal peak/origin convention is unresolved by the paper: directly
connecting its fitted curve at gamma_p to the elastic peak gives a singular
DSS return. Use the explicitly NEW continuous normalized postpeak-total-DSS
curve in the [constitutive plan](../../research/notes/urmi-mc-damage40-2026-10-26/constitutive-plan.md).
Map total increment s to plastic engineering shear
`q=s+(sup-c(s))/G`, then kappa=q/sqrt3. This accounts for elastic unloading.
Its general MPM use is an objective equivalent-invariant adaptation, not a
claim that the paper specifies accumulated native J2 history. Alpha cancels
in normalization; it remains source metadata rather than an independently
fitted new parameter. Intermediate suR is not the final remolded floor.

Both root and independent source/math review accept the corrected mapping
for implementation with explicit limits: initial dc/dq is about-.487245G,
not the rejected direct-plastic-curve slope-.95025G. Native Cauchy strength
scales by J in Kirchhoff projection; the local worst-edge consistency bound
holds near J1 (approximately J<1.777 initially), not all positive J. Test
face and both edges/permutations/current J and preserve strict zero/multiple
root rejection. No root selection, fallback, strength/tolerance adjustment
or new hydrostatic apex mode is authorized.

## Required implementation and execution sequence

1. Optional owned material, bounded piecewise table (absolute chord error
   <=101.25Pa, <=64segments), actual zero-peak convention, read-only D_s from
   accepted cohesion, native transaction ownership and source-frozen point
   controls. Existing default MC/Wang/Joss sources remain unchanged.
2. Separate owned recipe: straight40deg/H10m/crest12m, no notch or driver,
  4m foundation of the same active soil, domain60x20m, h.5m/PPC2. These geometry
   choices are an adaptation, not the paper's site geometry. No protected
   elastic Joss base is imported. Constructed centre/domain geometry must be
   inspected rather than inferred from nominal area.
3. Stable drained ELASTOPLASTIC gravity initialization with properly masked
   free-DOF force and energy convergence. A fixed update count or elastic-only
   stress release is insufficient. Preserve failure if equilibrium cannot be
   reached; do not increase strength or erase stresses to force preparation.
4. Explicit all-particle undrained transfer preserving position/F/stress and
   recorded history, with rebuilt elastic compliance and cached state after
   E/nu change. Preserve native accumulated kappa; use a recorded origin for
   the new undrained degradation mechanism. Transfer needs its own frozen
   native ownership/rollback/current-J controls before a slope launch.
5. Bounded native/CSV/VTK smoke, then one fresh initial-state full run targeting
  60s dynamic time after preparation, mass1, dtScale.2,12h wall budget (not ETA).
   Freeze case, protocol, postprocessors, source/DLL before launch. Runout,
   positiveJ/mass/finite fields/strength-D identity/coherent motion need actual
   review. Show actual D_s with a fixed0–1 scale and actual metre coordinates.

Current state27October: owned optional material committed961c17a8 and transfer
controls checkpoint946dbce7. FIRST point controls exit0/PASS5groups with84pure
projectorentries,3nativeconstitutiveattempts/2accepted (one expected preflight
rejection),0MPM. The deterministic table has26segments; certified maximum
chord error81.900697Pa, sampled error75.428741Pa within101.25Pa budget.
FIRST transfer controls exit0/PASS4groups,6nativeattempts/6accepted,0MPM.
They cover current-J full compliance, preserved nonzero history/origin,
dt0 material release, late-candidate failure, ownership/caches/reset and stale
batch rejection. New particles are prepared off-simulation and committed with
one order-preserving vector swap; original objects survive any failure.
The material switch and genuine native zero-time return have separate energy
proxies; this is not a closed energy balance. Nodecheck/36tests also pass.
Owned recipe/smoke/full60s remain NOT_RUN. No full solver active. Do not claim
that preceding Joss native controls test this MC model.
Do not repeat completed oldMC/Joss gates, solver/replay/research/rendering.
No automatic geometry/strength/beta/psi/tolerance changes to force collapse.
