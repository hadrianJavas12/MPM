#!/usr/bin/env python3
"""Generate Milestone M3 constitutive verification plots (C-01: Model H vs C-02: Model HS)."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _pfloat(val: str) -> float:
    return float(val.replace("d", "e").replace("D", "E"))


def load_trajectories(csv_path: Path) -> dict[str, list[dict[str, float]]]:
    by_case: dict[str, list[dict[str, float]]] = defaultdict(list)
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row["case_id"]
            parsed = {
                k: (_pfloat(v) if k not in ("case_id", "dataset", "variant") else v)
                for k, v in row.items()
            }
            by_case[case_id].append(parsed)
    return by_case


def load_convergence(csv_path: Path) -> list[dict[str, float]]:
    rows = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: _pfloat(v) for k, v in row.items()})
    return rows


def plot_residual_pair(by_case: dict, ref_dir: Path, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.5), dpi=160)
    fig.suptitle(
        "Milestone M3 — Residual Soil Constitutive Point Verification (C-01: Model H vs C-02: Model HS)\n"
        r"$E = 20\,\mathrm{MPa},\;\nu = 0.2,\;c = 0,\;\psi = 0^\circ,\;\kappa_{\mathrm{peak}} = 0.037$",
        fontsize=12.5,
        fontweight="bold",
    )

    configs = [
        ("C-RES-100-H", "Model H (100 kPa)", "#1f77b4", "--"),
        ("C-RES-100-HS", "Model HS (100 kPa)", "#1f77b4", "-"),
        ("C-RES-200-H", "Model H (200 kPa)", "#d62728", "--"),
        ("C-RES-200-HS", "Model HS (200 kPa)", "#d62728", "-"),
    ]

    for case_id, label, color, ls in configs:
        rows = by_case[case_id]
        eps = [r["axial_strain_pct"] for r in rows]
        q = [r["q_kpa"] for r in rows]
        phi = [r["phi_deg"] for r in rows]
        kappa = [r["kappa"] for r in rows]
        work = [r["plastic_work_j_m3"] / 1000.0 for r in rows]

        axes[0, 0].plot(eps, q, label=label, color=color, linestyle=ls, linewidth=2.1)
        axes[0, 1].plot(kappa, phi, label=label, color=color, linestyle=ls, linewidth=2.1)
        axes[1, 0].plot(eps, kappa, label=label, color=color, linestyle=ls, linewidth=2.1)
        axes[1, 1].plot(eps, work, label=label, color=color, linestyle=ls, linewidth=2.1)

    # Overlay digitized digitization points from M1 reference JSON if present
    for s3, color, marker, fname in [
        (100, "#1f77b4", "o", "triaxial_100kpa_reference.json"),
        (200, "#d62728", "s", "triaxial_200kpa_reference.json"),
    ]:
        ref_file = ref_dir / fname
        if ref_file.exists():
            data = json.loads(ref_file.read_text(encoding="utf-8"))
            pts = data.get("curves", {}).get("paper_mpm_mc_hardening_softening", [])
            if pts:
                rx = [p["axial_strain_percent"] for p in pts]
                ry = [p["deviatoric_stress_kpa"] for p in pts]
                axes[0, 0].scatter(
                    rx[::2],
                    ry[::2],
                    color=color,
                    marker=marker,
                    s=22,
                    alpha=0.65,
                    label=f"Digitized M1 Ref ({s3} kPa)",
                )

    axes[0, 0].set_xlabel("Axial Strain (%)")
    axes[0, 0].set_ylabel("Deviatoric Stress q = σ₁ - σ₃ (kPa)")
    axes[0, 0].set_title("(a) Deviatoric Stress vs Axial Strain")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=8.5)

    axes[0, 1].axvline(0.037, color="gray", linestyle=":", linewidth=1.2, label="Peak κ = 0.037")
    axes[0, 1].set_xlabel("Internal Plastic Variable κ (-)")
    axes[0, 1].set_ylabel("Mobilized Friction Angle φ (deg)")
    axes[0, 1].set_title("(b) Strength Evolution Law φ(κ): H Plateau vs HS Softening")
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=8.5)

    axes[1, 0].axhline(0.037, color="gray", linestyle=":", linewidth=1.2, label="Peak κ = 0.037")
    axes[1, 0].set_xlabel("Axial Strain (%)")
    axes[1, 0].set_ylabel("Internal Plastic Variable κ (-)")
    axes[1, 0].set_title("(c) Equivalent Plastic Shear Strain κ vs Axial Strain")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=8.5)

    axes[1, 1].set_xlabel("Axial Strain (%)")
    axes[1, 1].set_ylabel("Cumulative Plastic Work (kJ/m³)")
    axes[1, 1].set_title("(d) Cumulative Plastic Dissipation")
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend(fontsize=8.5)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_zhan_pair(by_case: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.5), dpi=160)
    fig.suptitle(
        "Milestone M3 — Zhan Cliff Soil Constitutive Point Verification (C-01: Model H vs C-02: Model HS)\n"
        r"$E = 5.25\,\mathrm{MPa},\;\nu = 0.2,\;\phi: 15^\circ \to 20^\circ \to 13^\circ,\;c: 5 \to 7 \to 2\,\mathrm{kPa}$",
        fontsize=12.5,
        fontweight="bold",
    )

    configs = [
        ("C-ZHAN-50-H", "Model H (σ₃ = 50 kPa)", "#2ca02c", "--"),
        ("C-ZHAN-50-HS", "Model HS (σ₃ = 50 kPa)", "#2ca02c", "-"),
        ("C-ZHAN-100-H", "Model H (σ₃ = 100 kPa)", "#9467bd", "--"),
        ("C-ZHAN-100-HS", "Model HS (σ₃ = 100 kPa)", "#9467bd", "-"),
    ]

    for case_id, label, color, ls in configs:
        rows = by_case[case_id]
        eps = [r["axial_strain_pct"] for r in rows]
        q = [r["q_kpa"] for r in rows]
        phi = [r["phi_deg"] for r in rows]
        c_kpa = [r["c_kpa"] for r in rows]
        kappa = [r["kappa"] for r in rows]

        axes[0, 0].plot(eps, q, label=label, color=color, linestyle=ls, linewidth=2.1)
        axes[0, 1].plot(kappa, phi, label=label, color=color, linestyle=ls, linewidth=2.1)
        axes[1, 0].plot(kappa, c_kpa, label=label, color=color, linestyle=ls, linewidth=2.1)
        axes[1, 1].plot(eps, kappa, label=label, color=color, linestyle=ls, linewidth=2.1)

    axes[0, 0].set_xlabel("Axial Strain (%)")
    axes[0, 0].set_ylabel("Deviatoric Stress q = σ₁ - σ₃ (kPa)")
    axes[0, 0].set_title("(a) Deviatoric Stress vs Axial Strain")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=8.5)

    axes[0, 1].axvline(0.05, color="gray", linestyle=":", linewidth=1.2, label="Peak κ = 0.05")
    axes[0, 1].set_xlabel("Internal Plastic Variable κ (-)")
    axes[0, 1].set_ylabel("Mobilized Friction Angle φ (deg)")
    axes[0, 1].set_title("(b) Friction Evolution φ(κ)")
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=8.5)

    axes[1, 0].axvline(0.05, color="gray", linestyle=":", linewidth=1.2, label="Peak κ = 0.05")
    axes[1, 0].set_xlabel("Internal Plastic Variable κ (-)")
    axes[1, 0].set_ylabel("Mobilized Cohesion c (kPa)")
    axes[1, 0].set_title("(c) Coupled Cohesion Evolution c(κ)")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=8.5)

    axes[1, 1].axhline(0.05, color="gray", linestyle=":", linewidth=1.2, label="Peak κ = 0.05")
    axes[1, 1].set_xlabel("Axial Strain (%)")
    axes[1, 1].set_ylabel("Internal Plastic Variable κ (-)")
    axes[1, 1].set_title("(d) Equivalent Plastic Strain κ Trajectory")
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend(fontsize=8.5)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_urmi_comparison(by_case: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), dpi=160)
    fig.suptitle(
        "Milestone M3 — Piecewise-Linear vs Urmi et al. (2024) Eq. (2) Exponential-Linear Softening",
        fontsize=12,
        fontweight="bold",
    )

    series = [
        ("C-RES-100-H", "Residual H (Piecewise / Urmi Plateau)", "#1f77b4", "--"),
        ("C-RES-100-HS", "Residual HS (Piecewise Table)", "#1f77b4", "-"),
        ("C-RES-URMI-100-HS", "Residual HS (Urmi Eq. 2, β = -25)", "#ff7f0e", "-."),
        ("C-ZHAN-50-H", "Zhan H (Plateau)", "#2ca02c", "--"),
        ("C-ZHAN-50-HS", "Zhan HS (Piecewise Table)", "#2ca02c", "-"),
        ("C-ZHAN-URMI-50-HS", "Zhan HS (Urmi Eq. 2, β = -25)", "#d62728", "-."),
    ]

    for case_id, label, color, ls in series:
        rows = by_case[case_id]
        eps = [r["axial_strain_pct"] for r in rows]
        q = [r["q_kpa"] for r in rows]
        phi = [r["phi_deg"] for r in rows]
        kappa = [r["kappa"] for r in rows]
        axes[0].plot(eps, q, label=label, color=color, linestyle=ls, linewidth=2.0)
        axes[1].plot(kappa, phi, label=label, color=color, linestyle=ls, linewidth=2.0)

    axes[0].set_xlabel("Axial Strain (%)")
    axes[0].set_ylabel("Deviatoric Stress q (kPa)")
    axes[0].set_title("(a) Stress–Strain Response")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)

    axes[1].set_xlabel("Internal Plastic Variable κ (-)")
    axes[1].set_ylabel("Mobilized Friction Angle φ (deg)")
    axes[1].set_title("(b) Post-Peak Softening Trajectory φ(κ)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=8)

    fig.tight_layout(rect=[0, 0, 1, 0.92])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_substep_convergence(conv_rows: list[dict[str, float]], out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=160)
    fig.suptitle(
        "Milestone M3 — Return-Mapping Sub-Increment Convergence (C-RES-100-HS)",
        fontsize=12,
        fontweight="bold",
    )
    steps = [r["steps"] for r in conv_rows]
    peak_q = [r["peak_q_kpa"] for r in conv_rows]
    final_q = [r["final_q_kpa"] for r in conv_rows]
    max_res = [max(1e-16, r["max_yield_residual_pa"]) for r in conv_rows]

    axes[0].plot(steps, peak_q, "o-", label="Peak q (kPa)", linewidth=2.0, color="#1f77b4")
    axes[0].plot(steps, final_q, "s--", label="Final q at 25% Strain (kPa)", linewidth=2.0, color="#d62728")
    axes[0].set_xlabel("Number of Strain Increments")
    axes[0].set_ylabel("Deviatoric Stress q (kPa)")
    axes[0].set_title("(a) Peak & Residual Stress vs Step Count")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].semilogy(steps, max_res, "d-", linewidth=2.0, color="#2ca02c")
    axes[1].axhline(1e-3, color="red", linestyle=":", label="Pass Gate (10⁻³ Pa)")
    axes[1].set_xlabel("Number of Strain Increments")
    axes[1].set_ylabel("Max Yield Surface Residual |f| (Pa)")
    axes[1].set_title("(b) Yield Surface Drift / Residual Enforcement")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.tight_layout(rect=[0, 0, 1, 0.91])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    m3_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (repo / "research" / "constitutive-tests")
    ref_dir = repo / "research" / "configs"
    plots_dir = m3_dir / "plots"

    by_case = load_trajectories(m3_dir / "c01_c02_trajectories.csv")
    conv_rows = load_convergence(m3_dir / "c01_c02_substep_convergence.csv")

    plot_residual_pair(by_case, ref_dir, plots_dir / "m3_residual_soil_comparison.png")
    plot_zhan_pair(by_case, plots_dir / "m3_zhan_cliff_comparison.png")
    plot_urmi_comparison(by_case, plots_dir / "m3_urmi_eq2_comparison.png")
    plot_substep_convergence(conv_rows, plots_dir / "m3_substep_convergence.png")
    print(f"Saved M3 constitutive verification plots to {plots_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
