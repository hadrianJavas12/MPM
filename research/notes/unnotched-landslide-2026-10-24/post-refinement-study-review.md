# After the same-strength refinement: finite SSR response study

25 October 2026, Asia/Jakarta. The h0.5 run on native source1a9f29a completes
6 s with61 saved states and valid native integrity. Its first frozen review
and render exit0; both physical-metre windows remain NOT_DETECTED. Root has
inspected the actual scale1 geometry and comparison plots.

The fine common-cohort centroid advances2.363mm during the2–6s hold versus
0.196mm on h1. However, kinetic energy falls from27.440J/m at2s to0.0738J/m
at6s, and the terminal common-cohort horizontal mean velocity is approximately
zero. Plastic localisation increases, but no coherent moving component or toe
runout is observed. This establishes sensitivity, not mesh convergence or a
reason to assume that a longer movie will become a landslide.

The restricted Bishop diagnostic cannot establish a physical critical factor:
its near-critical minimum includes negative base-normal forces and a slip arc
near the fixed base. The D1-inspired polygon is an explicit adaptation, and
the fixed bottom differs from a validated frictional runout bed. These limits
remain in force; neither the static diagnostic nor native completion validates
the simulated physical problem.

The next study is a **finite, declared SSR response ladder**. Freeze the
[protocol](../../references/unnotched-mc-ssr/response-ladder-contract.json) before
creating/running its cases: screen h1 at1.6, then2.0, stopping at the first
integrity-valid coherent sliding response. Cap the study at2.0. Then confirm
the SAME first positive factor on h0.5; do not increase it for confirmation.
The h1 screen is economical compared with another two-hour resolution run.

The factors1.6 and2.0 are new experimental assumptions, not values verified
from a paper. They deliberately reduce cohesion and friction through the
existing SSR equations; they do not represent spontaneous collapse of unchanged
soil, creep or rainfall. Geometry, constitutive formulation, psi, elasticity,
density, boundaries, ramp,6s duration, solver settings and fixed physical-metre
observer remain unchanged. No notch, weak seed or external driver is added.

This can locate a six-second response transition in the adapted numerical
problem; it cannot establish a geotechnical factor of safety. A constitutive
rejection is not an unstable upper bound. Stop and diagnose on integrity or
material failure, if neither planned factor slides, or if the same positive
factor fails confirmation. No automatic further weakening, longer duration,
root preference, clamp or tolerance change is permitted by this protocol.

Cases, input controls and both screening runs are NOT_RUN at this checkpoint.
Primary method references and their limitations remain in
[the original method audit](strength-reduction-primary.md). No new literature
search or numerical experiment was performed for this design note.
