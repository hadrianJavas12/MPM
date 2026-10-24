---
title: Unnotched landslide method selection
type: synthesis
tags: [mpm, landslide, unnotched, literature, strength-reduction]
sources: [raw/unnotched-landslide-request-2026-10-24.md, docs/benchmarks/UNNOTCHED_LANDSLIDE_METHOD_SELECTION.md]
updated: 2026-10-24
---

# Unnotched landslide method selection

The human authorizes broader journal methods to obtain actual landslide without
a notch. [[wang2017-residual-history-scope]] remains a tested repair with no
verified coherent slope failure, not a reason to keep changing its endpoint.

Primary studies distinguish different mechanisms: Wang/Hicks/Vardon2016 uses
self-weight and Von Mises softening in an initially unstable intact clay slope;
Yu/Kasama2024 uses DP and separately studies SSR and unstable runout;
Xie/Navas/López-Querol2023 supplies a direct MC-MPM strength-reduction bridge;
Remmerswaal/Vardon/Hicks2025 informs gravity/crest-load triggering in3D.
Their laws, histories, geometries and triggers are not interchangeable.

The first selected control is a separate gravity-only MC scenario with independent
SRF1 and1.40 trials. Reduction of c and tan(phi) is explicit; this is a strength
reduction study, not natural creep or spontaneous failure of unchanged soil.
No notch or Wang actuator belongs in the recipe. Current native MC can be reused
without a new softening coordinate. Exact source polygon and explicit gravity
schedule still need to be frozen; Figure7 geometry was not visually verified,
so an adapted polygon must be named as an adaptation.

See the full decision and source matrix in
`docs/benchmarks/UNNOTCHED_LANDSLIDE_METHOD_SELECTION.md` and linked research
notes. No new full solver, material calls, Node tests or old gate repetitions
were performed for the literature checkpoint. Real coherent free-mass motion,
toe crossing and consistent native fields are required; neither a coloured
movie nor solver completion proves landslide or scientific validation.

Implementation should reuse [[cl-mpm-architecture]] component ownership and
[[windows-port]] source-freezing/runtime evidence. Follow-on material-driven
retrogression needs its own constitutive mapping and regularisation study.
