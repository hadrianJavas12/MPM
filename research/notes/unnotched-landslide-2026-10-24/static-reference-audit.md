# Static-reference and geometry audit

25 October 2026. Primary-source browsing and mathematical review only; no static
factor, projector, test or solver was calculated/executed for this audit.

## Geometry: what is established

[Griffiths–Lane1999](https://doi.org/10.1680/geot.1999.49.3.387), Example1,
p391/Figure1, is a dry homogeneous slope without foundation(D=1). Its indexed
[author PDF](https://inside.mines.edu/~vgriffit/pubs/All_J_Pubs/41.pdf) identifies
crest1.2H, face projection2H, angle26.57°, phi20°, c/(gamma H)=0.05,
left rollers and fixed base. The live legacy author links redirect to the
author homepage; **a fresh visual figure inspection was not obtained**.

[Xie2023](https://doi.org/10.1002/nag.3599), Section3.2, confirms H10m,
angle26.57°, the same strength ratio, side rollers/base fixed, independent
SRFs and the reported1.35–1.40 critical bracket(reference LEM1.38). Its text
describes a foundation and21,540 MPs at36 MPs per1m² patch. **Figure7's complete
polygon remains visually unverified**, and these counts do not establish its
dimensions. Do not equate that problem with the220m² D1 adaptation. Material
values E100MPa,nu0.3,gamma20kN/m³,c10kPa,phi20°,psi0 come from the prior
Table1 audit; this wakeup did not freshly render that table.

Our known polygon `(0,0),(32,0),(12,10),(0,10)` is therefore a named
D1-inspired adaptation. The dimensional choices H10m and gamma20kN/m³ give
c10kPa from the verified ratio, but do not establish exact reproduction.
The literature bracket is a comparison target, not a proven critical SRF
for our explicit model or a reason to change its strength until it moves.

## Dry simplified Bishop equation

The publisher page for [Bishop1955](https://doi.org/10.1680/geot.1955.5.1.7)
returned403. The authoritative official [USACE EM1110-2-1902](https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1902.pdf?ver=2014-05-07-083439-823)
is indexed: AppendixC§C-3, equationsC-15/C-16 and AppendixF(F-1).
For zero pore pressure/surface loads, its equation reduces to

```
m_i(F) = cos(alpha_i) + sin(alpha_i)*tan(phi_i)/F
F = sum((c_i*b_i + W_i*tan(phi_i))/m_i(F)) / sum(W_i*sin(alpha_i))
```

It assumes circular slip, horizontal interslice forces, vertical slice-force
equilibrium and overall moment equilibrium; it does not enforce all horizontal
force equilibrium. W is slice weight per unit thickness, b horizontal width.
FigureF-2's indexed sign description makes alpha positive for a base descending
toward the right. No direct PDF screenshot was obtained; the indexed official
equations and text, rather than an unofficial transcription, support this audit.

**USACE TableC-2 explicitly warns of potentially unreasonable/negative base
normal forces(§C-10.b/c).** Negative values must be reported, not silently
clamped or hidden behind a convergence flag. No tension-crack rule is adopted.

## Independent implementation review: no result asserted

For x-right/y-up lower arc `y=yc-sqrt(R²-(x-xc)²)`, use
`sin(alpha)=(xc-x)/R`, `cos(alpha)=sqrt(R²-(x-xc)²)/R`.
Dry vertical equilibrium gives
`N_i=(W_i-c_i*b_i*tan(alpha_i)/F)/m_i`.
At a cohesive crest entry, first-slice weight is O(b²), while the cohesion
term is O(b). Consequently negative entry normals can persist/refine in the
formal Bishop calculation. Rejecting every such circle can eliminate the
whole search family. Root's revised policy—retain formal F plus raw negative-N
counts/minima and no physical-admissibility PASS—is appropriate for a limited
diagnostic. It is not a tension-crack or no-tension soil calculation.

The preregistered family is crest entryx[0,12], face exitx[12.5,32],
`C=midpoint+rho*(-dy,dx)`, `R=chordLength*sqrt(.25+rho²)`,
rho[.25,4]. Counts9×17×13(coarse) and17×33×25(fine);200/400 slices,
plus400 slices on the same coarse family to isolate slice refinement.
These bounds are our diagnostic convention, not paper geometry/search data.

Require the center above both endpoints, a real lower arc within soil/above
the base, positive weights/driving moment/m_i and an isolated converged
positive F. Check the exact arc minimum at `clip(xc,entry,exit)` and ground
breakpointx12, not only slice midpoints. Preserve rejected-circle reasons and
boundary minima. A bounded circular family cannot certify a global FoS.

For a fixed circle, simultaneous `c→c/S` and `tan(phi)→tan(phi)/S` implies
`F→F/S`; substitution leaves m_i and N_i unchanged. This is a useful independent
scaling check. A static result still does not validate MPM locking, finite-strain
flow, initialization, dynamic landslide or runout. **Static result NOT_RUN.**
