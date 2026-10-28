---
title: Native Mohr-Coulomb hardening and softening study
type: synthesis
tags: [cl-mpm, mohr-coulomb, research, native-windows, verification, hardening, softening]
sources: [research/README.md, research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md, research/reports/FINAL_HARDENING_SOFTENING_COMPARISON.md, research/comparisons/h_vs_hs_metrics.json, research/triaxial/m4_verification_summary.json, research/cliff/m5_verification_summary.json]
updated: 2026-10-17
---

# Native Mohr-Coulomb hardening and softening study

> [!correction] Material identity28October
> User identifies this residual-soil triaxial dataset as clay. Source PDF
> pages6-7 says residualsoil; earlier "Resende sand" label is unsupported.
> c=0 in the MC-HS idealization does not classify soil as sand. Original
> reference case density2000kg/m3 differs from PDF gamma16.83kN/m3.
> New slope-material selection is recorded; no new slope simulation started.


Milestones **M0 through M6** of the Mohr–Coulomb strain-hardening (**Model H**, `:mc-h`) and
strain-hardening–softening (**Model HS**, `:mc-hs`) comparative study are **100% COMPLETE**
on branch `codex/mc-hardening-softening-study` (branched from `origin/main` at `e6f9abe`
after PR #8 merged the [[cl-mpm-architecture]] Section 2/5 ownership migration).

See [`research/reports/FINAL_HARDENING_SOFTENING_COMPARISON.md`](../../research/reports/FINAL_HARDENING_SOFTENING_COMPARISON.md)
and [`research/comparisons/h_vs_hs_metrics.json`](../../research/comparisons/h_vs_hs_metrics.json)
for complete equations, numerical tables, plots, and side-by-side `.mp4` animations.

## Milestone M2 & M3 — Constitutive Implementation & Point Verification

- Installed dedicated package `cl-mpm/models/mc-evolution` (`particle-mc-evolution`) in
  `materials/models/plastic/mohr-coulomb-evolution/{package,law,projection,particle}.lisp`
  and integrated framework constructors `:mc-h` and `:mc-hs` in [[reusable-simulation-framework]].
- Supports both piecewise-linear tables (`make-evolution-law`) and the combined exponential + linear
  post-peak strain-softening law of Urmi et al. (2024, Eq. 2) (`make-urmi-evolution-law`).
- Multi-surface Koiter return mapping (`project-principal`) handles 1-plane (smooth face),
  2-plane (edge), and 3-plane (apex: `(0 1 4)`, `(1 3 4)`, `(0 3 4)`) active sets with exact
  piecewise-linear breakpoint crossing.
- `tests/materials/mc-evolution-points.lisp`: **34/34 unit assertions PASS**.
- Across all 7 constitutive point pairs (`C-RES-100/200`, `C-RES-URMI-100/200`, `C-ZHAN-50/100`,
  `C-ZHAN-URMI-50`), pre-peak identity holds to $\max |q_H - q_{HS}| \le 1.17 \times 10^{-11}\text{ kPa}$,
  post-peak softening drops deviatoric capacity by **$-69.12\%$** (Resende sand, $\phi: 33.99^\circ \to 16.34^\circ$)
  and **$-52.69\%$** (Zhan cliff soil at $\sigma_3 = 50\text{ kPa}$, $(c,\phi): (7\text{ kPa}, 20^\circ) \to (2\text{ kPa}, 13^\circ)$),
  and 6-plane yield residuals remain $\le 1.16 \times 10^{-10}\text{ Pa}$.

## Milestone M4 — Paired 3D MPM Triaxial Compression (`T-100-H` vs `T-100-HS`)

- Executed with $780$ 3D GIMP particles ($D = 70\text{ mm}, H = 140\text{ mm}, \sigma_3 = 100\text{ kPa}, E = 20\text{ MPa}, \nu = 0.2, c = 0, \psi = 0^\circ$).
- **Pre-peak identity ($\varepsilon_a = 0\% \to 6.00\%$, frames 0..13):** $\max |q_H - q_{HS}| = 5.29 \times 10^{-12}\text{ kPa}$, $\max |\Delta \kappa| = 1.00 \times 10^{-14}$.
- **Peak strength ($\varepsilon_a = 6.52\%$):** $q_{\text{peak},H} = 252.87\text{ kPa}$ vs $q_{\text{peak},HS} = 250.30\text{ kPa}$.
- **Post-peak divergence ($\varepsilon_a = 14.26\%$, frame 29, 2,224 updates):**
  - `T-100-H` (Model H): sustains plateau $q_H = 242.39\text{ kPa}$ (and $226.59\text{ kPa}$ at $\varepsilon_a = 22.0\%$), uniform $\phi = 33.99^\circ$, $\kappa_{\max} = 0.3394$ ($\kappa_{\max}/\kappa_{\text{mean}} = 2.62\times$).
  - `T-100-HS` (Model HS): localizes into a 3D shear band ($\kappa_{\max} = 0.6586$, $\kappa_{\max}/\kappa_{\text{mean}} = 4.20\times$), softens to residual $\phi_{\min} = 16.34^\circ$ ($97.44\%$ softened particles), and drops macroscopic deviatoric stress to **$q_{HS} = 91.31\text{ kPa}$** (**$-62.33\%$ vs Model H**, **$-63.52\%$ vs peak**).
- Artifacts: `research/triaxial/m4_verification_summary.json`, `research/triaxial/plots/m4_triaxial_100kpa_h_vs_hs.png`, `research/triaxial/plots/m4_triaxial_3d_localization_snapshot.png`, and `research/triaxial/videos/triaxial_100kpa_h_vs_hs.mp4`.

## Milestone M5 — Paired 2D MPM Cliff / Slope Collapse (`L-H` vs `L-HS`)

- Executed with $5,667$ 2D GIMP particles using Master Plan Section 2.5 Zhan cliff parameters ($H = 12\text{ m}$, base $4\text{ m}$, slope $72^\circ$, notch $2.5 \times 2.5\text{ m}$, $E = 5.25\text{ MPa}, \nu = 0.2, \rho = 1917.07\text{ kg/m}^3, \psi = 1.0^\circ$) and the Urmi et al. (2024) two-stage MPM landslide protocol ($200$ elastic gravity settling steps with $\alpha = 0.75 c_p / h$ followed by $875$ low-damping dynamic elasto-plastic steps with $\alpha = 0.02 c_p / h$ to $t = 1.93\text{ s}$).
- **Stage-1 & pre-peak identity (frames 0..3, $\kappa_{\max} \le 0.05$):** $\max |\Delta u| = 0.0\text{ m}$, $\max |\Delta \kappa| = 0.0$.
- **Post-peak progressive failure ($t = 1.93\text{ s}$, frame 35):**
  - `L-H` (Model H): shear zone hardens to peak plateau ($c = 7\text{ kPa}, \phi = 20^\circ$), $\kappa_{\max} = 1.7993$, max displacement $|u|_{\max} = 3.7089\text{ m}$, toe runout $3.2254\text{ m}$, crest settlement $3.0225\text{ m}$, final kinetic energy $80.97\text{ kJ}$.
  - `L-HS` (Model HS): shear band degrades to residual ($c_{\min} = 2\text{ kPa}, \phi_{\min} = 13^\circ$, $33.39\%$ softened particles), triggering a secondary retrogressive surge with $\kappa_{\max} = 4.7737$ (**$2.65\times$ Model H**), max displacement **$5.6345\text{ m}$** (**$+51.92\%$**), toe runout **$4.4764\text{ m}$** (**$+38.79\%$**), crest settlement **$3.6408\text{ m}$** (**$+20.46\%$**), peak velocity $5.5939\text{ m/s}$ (**$+52.39\%$**), and final kinetic energy $182.75\text{ kJ}$ (**$2.26\times$**).
- Artifacts: `research/cliff/m5_verification_summary.json`, `research/cliff/plots/m5_cliff_h_vs_hs_dashboard.png`, `research/cliff/plots/m5_cliff_spatial_localization.png`, `research/cliff/videos/3_cliff_2d_hardening_lh.mp4`, `research/cliff/videos/4_cliff_2d_softening_lhs.mp4`, and `research/cliff/videos/cliff_h_vs_hs.mp4`.

### Elongated Urmi-Geometry Long-Duration 2D MPM Cliff Pair (`L-URMI-LONG-H` vs `L-URMI-LONG-HS`)

- Executed over an elongated $102\text{ m} \times 16\text{ m}$ domain ($48\text{ m}$ upper terrace + $54\text{ m}$ runout floor, $H = 12\text{ m}$, base $4\text{ m}$, $15,267$ 2D GIMP particles at $h = 0.5\text{ m}$) for $220$ Stage-1 settling steps + $80\text{ frames} \times 40\text{ substeps} = 3,200\text{ dynamic steps}$ ($t = 9.79\text{ s}$) using Urmi et al. (2024) Eq. (2) exponential–linear softening (`make-urmi-evolution-law`).
- `L-URMI-LONG-H` (Model H): arrests after a single-stage slump by $t \approx 3.5\text{ s}$, with continuum $|u|_{\max} = 7.9424\text{ m}$, toe runout $7.7678\text{ m}$, crest settlement $5.5405\text{ m}$, and $\kappa_{\max} = 4.9304$ ($\kappa_{\text{mean}} = 0.0883$).
- `L-URMI-LONG-HS` (Model HS): undergoes 3 retrogressive collapse surges ($t = 0.25\text{ s}$, $0.8\text{–}2.0\text{ s}$, and $5.2\text{–}6.1\text{ s}$), reaching continuum $|u|_{\max} = 13.5387\text{ m}$ (**$+70.46\%$**), toe runout $13.0667\text{ m}$ (**$+68.22\%$**), crest settlement $7.7317\text{ m}$ (**$+39.55\%$**), and $\kappa_{\max} = 7.5377$ (**$1.53\times$**, $\kappa_{\text{mean}} = 0.1756$, $+98.9\%$).
- Artifacts: `research/cliff/m5_urmi_long_summary.json`, `research/cliff/plots/m5_urmi_long_dashboard.png`, `research/cliff/plots/m5_urmi_long_spatial_localization.png`, `research/cliff/videos/5_cliff_urmi_long_hardening_lh.mp4`, `research/cliff/videos/6_cliff_urmi_long_softening_lhs.mp4`, and `research/cliff/videos/cliff_urmi_long_h_vs_hs.mp4`.


## Human-approved clay slope28October
New h.5/PPC2x2/14010MP native run started08:44WIB. Human chose peak-initial phi33.99 (originalphi0 hardening intentionally replaced), positive quartertanphi residual9.568deg, Dphi<=.75. No Urmi material switch or CUclaim. Gravityramp recorded, no geostaticequilibriumclaim. Main outcomes pending; see [[urmi-mc-proper-main]] for olderfailedattempt, not thisnewmaterial.
