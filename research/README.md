# Native Hardening–Softening Comparative Study (M0–M6 Complete)

This directory contains the complete implementation, verification, numerical outputs,
plots, side-by-side videos, and scientific comparison report of the Mohr–Coulomb
strain-hardening (**Model H**, `:mc-h`) and strain-hardening–softening (**Model HS**, `:mc-hs`)
study on `codex/mc-hardening-softening-study`, following the
[master plan](plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md) and the two-stage MPM
landslide protocol of Urmi et al. (2024) (`docs/Prediction of retrogressive landslide in sensitive clays.pdf`).

- **Final Synthesis Report:** [`reports/FINAL_HARDENING_SOFTENING_COMPARISON.md`](reports/FINAL_HARDENING_SOFTENING_COMPARISON.md)
- **Canonical Metrics JSON:** [`comparisons/h_vs_hs_metrics.json`](comparisons/h_vs_hs_metrics.json)

## Milestone Status Summary

| Milestone | Status | Verified Evidence & Outputs |
| --- | --- | --- |
| **M0:** Native framework & architecture | **COMPLETE** | Merged to `main` via PR #8 (`e6f9abe`); Section 2/5 physical ownership layout in `src/`, `materials/`, `scenarios/`, `cases/` |
| **M1:** Source-aware reference data | **COMPLETE** | `python research/references/test_reference_data.py` (9/9 integrity tests PASS); [`references/PROVENANCE.md`](references/PROVENANCE.md) |
| **M2:** Dedicated MC H/HS materials | **COMPLETE** | Installed in `materials/models/plastic/mohr-coulomb-evolution/` (`cl-mpm/models/mc-evolution`); `tests/materials/mc-evolution-points.lisp` (34/34 assertions PASS) |
| **M3:** Constitutive point verification | **COMPLETE** | 7 constitutive pairs (`C-RES-100/200`, `C-RES-URMI-100/200`, `C-ZHAN-50/100`, `C-ZHAN-URMI-50`), pre-peak $\max |\Delta q| \le 1.17 \times 10^{-11}\text{ kPa}$, post-peak drop $-69.12\%$ (Resende) and $-52.69\%$ (Zhan); [`constitutive-tests/m3_verification_summary.json`](constitutive-tests/m3_verification_summary.json) & 4 plots in [`constitutive-tests/plots/`](constitutive-tests/plots/) |
| **M4:** Paired 3D MPM Triaxial (`T-100-H` vs `T-100-HS`) | **COMPLETE** | $780$ 3D GIMP particles ($\sigma_3 = 100\text{ kPa}$), pre-peak $\max |\Delta q| = 5.29 \times 10^{-12}\text{ kPa}$, post-peak $q_H = 242.39\text{ kPa}$ vs $q_{HS} = 91.31\text{ kPa}$ ($-62.33\%$), 3D shear band $\kappa_{\max} = 0.6586$ ($4.20\times$ localization); [`triaxial/m4_verification_summary.json`](triaxial/m4_verification_summary.json), [`triaxial/plots/`](triaxial/plots/), and [`triaxial/videos/triaxial_100kpa_h_vs_hs.mp4`](triaxial/videos/triaxial_100kpa_h_vs_hs.mp4) |
| **M5:** Paired 2D MPM Cliff (`L-H` vs `L-HS`) | **COMPLETE** | $5,667$ 2D GIMP particles (Zhan cliff parameters + Urmi et al. 2024 two-stage protocol: 200 gravity settle steps + 875 dynamic steps to $t = 1.93\text{ s}$), shear-band $\kappa_{\max}: 1.7993 \to 4.7737$ ($2.65\times$), max displacement $3.7089\text{ m} \to 5.6345\text{ m}$ ($+51.92\%$), toe runout $3.2254\text{ m} \to 4.4764\text{ m}$ ($+38.79\%$), crest settlement $3.0225\text{ m} \to 3.6408\text{ m}$ ($+20.46\%$); [`cliff/m5_verification_summary.json`](cliff/m5_verification_summary.json), [`cliff/plots/`](cliff/plots/), and [`cliff/videos/cliff_h_vs_hs.mp4`](cliff/videos/cliff_h_vs_hs.mp4) |
| **M6:** Final synthesis, documentation & handover | **COMPLETE** | [`reports/FINAL_HARDENING_SOFTENING_COMPARISON.md`](reports/FINAL_HARDENING_SOFTENING_COMPARISON.md), [`comparisons/h_vs_hs_metrics.json`](comparisons/h_vs_hs_metrics.json), updated `docs/AI_HANDOVER.md` and `wiki-vault/wiki/` |

## Directory Structure

- `plans/` — Master plan (`MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md`) and SHA-256 provenance.
- `references/` — Digitized Resende (1985) and Zhan et al. (2012) tables, provenance notes, and `test_reference_data.py`.
- `constitutive-tests/` — Milestone M3 CSV trajectories, `m3_verification_summary.json`, and 4 comparison PNGs (`plots/`).
- `triaxial/` — Milestone M4 3D MPM runs (`t-100-h/`, `t-100-hs/`), `m4_verification_summary.json`, comparison plots (`plots/`), and side-by-side video (`videos/triaxial_100kpa_h_vs_hs.mp4`).
- `cliff/` — Milestone M5 2D MPM runs (`l-h/`, `l-hs/`), `m5_verification_summary.json`, comparison plots (`plots/`), and side-by-side video (`videos/cliff_h_vs_hs.mp4`).
- `comparisons/` — Canonical cross-milestone metrics (`h_vs_hs_metrics.json`).
- `reports/` — Technical design notes and [`FINAL_HARDENING_SOFTENING_COMPARISON.md`](reports/FINAL_HARDENING_SOFTENING_COMPARISON.md).
