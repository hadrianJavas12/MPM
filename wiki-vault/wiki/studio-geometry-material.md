---
title: Studio geometry and material controls
type: concept
tags: [studio, geometry, material, units]
sources: [studio/GEOMETRY.md, studio/MATERIAL.md, studio/schema.json]
updated: 2026-10-14
---

# Studio geometry and material controls

[[cl-mpm-studio]] configures cliff height/aspect/slope/overhang and toe notches.
Rectangle is the legacy default; ellipse and triangle are selectable. Triangle
tip fraction changes tip height; zero notch height disables clipping and zero
depth uses the legacy automatic rule. The sampled SVG is a preview, not a solver
result; compare actual VTK material points at the chosen mesh resolution.

`soilBoundary` is a geometric base thickness. It does not create a separately
modelled soil material; the current scenario fills it with chalk particles.
`undercut` is face overhang, not an individual notch angle.

The existing chalk law has controls for E/nu, density, friction, cohesion,
dilatancy, nonlocal length, damage onset/delay, ductility and plasticity/damage
flags. UI GPa/kPa values convert explicitly to API/export Pa. Schema defaults
remain the legacy values. Elastic Gravity Settle disables plasticity/damage
without switching the built-in particle class. Damage selection reaches both
simulation and particle flags.

Custom stress law: [[studio-custom-models]]. Scientific and testing scope:
[[studio-verification-2026-10-14]].
