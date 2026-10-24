---
title: Wang2017 native Soil2 integration
type: synthesis
tags: [wang2017, soil2, native-windows, constitutive-integration]
sources: [docs/benchmarks/WANG2017_SOIL2_NATIVE_PLAN.md, tests/materials/wang2017-native.lisp, docs/testing.md]
updated: 2026-10-24
---

# Wang2017 native Soil2 integration

The human objective is an actual landslide, following the negative Soil1 control
in [[wang2017-fast-trial-2026-10-24]]. New branch
`codex/wang2017-soil2-landslide` preserves that evidence and all original models.

The optional native adapter uses the coupled signed-tensor point projector from
[[wang2017-paper-history]], with paper c30→15kPa overkps0→.02,phi35/psi0,
E20MPa,nu.25,gamma20kN/m3. Its finite-strain MPM adaptation rotates committed Ep
with the proper polar rotation of the same incremental deformation gradient as
the elastic trial, then adds the current-frame plastic increment. This is an
explicit corotated accumulator, not an exact log(Fp) or uniquely specified Wang
finite-strain law. Native summedJ2 stays separate from paperkps.

Signed-history decrease beyond1e-13 is rejected, not clamped to a hidden maximum
or accepted as healing. Such a path can have positive plastic work; rejection
identifies unsupported history scope rather than invalid physical loading.
Multiple admissible roots also remain rejected. No apex, strength or dilation
shortcut is enabled to produce a collapse.

Actual Windows frozen003:18PASS,28constitutive calls, zero MPM updates;
271source hashes and mapped copiedDLL verified. Earlier001 bootstrap and002
final-proof harness failures remain retained. Root MC34/framework10/input3
groups pass separately using workspace sources; Node check/36tests pass.
Frozen output002 additionally passes8groups with2 genuine USF updates,25MPs,
2 observed VTKs and50material/4contact CSV rows. Full F becomes nonidentity;
CSV detF/paper-invariant residuals0 and surface identity residual8.33e-17m.
Output is read-only and oldSoil1 creates no additional files. Initial001 retained
6PASS/1FAIL/1NOT_RUN due to missing Soil1 test-fixture metadata;002 fixes only
the fixture and observed-count reporting. This elastic, unequilibrated miniature
is an integration check, not a plastic-flow or landslide benchmark.

The first paired experiment keeps0.01m/s to60mm/6s, mesh/contact/BC/material
elasticity and gravity policy from Soil1. Soil2 gravity history must not be
reset. F9/J/Ep6/cohesion and contact geometry/spring energy are saved to make
the physical outcome auditable. Colour, forced settlement or a speed outlier
alone is not landslide evidence. Rate100x, assumed10m height, local softening
mesh dependence and unverified reference curve remain limitations.

[[wang2017-apex-and-rate-study]] retains earlier apex and interrupted-rate
evidence. [[reusable-simulation-framework]] owns the compatible integration.
