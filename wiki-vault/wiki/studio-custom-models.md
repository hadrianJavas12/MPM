---
title: Studio custom constitutive models
type: concept
tags: [studio, constitutive, common-lisp, clos]
sources: ["[[studio-hardening-2026-10-14]]", "[[studio-verification-2026-10-14]]", studio/CUSTOM_MODELS.md, studio/lisp/custom-model.lisp]
updated: 2026-10-14
---

# Studio custom constitutive models

[[cl-mpm-studio]] imports/edits/exports trusted `.lisp` source. Custom particles
use `cl-mpm-studio::studio-custom-chalk`, extending the existing chalk class.
The author defines a primary `cl-mpm/particle:constitutive-model` method with
arguments `((mp studio-custom-chalk) strain dt)`. Delegate calls the unchanged
chalk method. Stress updates and independent damage evolution are separate APIs.

The shared loader clears stale/partially installed primary methods and requires
a new exact primary method. Scenario construction checks it too. A custom-only
around method rejects incorrect stress matrix dimensions/types and non-finite
values before core copies. This checks the interface, not numerical accuracy.

The elastic template uses elastic trial Hencky strain, refreshes undamaged and
Kirchhoff stress, and lets the engine convert to Cauchy stress. It requires both
plasticity/damage off and zero initial damage; template selection disables them.

`custom-model.lisp` exports editor text. `simulation.lisp` exports all schema
settings through shared normalization and uses the same loader for the adjacent
model. Both need the installed CL-MPM/Quicklisp environment. They are not standalone.

Execution remains disabled by default. It requires local loopback binding,
`STUDIO_ALLOW_CUSTOM_LISP=1`, allowed Host/origin, JSON, affirmative per-run
confirmation and ≤32 KiB source without NUL. Lisp has unrestricted local user
permissions; this is not a sandbox.

Native Windows delegate smoke passed with zero position/stress differences
from built-in and actual CLOS calls. A browser delegate run with damage/plasticity
on completed three frames. Its unchanged downloaded script from a spaced path
matched all 28 settings, exact custom source and all seven VTK/PNG outputs byte
for byte. These short checks establish integration and reproduction for that
delegate case. Arbitrary laws, the custom elastic template under the full engine,
calibration and long-run/convergence tests remain open.

Evidence and remaining gates: [[studio-verification-2026-10-14]].
Geometry/material conventions: [[studio-geometry-material]].
