---
title: Clay creep design inputs 2026-10-22
type: source
tags: [creep, clay, user-input, assumed-parameters]
sources: [user-request-2026-10-22]
updated: 2026-10-22
---

# Clay creep design inputs

Immutable intake record. User: "dimodifikasi agar seperti pergerakan creep yang
akan menyebabkan longsor". Earlier user directions require real native physics,
token economy, reproducible evidence, cohesive commits/push and no UI focus.

Engineering choice: a separate experimental total-stress phi_u=0 J2 Perzyna
material with strain-driven softening, constant self-weight and free crest.
This choice is not a claim that the user supplied clay creep laboratory values
or requested a specific constitutive equation. The Wang MC case remains separate.

Assumed demonstration values: E20MPa, nu.25, gamma20kN/m3, peak/residual
Kirchhoff q strengths sqrt(3)*30/6kPa, eta50MPa*s, kappa_s.01; slope relief10m,
width20m, base5m, crest10m,60degrees, grid1m. Strength is not silently Cauchy
strength; nu.25 is compressible and no pore-fluid model is supplied.

Primary conceptual source (reviewed2026-10-22):
https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_mat/rate.html
describes Perzyna overstress plasticity, elastic response below yield and
rate dependence above it. The repository's linear radial variant, parameters
and local strain softening are explicit engineering assumptions, not a
reproduction of that vendor's solver or a published clay calibration.

Controlled experiments and subsequent outcomes belong in synthesis/evidence;
do not edit this intake to turn assumptions into measured or published facts.
