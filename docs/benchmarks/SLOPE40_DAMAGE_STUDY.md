# Requested 40-degree damage slope

26 October 2026, branch `codex/slope40-damage`, from `c2cd4069`.
The human requests a 40-degree slope, actual damage display, a sufficiently
long run, and low token use. The earlier completed MC numerical sliding
experiment and its original outputs remain closed and unchanged.

## Explicit experiment choice

The current perfect MC composite model has no damage variable. This separate
experiment reuses the existing Joss delayed nonlocal damage/chalk material,
including its DP damage-driving stress and protected elastic foundation.
The material choice was presented to the human; pending other preference,
the existing damage model is the stated working assumption. This is a material
change, not a new name for plastic history, and is not a Wang or soil-MC
reproduction. No parameters will be tuned merely to force collapse.

Planned geometry: straight face 40 degrees from horizontal, relief 10m,
crest 12m, horizontal face run 10/tan(40deg)=11.9175359259421m,
toe x23.9175359259421m, foundation 1m, total horizontal domain 60m,
upper vertical face 0m and notch depth 0m. Grid h0.5m, 2 MPs per cell axis,
one worker. Actual sampled particle domains/counts will be measured by the
native gate; boundary clipping/refinement means they are not inferred solely
from nominal h/2.

Use the existing accepted Joss material values unchanged: density1700kg/m3,
E1GPa, nu0.24, fracture energy4.8J/m2, nonlocal length0.5m,
damage cohesion26kPa/friction50deg, derived initiation18926.452Pa,
derived ductility53.599755, delay10s/exponent2. Plastic cohesion1.9656MPa,
friction50deg, dilation0; residual ratios1/0/0.51. These are inherited chalk
assumptions, not calibrated slope40 soil properties.

## Bounded execution and evidence

Planned full target 60s of the existing staged runner clock, maximum1500saved
steps, 12h wall budget. This is longer than the earlier 6s MC experiment.
The inherited Joss accelerate/collapse stages use mass scale10000/1 and
return-to-accelerate velocity/work resets. Therefore this clock is not an
unchanged-mass natural creep history or a calibrated physical failure time.
Initialization requires elastic equilibrium with damage/plasticity disabled;
damage is then enabled above the tagged foundation. The 10s constitutive
delay parameter does not prescribe damage onset or promise collapse.

Before the long run: a FIRST focused native gate checks actual 40-degree
geometry/no notch, effective native material values, genuine damage fields,
initial/protected-base zero damage, finite positive particle state and native
updates. Then a fresh bounded 4s smoke checks equilibrium/activation and saved
VTK damage. Failed preparation must prevent the full launch. Do not repeat old
MC/Joss tests, solvers or renderings; repair only a demonstrated new failure.

An optional owned scenario adapter handles exactly40deg without changing the
Studio schema, UI, original Joss adapter or engine defaults: the public Joss
schema otherwise raises an input40deg to45deg. The effective native40deg must
be tested explicitly. Both geometry and constitutive model are declared
changes from the previous MC run.

Use the existing frozen-source native CLI, a dedicated Joss metadata-aware
wrapper, fresh outputs, source/DLL/caller/process identities and CSV-based
quiet progress. Joss completion is native exit0 plus reference-metadata
complete/termination/target clock, not an invented gravity manifest. Native,
wall-budget, equilibrium, postprocessing and media failures stay distinct.

Render actual saved native damage with a fixed [0,1] scale, actual coordinates
and no missing-field-to-zero fallback; retain initial geometry, timestamps,
all particles and raw VTK. Review finite state, mass, positive volume, damage
bounds, foundation protection and observed movement. Damage is not a measured
crack opening, and neither a red band nor a long native completion proves
landslide or scientific validation. Stable/no-damage results are retained.

FIRST native controls on sourcef3f0e141 PASS/exit0: three new groups,
4168particles/960protected-base particles, exactly2native updates/2damage
passes,8336accepted material calls/6416enabled native damage calls. Actual
40-degree/no-notch geometry, inherited effective parameters, positive finite
state/F/J, base protection and real native VTK damage fields pass. Tiny-gate
maximum damage0 is not onset or equilibrium evidence. Root verifies291frozen
files and the stored mapped DLL. The
[control packet](../evidence/slope40-damage-2026-10-26/controls-001/index.json)
retains actual sources/runtime/results/commands. Required Node baseline check
and36tests also pass; these do not validate damage physics. New wrappers pass
PowerShell parsing; reviewer passes Python syntax compilation only. The full
saved-data workflow is NOT_RUN until actual smoke output exists.

Next is a fresh4s smoke through the unchanged strict equilibrium/activation
path. Full60s remains NOT_RUN until that actual smoke succeeds. No automatic
strength/angle/mesh/time escalation after this requested experiment.
