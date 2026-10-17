# M3 Parameter Provenance & Constitutive Assumptions

## 1. Scientific Scope & Non-Calibration Policy

All parameters in this study are **prescribed reference and scenario parameters** compiled from:
1. [MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md](file:///d:/MPM/research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md) (`docs/Numerical Simulation of Residual Soil Triaxial.pdf`, pages 6–14 for the Residual Soil pair and pages 17–25 for the independent Zhan et al. 2012 Soil Cliff pair).
2. [Prediction of retrogressive landslide in sensitive clays.pdf](file:///d:/MPM/docs/Prediction%20of%20retrogressive%20landslide%20in%20sensitive%20clays.pdf) — Urmi, Z.A., Yerro, A., Saeidi, A., & Chavali, R.V.P. (2024), *Engineering Geology* 340, 107669 (for the two-stage MPM gravity initialization + dynamic post-failure protocol and the Eq. 2 exponential-linear post-peak softening law comparison).

No curves from the slide deck or paper have been digitized for parameter fitting or optimization.

---

## 2. Dataset 1 — Residual Soil Pair (`T-100-H`, `T-100-HS`, `T-200-H`, `T-200-HS`)

| Parameter | Symbol | Value (SI) | Source & Classification |
|---|---|---|---|
| Bulk unit weight | $\gamma$ | $16.83\text{ kN/m}^3$ | PDF p. 6 (`reference_not_calibration`) |
| Standard gravity | $g$ | $9.80665\text{ m/s}^2$ | SI convention (`derived_si`) |
| Mass density | $\rho = \gamma / g$ | $1716.1824256292906\text{ kg/m}^3$ | Derived SI (`derived_si`) |
| Young's modulus | $E$ | $20.0 \times 10^6\text{ Pa}$ | PDF p. 7/11 (`reference_not_calibration`) |
| Poisson's ratio | $\nu$ | $0.20$ | PDF p. 7/11 (`reference_not_calibration`) |
| Cohesion | $c'$ | $0.0\text{ Pa}$ | PDF p. 7/11 (`reference_not_calibration`) |
| Dilation angle | $\psi$ | $0.0^\circ$ ($0.0\text{ rad}$) | PDF p. 7/11 baseline (`reference_not_calibration`) |
| Peak plastic strain | $\kappa_{\text{peak}}$ | $0.037$ | PDF p. 7/11 (`reference_not_calibration`) |
| Residual plastic strain | $\kappa_{\text{res}}$ | $0.20$ | PDF p. 7/11 (`reference_not_calibration`) |
| Friction table `(κ, φ_deg)` | $\phi(\kappa)$ | `(0, 0°), (0.0068, 27.10°), (0.037, 33.99°), (0.10, 27.62°), (0.20, 16.34°)` | PDF p. 7/11 (`reference_not_calibration`) |
| Confining pressures | $\sigma_3$ | $100\text{ kPa}$, $200\text{ kPa}$ | PDF p. 6 (`reference_not_calibration`) |
| Specimen 3D geometry | $D \times H$ | $\varnothing 0.07\text{ m} \times 0.14\text{ m}$ | Master Plan Section 4 M4 (`scenario_parameter`) |

### Model H vs Model HS Distinction (Residual Soil)
- **Model H (`:mc-h`)**: Evaluates $\phi_{\text{H}}(\kappa) = \phi_{\text{table}}(\min(\kappa, 0.037))$. Pre-peak hardening is identical to Model HS; for $\kappa \ge 0.037$, friction remains clamped at the peak plateau $\phi_p = 33.99^\circ$.
- **Model HS (`:mc-hs`)**: Evaluates $\phi_{\text{HS}}(\kappa) = \phi_{\text{table}}(\kappa)$ with endpoint clamping at $\phi_r = 16.34^\circ$ for $\kappa \ge 0.20$.

---

## 3. Dataset 2 — Soil Cliff / Slope Pair (`L-H`, `L-HS`, `L-SENS-*`)

| Parameter | Symbol | Value (SI) | Source & Classification |
|---|---|---|---|
| Bulk unit weight | $\gamma$ | $18.8\text{ kN/m}^3$ | PDF p. 17, Zhan et al. (2012) (`reference_not_calibration`) |
| Mass density | $\rho = \gamma / g$ | $1917.066479888647\text{ kg/m}^3$ | Derived SI (`derived_si`) |
| Young's modulus | $E$ | $5.25 \times 10^6\text{ Pa}$ (min $4.0\text{ MPa}$) | PDF p. 17 $E=25(p'+100)\text{ kPa}$ (`scenario_assumption`) |
| Poisson's ratio | $\nu$ | $0.20$ | PDF p. 17 (`reference_not_calibration`) |
| Dilation angle | $\psi$ | $0.0^\circ$ (sensitivity: $\psi = \phi'$) | PDF p. 17 (`reference_not_calibration`) |
| Peak cohesion & friction | $c'_p, \phi'_p$ | $7.0\text{ kPa}, 20.0^\circ$ at $\kappa_p = 0.05$ | PDF p. 17 (`reference_not_calibration`) |
| Residual cohesion & friction | $c'_r, \phi'_r$ | $2.0\text{ kPa}, 13.0^\circ$ at $\kappa_r = 0.20$ | PDF p. 17 (`reference_not_calibration`) |
| Initial pre-peak ramp | $c'_0, \phi'_0$ | $(5.0\text{ kPa}, 15.0^\circ) \to (7.0\text{ kPa}, 20.0^\circ)$ on $\kappa \in [0, 0.05]$ (plus plateau-from-zero variant $(7.0\text{ kPa}, 20.0^\circ)$ on $[0, 0.05]$) | Master Plan Section 3.1 (`scenario_assumption`) |
| Stage 1 local damping | $\alpha_1$ | $0.75$ (quasi-static gravity initialization) | Urmi et al. (2024) Section 4, p. 6 (`methodology_reference`) |
| Stage 2 local damping | $\alpha_2$ | $0.02$ (dynamic post-failure propagation) | Urmi et al. (2024) Section 4, p. 6 (`methodology_reference`) |

---

## 4. Internal Plastic Strain Convention (`κ`)

In `cl-mpm/models/mc-evolution`:
$$\Delta\kappa = \sqrt{\frac{2}{3} \|\operatorname{dev}(\Delta\boldsymbol{\varepsilon}^p)\|^2}, \qquad \kappa_{n+1} = \kappa_n + \Delta\kappa$$
- The legacy native scalar `mp-strain-plastic-vm` is stored as $\sqrt{3 J_2(\operatorname{dev}\Delta\boldsymbol{\varepsilon}^p)} = 1.5\,\kappa$ for compatibility with existing native inspection tools, while all constitutive table lookups use $\kappa$ directly without applying FLAC's $\times 20$ axisym-to-3D heuristic multiplier.
