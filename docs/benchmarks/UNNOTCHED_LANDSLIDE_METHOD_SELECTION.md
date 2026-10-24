# Unnotched landslide: literature and method selection

24 October 2026 · Windows native CL-MPM · research/design checkpoint

**Objective:** obtain genuine, coherent slope failure without a toe notch,
excavation or prescribed particle trajectory. The previous Wang2017 trials
have not verified this result. This document selects the next method; it is
not evidence of a newly executed simulation.

## Primary references and their distinct mechanisms

| Reference | How an intact slope fails | Why it matters here | Remaining translation work |
| --- | --- | --- | --- |
| [Wang, Hicks & Vardon (2016), Géotechnique Letters](https://doi.org/10.1680/jgele.16.00019) | An initially unstable 5 m, 45° clay slope fails under self-weight; cohesion softening permits retrogression. | Direct example of the desired unnotched gravity mechanism. | Von Mises surface, plastic-tensor norm and Coulomb base must match. Numerical unit weight was not found in the inspected paper; do not invent it as a reported value. |
| [Yu & Kasama (2024), Journal of JSCE](https://doi.org/10.2208/journalofjsce.23-15036) | Separate strength-reduction and already unstable runout studies; Drucker–Prager with cohesion softening. | Clear continuous geometry, unit weight, mesh, duration and definitions of moving mass/runout. | DP convention, dilation evolution and smeared-crack regularisation are not a drop-in replacement for native MC. Do not mix parameters from its different substudies. |
| [Xie, Navas & López-Querol (2023), IJNAMG](https://doi.org/10.1002/nag.3599) | Independent Mohr–Coulomb strength-reduction analyses of the classical intact slope. | Closest material fit to the existing tested MC implementation. | Published solver is implicit B-spline MPM with F-bar comparisons. Our explicit formulation, gravity schedule and any geometry assumptions must be declared. |
| [Remmerswaal, Vardon & Hicks (2025), Acta Geotechnica](https://doi.org/10.1007/s11440-025-02542-w) | Gravity release, and crest foundation loading for stable cases, in 3D slopes. | Useful source for explicitly separating stress initialization, trigger and physical motion. | 3D/random-field method and substantially greater computation; not the first economical pilot. |

The original [Griffiths & Lane (1999)](https://doi.org/10.1680/geot.1999.49.3.387)
is the classical SSR reference. SSR deliberately applies
`c_f = c / SRF` and `phi_f = atan(tan(phi) / SRF)`.
It must not be described as unchanged soil spontaneously failing, rainfall or
creep. A reduced friction angle is not `phi / SRF`.

## Decision: first a separate MC gravity/SSR control

Start with the method of the classical MC benchmark and its direct MPM bridge,
rather than changing the unsuccessful Wang2017 material until a movie collapses.
Use independent, predeclared SRF **1.00** and **1.40** trials. The published
classical critical bracket **1.35–1.40** is a comparison target, not a guaranteed
result of our different discretisation or a tolerance to impose on it.
Retain the 1.35 case for a later bracket study. Do not increase SRF after seeing
a stable result without recording a new, justified experiment.

This isolates a missing capability: a reusable gravity-only slope procedure,
with no Wang crest actuator. It also avoids introducing an unverified new DP
or Von Mises softening law at the same time as a new scenario. The subsequent
gravity-softening route remains important for material-driven retrogression;
Wang2016 and Yu2024 guide that separate constitutive/regularisation study.

The Xie Section 3.2 inputs are H=10 m, gamma=20 kN/m³, E=100 MPa, nu=0.3,
c=10 kPa, phi=20°, psi=0°. Each SRF is independent. Its gravity is increased
in implicit load steps; those step counts do **not** prescribe an explicit
physical loading time. Its full Figure 7 polygon has not been visually verified
here. The indexed Griffiths D=1 geometry has a 2H face projection and a 1.2H
rear crest. Until the full chosen polygon is verified, any use of those
dimensions is a **declared reference-inspired adaptation**, not an exact Xie
reproduction. No new full slope run is launched at this research checkpoint.

## Input and implementation gate before running

1. Freeze one complete polygon and empty runout domain, material/stress units,
   SRFs, essential boundary DOFs and gravity schedule. Record each input as
   source fact, derived value or explicit assumption. No notch, weak seed,
   retaining-wall removal or crest actuator is implicit in the recipe.
2. Add a small `gravity-slope` scenario beside the existing scenarios. Reuse
   the material factory, native MC law, clipping, measurements, retained CSV
   and source-freezing CLI. Keep the material under `materials/`, geometry and
   procedure under `scenarios/`, and component assignments under `cases/`.
   No original material/solver/default is changed.
3. Check the reduction formula, correct angle units, unchanged elasticity and
   density, geometry/mass, free surface, basal/side DOFs, and absence of any
   actuator in a zero-update native gate. Add only tests for new behavior.
4. Verify actual bounded MPM updates and complete per-ID VTK/CSV diagnostics.
   Explicit plastic gravity initialization must not silently be replaced by an
   overstressed elastic state followed by plastic release. Conversely, an
   intentionally released state requires a separate declared experiment.
5. Measure a pilot's wall time and native update cost before launching a full
   pair. Never use a paper's implicit timestep as a stable explicit timestep.

## What counts as a useful physical result

Follow the same initially selected, free upper-slope mass by particle ID.
Report coherent downslope motion, centroid descent and speed distribution,
localisation, mass crossing the initial toe and front/runout advance, plus
finite fields, positive J, mass/count conservation and constitutive admissibility.
Separate motion during the gravity ramp from sustained response afterward.
Store stable and unstable results, source snapshots, runtime proof and scale-1
media. A colour change, single velocity outlier, reaction drop, solver exit or
FEM nonconvergence criterion alone is insufficient.

No factor of safety, physical runout, mesh objectivity or paper agreement is
claimed yet. Dynamic damping, grid/PPC, timestep, ramp time, basal constraint
and domain sensitivity need explicit assessment. A stable control may still
settle elastically; it need not have exactly zero displacement.

## Evidence and reading trail

- [MPM softening facts and source locations](../../research/notes/unnotched-landslide-2026-10-24/mpm-softening-primary.md)
- [SSR formulas, classical and direct MPM references](../../research/notes/unnotched-landslide-2026-10-24/strength-reduction-primary.md)
- [Actual engine fit and boundary caveats](../../research/notes/unnotched-landslide-2026-10-24/engine-fit.md)
- [Concrete API/recipe audit and proposed adaptation](../../research/notes/unnotched-landslide-2026-10-24/recipe-implementation-audit.md)
- [Earlier Wang failure and tested residual-only policy](WANG2017_RESIDUAL_HISTORY_SCOPE.md)

The Yu PDF was read locally and its geometry/table pages visually inspected.
SHA256: `d6ae3c22e6e93f86ae832b8f57446aac3721b3d75ac5a56f585afaf8cd306ce5`.
Local read-only source: `tmp/pdfs/unnotched-landslide-2026-10-24/yu-kasama-2024.pdf`;
the full paper is not copied into Git. The journal URL above remains the
retrievable source. Xie publisher/repository text was read; a Figure 7 screenshot
timed out. These retrieval limits are retained rather than filling missing
dimensions by inference. Literature review ran **zero** Node tests, native
constitutive calls or MPM steps; previous numerical gates were not repeated.
