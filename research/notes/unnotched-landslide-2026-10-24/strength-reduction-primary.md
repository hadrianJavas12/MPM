# Primary sources: unnotched slope failure with explicit strength reduction

2026-10-24, Asia/Jakarta. Literature/design audit only; no numerical changes,
tests, material-point calls or solver runs.

## Classical reference

[Griffiths & Lane1999](https://doi.org/10.1680/geot.1999.49.3.387),
Example1/Figures1–4/Table2: homogeneous dry MC slope, inclination26.57deg
(2horizontal:1vertical), c/(gammaH)=0.05, phi20deg, D=1(no foundation layer),
left vertical rollers and fixed base. Indexed Figure1 labels rear crest1.2H
and horizontal slope projection2H. Each factor is an independent analysis:
1.35 converges;1.40 reaches1000iterations with a displacement jump.
[Indexed author PDF](https://inside.mines.edu/~vgriffit/pubs/All_J_Pubs/41.pdf).
Live legacy URLs now redirect to the author's home page; this audit read
indexed primary excerpts, not a freshly downloaded1999 PDF. Figure coordinates
were not independently visually rechecked.

## Direct MPM bridge

[Xie, Navas & Lopez-Querol2023](https://doi.org/10.1002/nag.3599),
Table1/Section3.2/Figures7–10, uses implicit MC B-spline MPM: H10m,
inclination26.57deg, gamma20kN/m3, E100000kPa, nu0.3, phi20deg,
c10kPa, psi0; bottom fixed, side rollers. Independent SRF analyses use
c_f=c/SRF and phi_f=atan(tan(phi)/SRF). It reports the classical critical
bracket1.35–1.40 and comparison value1.38. Locking/stress oscillation affect
post-failure results. [Author-repository PDF](https://researchportal.lsbu.ac.uk/ws/portalfiles/portal/18005867/Num_Anal_Meth_Geomechanics_-_2023_-_Xie_-_An_implicit_locking_free_B_spline_Material_Point_Method_for_large_strain.pdf).
Web full text was available; direct LSBU/UCL downloads returned403. No bypass
was attempted. Figure7's full polygon/foundation dimensions remain unverified;
do not silently identify that geometry with original Example1/D1.

[Jiang et al.2022](https://dzkjtb.cug.edu.cn/cn/article/doi/10.19509/j.cnki.dzkq.2021.0075)
compares MPM strength-reduction criteria against Spencer LEM. In its two
examples, numerical nonconvergence is unsuitable; characteristic-displacement
jumps perform better, while plastic-zone connection or limiting displacement
alone are insufficient. This supports multiple physical observations rather
than transferring a FEM iteration-limit criterion to explicit MPM.

## MC versus DP

Auxiliary mapping source: [Sugai et al.2023](https://onlinelibrary.wiley.com/doi/full/10.1002/nme.7216),
Section4.3.1/Eq36–39. For its Kirchhoff convention,
f=sqrt(J2)+eta*p−xi*c, p=tr(tau)/3,
eta=3tan(phi)/sqrt(9+12tan(phi)^2), xi=3/sqrt(9+12tan(phi)^2),
with dilation mapped separately. Its intended match is a plane-strain collapse
load, not identity of MC/DP surfaces on every stress path. No mapping was
implemented. Keep native MC first; an arbitrary DP model with copied c/phi is
not an equivalent replacement or a permissible silent fallback after rejection.

## Recommended study and claim boundary — our inference

SSR estimates the critical strength ratio/FoS. It deliberately weakens a
numerical material; it does not prove unchanged original field soil naturally
fails or reproduce rainfall/creep. The reference slope is stable at SRF1.

1. Confirm the full chosen source polygon, foundation and boundaries before
   running. Keep empty runout-domain extension separate from initial soil.
2. Use a separate perfect-plastic MC benchmark, no notch or crest driver.
   Predeclare independent trials at SRF1 and published1.40, with1.35 available
   to establish the reference bracket. Reduce c and tan(phi), never phi itself.
   Keep other material/numerical choices explicit and unchanged.
3. Record gravity ramp and equilibrium sensitivity. In explicit MPM, timestep
   exhaustion or exit status is not failure/FoS. Require coherent mass motion,
   measured displacement/velocity, connected localization, finite/J/mass checks
   and sustained motion after the gravity ramp ends.
4. Freeze a declared supercritical factor for a separate dynamic-runout study.
   Initializing full strength then reducing it is a different loading history
   from independent reduced-strength gravity tests; label the difference.

FoS agreement is not calibrated runout. Check grid/particle quadrature, dt,
ramp/damping, locking/noise, basal friction and domain boundaries. Perfect
plasticity does not eliminate localization/resolution sensitivity. Later
softening needs its own regularization/length or fracture-energy study; local
softening alone is not mesh-objective. Changing base/contact/release conditions
changes the study. Retain negative evidence; do not tune strength, surface,
tolerance or rate merely to produce collapse. **Benchmark/runout NOT_RUN.**
