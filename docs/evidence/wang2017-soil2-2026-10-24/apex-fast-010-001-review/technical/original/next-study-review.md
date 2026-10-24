# Wang2017: next physical study review

Date: 2026-10-24, Asia/Jakarta. Read-only audit; no code, controls or solver run.

## What the reference establishes

[Wang et al.,2017](https://doi.org/10.1007/s11629-016-3951-1), Section2,
printed pp.179â€“182, uses gravity initialization followed by crest descent at
1e-4m/s. Soil1/Figure3 is perfect plastic; Soil2/Figures4â€“5 softens cohesion.
The author text describes the Soil2 local-arc-length reaction approaching zero
and progressive shear-band development. These figures do not establish a
large-runout time history. [Author-upload source](https://www.researchgate.net/profile/Qiguo-Rong/publication/312201146_Stability_analysis_of_slope_in_strain-softening_soils_using_local_arc-length_solution_scheme/links/59cdde08aca272b0ec164432/Stability-analysis-of-slope-in-strain-softening-soils-using-local-arc-length-solution-scheme.pdf).

The retained page-179 render shows width20m, crest7+3m, base5m and angle60deg,
with no numerical relief height. The retained page-180 render visibly confirms
Figure3's horizontal axis0â€“0.10m; its curves end around0.085â€“0.09m. This is an
approximate visual reading, not a digitized endpoint. The Figure4/5 numeric
endpoint and their stage labels remain unverified. The separate excavation
case in Section3 is not the first homogeneous-slope example.

## Existing evidence and comparison boundary

Local primary-derived artifacts inspected:
`output/paper-3951-2026-10-22/{paper.txt,page-05.png,page-06.png}`.
Exact byte counts and SHA256 hashes for those unchanged source artifacts are
retained in [source-proof.json](source-proof.json). Figure3 visually plateaus
near600kN from about0.05m; these approximate readings are not digitized data.
The original PDF path is still absent. Web text retrieval succeeded; Figure4
screenshot/author-image requests failed. No blocked-PDF download was retried
or bypassed. Geometry cannot be uniquely reconstructed from the labelled
lengths without an additional relief/toe-location input;10m remains an
assumption, not a measured source dimension.

The current completed manifest reports6s, command60mm, measured59.5539606mm,
reaction642.296777kN/m,61frames, zero mass error and finite fields. This is the
current opt-in composite-apex model at0.01m/s,100 times the reference rate.
It is not a quantitatively comparable paper result: relief/fixity/penalty/grid,
MPM versus equilibrium FEM, loading rate, and the declared extra apex mode are
still differences. No CSV trend analysis is duplicated here; that review is
owned separately. Root's viewport finding of no coherent collapse is retained.

## Gated recommendation: loading extension before a hold

If the independent raw-output audit finds no invalid state, a bounded next
study should retain exactly the current material, strength curve, apex policy,
geometry, rate0.01m/s, grid, timestep, damping and penalty, while extending the
command endpoint to0.10m (10s total). This is the existing comparison target,
now visibly within the Figure3 axis, NOT a newly verified Soil2 failure
endpoint. It isolates whether60mm simply ended before this model's peak and
post-peak response; it does not guarantee failure. Preserve0â€“60mm at the same
output cadence and compare the common displacement prefix before interpreting
any later change. Do not alter strength, dilation, history, mass or rate to
manufacture a collapse. A fresh10s run is required unless a true full-state
restart has independently been verified; raw VTK is not such a restart.

Before launch, confirm the current audit and constitutive gates, keep frozen
sources, declare a wall budget from the actual6s runtime, and retain negative
outcomes. Assess raw signed reaction versus MEASURED descent, spatially
connected localization, ID-aligned mass motion/velocity, volume/mass/finite
state and actuator tracking. Increasing local kps alone is not landslide proof.

A stationary-command hold is a later, separate diagnostic if post-peak
localization/motion develops. It is not the source protocol; a bilateral strip
can restrain sliding and exchange spring energy even when command work stops.
The monotonic-history guard may reject relaxation; preserve such a rejection
rather than introduce healing or max-history silently. Autonomous runout would
need a separately declared release/contact protocol and boundary/domain review.
If0.10m remains pre-peak, report that result and resolve source geometry plus
rate/mesh sensitivity before choosing another endpoint. Do not extend endlessly
or present an animated displaced shape as a verified gravity-driven landslide.
