# Completed unnotched numerical sliding example

26 October 2026. Branch `codex/unnotched-mc-composite-apex`, native source
`139005c28ff579fe7cbce410f8e07917ec6cf17c`.

**The completed h0.5 simulation shows numerical onset of coherent downslope
sliding without a notch.** The upper wedge moves above a localized plastic
band at actual scale. Both frozen physical-metre motion windows pass and the
saved-state integrity checks pass. This delivers the requested simulated slide
within the declared adapted experiment; it is **resolution-sensitive onset,
not validated physical failure**. No toe runout is detected.

## Actual run and media

`output/mc-composite-apex-2026-10-26/srf1p6-composite-h05-002` starts13:54WIB
and completes at16:09WIB: native/worker0,6physical seconds,61saved states,
3520particles and15470updates. The FIRST prepared variant audit/render exits0;
61VTKs/214720material rows,288frozen source files and stored mapped DLL agree.
IDs/count/mass/finite fields/F/J/volume/law/yield and cumulative plastic work/
volume checks pass. No sampled centre exits/floor penetrations occur.

[Actual video](../evidence/mc-composite-apex-2026-10-26/srf1p6-composite-h05-002-completed/saved-analysis/variant-review-001/gravity-slope-actual.mp4)
contains61actual states at4fps:15.25s playback for6physical seconds, scale1,
no interpolation, full decode0.
[Actual scale1 summary](../evidence/mc-composite-apex-2026-10-26/srf1p6-composite-h05-002-completed/saved-analysis/variant-review-001/gravity-slope-review.png)
was visually inspected by root. Plastic-history colour is not damage.

## Mesh and the apparent crack origin: human follow-up

A new descriptive saved-data query, without another solver/audit/render, finds
the first saved nonzero plastic history at frame7/t0.7s (previous saved0.6s).
There are711particles with positive kappa, spanning y0.124948–3.623775m; maximum
kappa2.134099342238181e-5 is near(x7.125013,y0.374846)m. Thus early saved
plasticity already occurs in the lower body. This is not an exact substep
initiation time, unique nucleation point or a modeled crack. The
[transcribed numerical output](../../research/notes/unnotched-landslide-2026-10-24/saved-plasticity-onset-002.json)
records the query scope and method honestly after execution.

The video uses a fixed full-run kappa colour scale (maximum about0.966), so
this early signal is almost invisible. Current perfect MC keeps c/phi constant
during the run; kappa is plastic history, not damage or crack opening. Finer
mesh alone cannot introduce a fracture/damage law. h1 versus h0.5 changes the
qualitative response, so adequacy/convergence of h0.5 remains unestablished.

The [accepted older Joss pilot](../JOSS_DAMAGE_DIAGNOSIS_2026-10-15.md) instead
shows actual damage0–1, first saved at4s on the lower cliff face near
(13.125,3.625)m; the protected base remains undamaged. The
[legacy Urmi renderer](URMI_LEGACY_COMPARISON.md) shows kappa/friction evolution,
not that Joss damage field. Different laws/geometry/preparation preclude
attributing differing band paths solely to mesh or colour. No new simulation,
monitor or parameter change is authorized by this explanatory query.

## Criteria fixed before results

The full CSV-only pair comparison exits0 using unchanged
[physical criteria](../../research/references/unnotched-mc-ssr/composite-apex-refinement-contract.json):
initial cohort x>2m/y>2m, adjacency1.01m, dx≥0.25m and downslope displacement≥0.5m,
connected mass≥10%of cohort, positive dx≥75%of component mass, and the same
component's mean vx>0.001m/s at every saved state in a≥1s interval. Hold
displacement is relative to the actual saved2s state. No interpolation or
cross-mesh particle-ID matching is used; all61matched times agree exactly.

| Observation | Whole window | After gravity ramp |
| --- | ---: | ---: |
| First motion detection, s |3.4|3.5|
| Connected particles at detection |626|427|
| Component fraction of physical cohort |27.1701%|18.5330%|
| Median component dx, m |0.501706|0.479058|
| Median component downslope displacement, m |0.534946|0.516897|
| Component positive-dx mass |100%|100%|

The fixed hold component passes over saved2–3s:11states, minimum mean vx
0.187362m/s. The whole-window persistence interval is0.8–1.8s and includes the
ramp; it is reported separately. Neither interval certifies every unsaved
substep, all6s continuously, or future acceleration.

At6s the fixed physical cohort's centroid displacement is(+0.505536,-0.248127)m
and mean velocity(+0.041278,-0.018292)m/s. Maximum particle displacement is
1.498551m, but this extremum is not the acceptance criterion. Final KE874.692J/m
is below its earlier peak: no continuing acceleration is claimed.

The same-factor h1 control is negative in both motion windows. The different
response therefore establishes sensitivity to coupled space/time/sampling,
**not mesh convergence**. Toe runout is explicitly a separate frozen measure;
both runs have0mass beyond x32.5m. It is not a post hoc prerequisite for the
initial sliding result. Automatic reviewer flags remain unpromoted/false;
the separate `root-numerical-onset-acceptance.json` binds this manual spatial
decision to the immutable full audit and pair hashes. Scientific validation
remains false.

## Model and limits

This is a gravity/SSR adaptation: reference c10kPa/phi20degrees deliberately
reduced by1.6 to c6250Pa/phi atan(tan20degrees/1.6), regular psi0, E100MPa,
nu0.3,gamma20kN/m3. The optional composite model adds declared g_A=p plastic
volume at the hydrostatic apex. The unnotched adapted polygon is
(0,0)(32,0)(12,10)(0,10), fixed bottom, grid0.5m,2particles per cell axis,
USF/FLIP, dtScale0.2, gravity ramp0–2s/hold2–6s, no damping/mass scaling/Fbar.
There is no driver, weak seed, elastic-only initialization/release or reset.

This is not unchanged-soil creep, an exact Wang/Urmi/Xie reproduction, calibrated
field prediction or quantitative FoS/runout validation. Fixed-base/adapted
foundation and extra apex-flow assumptions remain. Minimum particle-domain
margin is-1.20943micrometres; centre tests do not certify kernel containment.
No closed energy balance or mesh convergence is inferred. The finite study
ends here; no automatic h0.25/SRF/duration/strength/psi/tolerance escalation.

The[completion packet](../evidence/mc-composite-apex-2026-10-26/srf1p6-composite-h05-002-completed/README.md)
retains77indexed artifacts,2ZIPs/497decoded members and288actual source files.
Root independently verifies all78Git blobs, full original/archive sources and
indexed PNG/MP4/manual acceptance bytes. Original source/runtime/raw/caller/
prelaunch/analysis records remain intact; the old launch ZIP is referenced,
not duplicated. Result checkpoint1922fb8a is pushed; the obsolete run monitor
is deleted after completing the simulation and review. The earlier failed001,
synthetic diagnosis and four repair gates
remain in their original packets. The[repair](COMPOSITE_APEX_ROUNDOFF_REPAIR.md)
uses equivalent symmetric principal differences with unchanged physical law,
branch/mean/q/checks/tolerances plus owned failure capture. Missing old trial
inputs stay unavailable; successful002 does not retroactively prove their cause.
