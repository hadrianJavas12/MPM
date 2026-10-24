---
title: Wang2017 completed apex60mm review and endpoint study
type: synthesis
tags: [wang2017, soil2, apex-flow, saved-data-review]
sources: [docs/benchmarks/WANG2017_APEX_TRIAL.md, docs/testing.md, research/references/wang2017/mpm-reference-contract.json]
updated: 2026-10-24
---

# Wang2017 completed apex60mm review and endpoint study

The subsequent100mm experiment failed the history-scope guard after last saved
9s/90mm. [[wang2017-residual-history-scope]] retains the actual replay, partial
physical result and a separate tested residual-only policy; no coherent
landslide or successful10s run is claimed.

[[wang2017-apex-flow]] source55bc85d completed native0 at13:33:43WIB,
audit/render/worker0 at13:34:44.61states/915IDs/20640updates reach6s60mm.
Actual-output audit confirms55815material/366contact rows and mass/finite/F/J/
tensor/cohesion/contact identities. This is numerical consistency, not a
verified landslide or paper validation.

Apex flow genuinely occurs at sampled ID627 near the free face from5.8s;
accumulated volumetric plastic strain reaches0.000728068207, consistent with Ep
trace to8.32e-15. Current-minus-committed trial increment is0 after saved commit,
so cumulative differences are needed to observe its evolution. Sampled flags
do not count every internal event; volume strain is not porosity or det(Fp).

Maximum paperkps.017506169, minimum cohesion16.870373kPa exceeds15kPa residual.
Reaction rises on every saved interval to642.2968kN/m.509free above-base MPs,
excluding6driven, move centroid+2.106mmX/−18.521mmY; none crosses the original
toe. The fastest particle moves upward. No coherent failure/run-out verified.
58strict-prefix snapshots match before sampled apex activation. Against Soil1,
final reaction−3.9392%, max displacement difference3.28313mm, not convergence.

Completed evidence24hashes/361archive members,275 frozen sourcefiles and actual
DLL verified; review19hashes includes exact scripts/results/source hashes and
next-study review. Video61actual states/4fps/15.25s playback/scale1, full decode0.
Root inspected actual overview/energy/physical figures and retained primary
pages179/180. Figure3 axis0–0.10m and approximate600kN plateau from.05m are
visually verified for Soil1; Soil2 endpoint remains unknown.

Next bounded study: same material/rate/numerics,100mm/10s. Native zero-update
input3 groups pass; only travel,derivedduration,frames change.101frames keep
nominal.1s cadence but actual prefix still needs fixed-tolerance comparison.
Runtime estimate~142min from85m11s measured;3h budget. No VTK restart assumed.
The endpoint is a declared comparison, not a Soil2 paper datum or collapse
guarantee. It tests whether60mm ended before global peak/residual response.
If still pre-peak, resolve source geometry/rate/mesh rather than extend forever.
A hold would test relaxation/inertia; bilateral strip can restrain motion and
exchange spring energy. It is not natural creep/free runout.

The100mm experiment started13:52:42WIB on3caa6be in apex-100mm-001,3h budget
until16:52:42. Worker31296/wrapper38252/cmd25892/SBCL27304 Session11, initial
native RUNNING, same quiet15min monitor. Runtime source/DLL proof was not yet
ready at the single initial capture check; no verified launch packet claimed.
No10s completion or landslide result is established by this launch.
Later14:08WIB authorized capture verifies275 frozen sources/DLL/postprocessors/
process chain,6artifact hashes/292ZIPmembers. Captured RUNNING/complete=false
only, initial unavailable-proof history preserved, no active-data/tests rerun.

See [[wang2017-soil2-native]], [[wang2017-soil2-return-failure]] and
[[wang2017-fast-trial-2026-10-24]] for retained strict/Soil1 controls.
