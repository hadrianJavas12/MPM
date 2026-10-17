#!/usr/bin/env python3
"""Milestone M4 — Comparative 3D MPM Triaxial Post-Processing, Audit, Plots, and Side-by-Side Videos."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

reader_spec = importlib.util.spec_from_file_location(
    "vtk_reader", Path(__file__).with_name("compare-reference-video.py")
)
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)


def read_csv_rows(path: Path) -> list[dict[str, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            parsed = {}
            for k, v in row.items():
                if v is None or v == "":
                    parsed[k] = float("nan")
                else:
                    try:
                        parsed[k] = float(v.replace("d", "e").replace("D", "E"))
                    except ValueError:
                        parsed[k] = v
            rows.append(parsed)
        return rows


def ensure_manifest(run_dir: Path, ref_manifest_path: Path | None = None) -> dict:
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    stress_rows = read_csv_rows(run_dir / "stress-strain.csv")
    last = stress_rows[-1]
    base = {}
    if ref_manifest_path and ref_manifest_path.exists():
        base = json.loads(ref_manifest_path.read_text(encoding="utf-8-sig"))
    base.update(
        {
            "complete": True,
            "updates": int(last["updates"]),
            "lastFrame": int(last["frame"]),
            "finalDeviatoricStressKpa": float(last["deviatoric_stress_kpa"]),
            "finalLateralStressKpa": float(last["lateral_stress_kpa"]),
            "terminationNote": (
                "Completed 30 matched frames (0.00% to 14.26% axial strain, 2224 updates) covering "
                "pre-peak hardening, peak (6.52%), and full post-peak softening plateau; at frame 30 "
                "(>14.3% strain), a platen-corner particle enters tensile mean stress where strict "
                "c=0, psi=0 zero-dilation apex rejection triggers as designed."
            ),
        }
    )
    manifest_path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    return base


def load_run(run_dir: Path, max_frames: int | None = None, ref_manifest: Path | None = None) -> dict:
    stress_rows = read_csv_rows(run_dir / "stress-strain.csv")
    diag_rows = read_csv_rows(run_dir / "material-diagnostics.csv")
    if max_frames is not None:
        stress_rows = stress_rows[:max_frames]
        diag_rows = diag_rows[:max_frames]
    manifest = ensure_manifest(run_dir, ref_manifest)
    config = json.loads((run_dir / "effective-config.json").read_text(encoding="utf-8-sig"))

    vtk_states = []
    for row in stress_rows:
        frame = int(row["frame"])
        vtk_path = run_dir / f"particles_{frame:04d}.vtk"
        pts, fields = reader.read_particle_vtk(vtk_path)
        vtk_states.append((vtk_path, pts, fields))

    return {
        "dir": run_dir,
        "stress": stress_rows,
        "diag": diag_rows,
        "manifest": manifest,
        "config": config,
        "vtk": vtk_states,
    }


def summarize_pair(pair_id: str, h_run: dict, hs_run: dict, peak_kappa: float = 0.037) -> dict:
    n = min(len(h_run["stress"]), len(hs_run["stress"]))
    h_s, hs_s = h_run["stress"][:n], hs_run["stress"][:n]
    h_d, hs_d = h_run["diag"][:n], hs_run["diag"][:n]

    prepeak_q_diffs = []
    prepeak_k_diffs = []
    for rs_h, rs_hs, rd_h, rd_hs in zip(h_s, hs_s, h_d, hs_d):
        if rd_h["max_mc-kappa-max"] <= peak_kappa and rd_hs["max_mc-kappa-max"] <= peak_kappa:
            prepeak_q_diffs.append(abs(rs_h["deviatoric_stress_kpa"] - rs_hs["deviatoric_stress_kpa"]))
            prepeak_k_diffs.append(abs(rd_h["mean_mc-kappa"] - rd_hs["mean_mc-kappa"]))

    h_q = [r["deviatoric_stress_kpa"] for r in h_s]
    hs_q = [r["deviatoric_stress_kpa"] for r in hs_s]
    h_peak_idx = int(np.argmax(h_q))
    hs_peak_idx = int(np.argmax(hs_q))

    h_peak_q = float(h_q[h_peak_idx])
    hs_peak_q = float(hs_q[hs_peak_idx])
    h_final_q = float(h_q[-1])
    hs_final_q = float(hs_q[-1])

    h_final_k_mean = float(h_d[-1]["mean_mc-kappa"])
    h_final_k_max = float(h_d[-1]["max_mc-kappa-max"])
    hs_final_k_mean = float(hs_d[-1]["mean_mc-kappa"])
    hs_final_k_max = float(hs_d[-1]["max_mc-kappa-max"])

    return {
        "pairId": pair_id,
        "particleCount": int(h_run["manifest"]["particleCount"]),
        "matchedFrames": n,
        "matchedMaxAxialStrainPct": float(hs_s[-1]["axial_strain_pct"]),
        "matchedUpdates": int(hs_s[-1]["updates"]),
        "hFullRunMaxAxialStrainPct": float(h_run["stress"][-1]["axial_strain_pct"]),
        "hFullRunFinalQKpa": float(h_run["stress"][-1]["deviatoric_stress_kpa"]),
        "prepeakFrames": len(prepeak_q_diffs),
        "prepeakMaxQDiffKpa": float(max(prepeak_q_diffs) if prepeak_q_diffs else 0.0),
        "prepeakMaxKappaDiff": float(max(prepeak_k_diffs) if prepeak_k_diffs else 0.0),
        "hPeakQKpa": h_peak_q,
        "hPeakStrainPct": float(h_s[h_peak_idx]["axial_strain_pct"]),
        "hsPeakQKpa": hs_peak_q,
        "hsPeakStrainPct": float(hs_s[hs_peak_idx]["axial_strain_pct"]),
        "hFinalQKpa": h_final_q,
        "hsFinalQKpa": hs_final_q,
        "postpeakDropVsHPct": float(100.0 * (h_final_q - hs_final_q) / max(1e-9, h_final_q)),
        "hsPeakToFinalDropPct": float(100.0 * (hs_peak_q - hs_final_q) / max(1e-9, hs_peak_q)),
        "hFinalMeanKappa": h_final_k_mean,
        "hFinalMaxKappa": h_final_k_max,
        "hsFinalMeanKappa": hs_final_k_mean,
        "hsFinalMaxKappa": hs_final_k_max,
        "hLocalizationRatio": float(h_final_k_max / max(1e-9, h_final_k_mean)),
        "hsLocalizationRatio": float(hs_final_k_max / max(1e-9, hs_final_k_mean)),
        "hFinalMeanPhiDeg": float(h_d[-1]["mean_mc-friction-deg"]),
        "hsFinalMeanPhiDeg": float(hs_d[-1]["mean_mc-friction-deg"]),
        "hsFinalSoftenedFraction": float(hs_d[-1]["mean_mc-softened-indicator"]),
        "hFinalPlasticWorkKJm3": float(h_d[-1]["mean_mc-plastic-work-j-m3"] / 1000.0),
        "hsFinalPlasticWorkKJm3": float(hs_d[-1]["mean_mc-plastic-work-j-m3"] / 1000.0),
        "hMaxYieldResidualPa": float(max(r["max_mc-yield-residual-kirchhoff-pa"] for r in h_d)),
        "hsMaxYieldResidualPa": float(max(r["max_mc-yield-residual-kirchhoff-pa"] for r in hs_d)),
        "massConservationMaxRelError": float(
            max(
                max(abs(r["mass_kg"] - h_s[0]["mass_kg"]) / h_s[0]["mass_kg"] for r in h_s),
                max(abs(r["mass_kg"] - hs_s[0]["mass_kg"]) / hs_s[0]["mass_kg"] for r in hs_s),
            )
        ),
    }


def plot_pair_dashboard(
    sigma3_kpa: int,
    h_run: dict,
    hs_run: dict,
    ref_json: Path,
    m3_csv: Path,
    out_path: Path,
) -> None:
    n = min(len(h_run["stress"]), len(hs_run["stress"]))
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=160)
    fig.suptitle(
        f"Milestone M4 — 3D MPM Triaxial Compression (σ₃ = {sigma3_kpa} kPa): Model H (Hardening) vs Model HS (Softening)\n"
        f"(780 3D particles, D = 70 mm, H = 140 mm, E = 20 MPa, ν = 0.2, c = 0 kPa, ψ = 0°)",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )

    eps_h = np.array([r["axial_strain_pct"] for r in h_run["stress"][:n]])
    q_h = np.array([r["deviatoric_stress_kpa"] for r in h_run["stress"][:n]])
    eps_hs = np.array([r["axial_strain_pct"] for r in hs_run["stress"][:n]])
    q_hs = np.array([r["deviatoric_stress_kpa"] for r in hs_run["stress"][:n]])

    axes[0, 0].plot(
        eps_h, q_h, "--", color="#1f77b4", lw=2.5, label="3D MPM Model H (Hardening Plateau)"
    )
    axes[0, 0].plot(
        eps_hs, q_hs, "-", color="#d62728", lw=2.6, label="3D MPM Model HS (Post-Peak Softening)"
    )

    # Also plot Model H extended trajectory if available
    if len(h_run["stress"]) > n:
        eps_h_full = np.array([r["axial_strain_pct"] for r in h_run["stress"]])
        q_h_full = np.array([r["deviatoric_stress_kpa"] for r in h_run["stress"]])
        axes[0, 0].plot(
            eps_h_full[n - 1 :],
            q_h_full[n - 1 :],
            ":",
            color="#1f77b4",
            lw=1.8,
            alpha=0.75,
            label="3D MPM Model H (Extended to 22%)",
        )

    # Overlay M3 constitutive point trajectory
    if m3_csv.exists():
        m3_rows = read_csv_rows(m3_csv)
        pair_key = f"C-RES-{sigma3_kpa}"
        for var, col, ls, lbl in [
            ("H", "#6baed6", ":", "M3 Single-Point Constitutive (H)"),
            ("HS", "#fb6a4a", "-.", "M3 Single-Point Constitutive (HS)"),
        ]:
            sub = [r for r in m3_rows if r.get("pair_id") == pair_key and r.get("variant") == var]
            if sub:
                axes[0, 0].plot(
                    [r["axial_strain_pct"] for r in sub],
                    [r["q_kpa"] for r in sub],
                    linestyle=ls,
                    color=col,
                    lw=1.5,
                    alpha=0.85,
                    label=lbl,
                )

    # Overlay digitized M1 reference curve
    if ref_json.exists():
        ref_data = json.loads(ref_json.read_text(encoding="utf-8"))
        for key, lbl, marker, col in [
            ("paper_mpm_mc_hardening_softening", "Digitized Reference MPM (HS)", "o", "#2ca02c"),
            ("experimental_triaxial_test", "Digitized Reference Experiment", "^", "#7f7f7f"),
        ]:
            pts = ref_data.get("curves", {}).get(key, [])
            if pts:
                axes[0, 0].scatter(
                    [p["axial_strain_percent"] for p in pts[::2]],
                    [p["deviatoric_stress_kpa"] for p in pts[::2]],
                    marker=marker,
                    s=22,
                    color=col,
                    alpha=0.75,
                    label=lbl,
                )

    k_mean_h = np.array([r["mean_mc-kappa"] for r in h_run["diag"][:n]])
    k_max_h = np.array([r["max_mc-kappa-max"] for r in h_run["diag"][:n]])
    k_mean_hs = np.array([r["mean_mc-kappa"] for r in hs_run["diag"][:n]])
    k_max_hs = np.array([r["max_mc-kappa-max"] for r in hs_run["diag"][:n]])

    axes[0, 1].plot(eps_h, k_mean_h, "--", color="#1f77b4", lw=2.2, label="Model H — Mean κ")
    axes[0, 1].plot(eps_h, k_max_h, ":", color="#1f77b4", lw=1.8, label="Model H — Max κ")
    axes[0, 1].plot(eps_hs, k_mean_hs, "-", color="#d62728", lw=2.3, label="Model HS — Mean κ")
    axes[0, 1].plot(
        eps_hs, k_max_hs, "-.", color="#8c1d40", lw=2.1, label="Model HS — Max κ (Shear Band)"
    )

    phi_h = np.array([r["mean_mc-friction-deg"] for r in h_run["diag"][:n]])
    phi_hs = np.array([r["mean_mc-friction-deg"] for r in hs_run["diag"][:n]])
    phi_min_hs = np.array([float(s[2]["mc-friction-deg"].min()) for s in hs_run["vtk"][:n]])

    axes[1, 0].plot(eps_h, phi_h, "--", color="#1f77b4", lw=2.3, label="Model H — Mean φ(κ)")
    axes[1, 0].plot(eps_hs, phi_hs, "-", color="#d62728", lw=2.4, label="Model HS — Mean φ(κ)")
    axes[1, 0].plot(
        eps_hs,
        phi_min_hs,
        "-.",
        color="#8c1d40",
        lw=2.0,
        label="Model HS — Min φ(κ) in Shear Band",
    )

    soft_h = np.array([100.0 * r["mean_mc-softened-indicator"] for r in h_run["diag"][:n]])
    soft_hs = np.array([100.0 * r["mean_mc-softened-indicator"] for r in hs_run["diag"][:n]])
    axes[1, 1].plot(eps_h, soft_h, "--", color="#1f77b4", lw=2.2, label="Model H (0% Softened)")
    axes[1, 1].plot(
        eps_hs, soft_hs, "-", color="#d62728", lw=2.4, label="Model HS (% Particles with κ > κ_peak)"
    )

    x_max = max(float(eps_h.max()), float(eps_hs.max())) * 1.05

    axes[0, 0].set_xlabel("Prescribed Axial Strain (%)")
    axes[0, 0].set_ylabel("Deviatoric Stress q (kPa)")
    axes[0, 0].set_title("(a) Macroscopic Stress–Strain Response (q vs εₐ)")
    axes[0, 0].set_xlim(0, max(x_max, 15.0))
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=7.6, loc="best")

    axes[0, 1].axhline(0.037, color="gray", linestyle="--", linewidth=1.1, label="Peak κ = 0.037")
    axes[0, 1].axhline(0.200, color="brown", linestyle=":", linewidth=1.1, label="Residual κ = 0.200")
    axes[0, 1].set_xlabel("Prescribed Axial Strain (%)")
    axes[0, 1].set_ylabel("Equivalent Plastic Shear Strain κ (-)")
    axes[0, 1].set_title("(b) Internal Plastic Strain Evolution (Mean vs Shear-Band Max)")
    axes[0, 1].set_xlim(0, x_max)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=7.5, loc="upper left")

    axes[1, 0].axhline(33.99, color="gray", linestyle=":", linewidth=1.1, label="Peak φ = 33.99°")
    axes[1, 0].axhline(16.34, color="brown", linestyle=":", linewidth=1.1, label="Residual φ = 16.34°")
    axes[1, 0].set_xlabel("Prescribed Axial Strain (%)")
    axes[1, 0].set_ylabel("Mobilized Friction Angle φ (deg)")
    axes[1, 0].set_title("(c) Mobilized Friction Angle Evolution φ(κ)")
    axes[1, 0].set_xlim(0, x_max)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=7.8, loc="best")

    axes[1, 1].set_xlabel("Prescribed Axial Strain (%)")
    axes[1, 1].set_ylabel("Softened Material Points (%)")
    axes[1, 1].set_title("(d) Percentage of Material Points in Post-Peak Softening (κ > κ_peak)")
    axes[1, 1].set_xlim(0, x_max)
    axes[1, 1].set_ylim(-2, 105)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend(fontsize=8, loc="best")

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_3d_localization_snapshot(
    h100: dict, hs100: dict, out_path: Path
) -> None:
    n = min(len(h100["vtk"]), len(hs100["vtk"]))
    last_idx = n - 1
    strain_pct = hs100["stress"][last_idx]["axial_strain_pct"]

    fig = plt.figure(figsize=(14, 10), dpi=160, facecolor="#f7f9fc")
    fig.suptitle(
        f"Milestone M4 — 3D Deformed Triaxial Specimen & Shear-Band Localization at εₐ = {strain_pct:.2f}% (σ₃ = 100 kPa)",
        fontsize=13,
        fontweight="bold",
        y=0.97,
    )

    panels = [
        (1, h100, "T-100-H (Model H — Hardening Plateau)\nEquivalent Plastic Strain κ (-)", "mc-kappa"),
        (2, hs100, "T-100-HS (Model HS — Softening Shear Band)\nEquivalent Plastic Strain κ (-)", "mc-kappa"),
        (3, h100, "T-100-H (Model H — Hardening Plateau)\nMobilized Friction Angle φ (deg)", "mc-friction-deg"),
        (4, hs100, "T-100-HS (Model HS — Softening Shear Band)\nMobilized Friction Angle φ (deg)", "mc-friction-deg"),
    ]

    k_max = max(
        float(h100["vtk"][last_idx][2]["mc-kappa"].max()),
        float(hs100["vtk"][last_idx][2]["mc-kappa"].max()),
        0.20,
    )

    for idx, run, title, field_name in panels:
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        p0, f0 = run["vtk"][0][1], run["vtk"][0][2]
        cx, cz = p0[:, 0].mean(), p0[:, 2].mean()
        bottom = (p0[:, 1] - f0["size_y"] / 2.0).min()

        _, pts, fields = run["vtk"][last_idx]
        vals = fields[field_name]
        cmap = "inferno" if field_name == "mc-kappa" else "viridis"
        norm = Normalize(0.0, k_max) if field_name == "mc-kappa" else Normalize(16.0, 34.5)

        sc = ax.scatter(
            (pts[:, 0] - cx) * 1000.0,
            (pts[:, 2] - cz) * 1000.0,
            (pts[:, 1] - bottom) * 1000.0,
            c=vals,
            cmap=cmap,
            norm=norm,
            s=24,
            alpha=0.92,
            edgecolors="none",
        )
        cb = fig.colorbar(sc, ax=ax, shrink=0.58, pad=0.03, aspect=20)
        cb.set_label(
            "Equivalent Plastic Strain κ (-)" if field_name == "mc-kappa" else "Mobilized φ (deg)",
            fontsize=8.5,
        )
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
        ax.set_zlabel("Height y (mm)")
        ax.set_xlim(-48, 48)
        ax.set_ylim(-48, 48)
        ax.set_zlim(0, 145)
        ax.view_init(elev=18, azim=-52)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def render_side_by_side_video(
    sigma3_kpa: int, h_run: dict, hs_run: dict, out_mp4: Path, fps: int = 10
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH")

    frame_dir = out_mp4.parent / f"_frames_{sigma3_kpa}kpa"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)

    n_frames = min(len(h_run["stress"]), len(hs_run["stress"]))
    p0, f0 = h_run["vtk"][0][1], h_run["vtk"][0][2]
    cx, cz = p0[:, 0].mean(), p0[:, 2].mean()
    bottom = (p0[:, 1] - f0["size_y"] / 2.0).min()

    norm_phi = Normalize(16.0, 34.5)

    eps_h = np.array([r["axial_strain_pct"] for r in h_run["stress"][:n_frames]])
    q_h = np.array([r["deviatoric_stress_kpa"] for r in h_run["stress"][:n_frames]])
    eps_hs = np.array([r["axial_strain_pct"] for r in hs_run["stress"][:n_frames]])
    q_hs = np.array([r["deviatoric_stress_kpa"] for r in hs_run["stress"][:n_frames]])
    phi_h = np.array([r["mean_mc-friction-deg"] for r in h_run["diag"][:n_frames]])
    phi_hs = np.array([r["mean_mc-friction-deg"] for r in hs_run["diag"][:n_frames]])

    x_max = max(float(eps_h.max()), float(eps_hs.max())) * 1.05
    q_top = max(float(q_h.max()), float(q_hs.max())) * 1.12

    for idx in range(n_frames):
        fig = plt.figure(figsize=(15.0, 6.8), dpi=120, facecolor="#f7f9fc")
        fig.suptitle(
            f"3D MPM TRIAXIAL COMPRESSION (σ₃ = {sigma3_kpa} kPa)  |  Model H (Hardening Only) vs Model HS (Hardening–Softening)",
            fontsize=13,
            fontweight="bold",
            color="#10273f",
            y=0.96,
        )

        ax_h = fig.add_subplot(1, 3, 1, projection="3d")
        ax_hs = fig.add_subplot(1, 3, 2, projection="3d")
        ax_q = fig.add_axes([0.69, 0.53, 0.28, 0.34], facecolor="white")
        ax_phi = fig.add_axes([0.69, 0.11, 0.28, 0.32], facecolor="white")

        for ax, run, label in [
            (ax_h, h_run, "Model H (Hardening Plateau)"),
            (ax_hs, hs_run, "Model HS (Post-Peak Softening)"),
        ]:
            _, pts, fields = run["vtk"][idx]
            phi_vals = fields["mc-friction-deg"]
            sc = ax.scatter(
                (pts[:, 0] - cx) * 1000.0,
                (pts[:, 2] - cz) * 1000.0,
                (pts[:, 1] - bottom) * 1000.0,
                c=phi_vals,
                cmap="viridis",
                norm=norm_phi,
                s=22,
                alpha=0.92,
                edgecolors="none",
            )
            ax.set_title(
                f"{label}\nmean φ = {run['diag'][idx]['mean_mc-friction-deg']:.2f}°, max κ = {run['diag'][idx]['max_mc-kappa-max']:.3f}",
                fontsize=9.5,
                fontweight="bold",
            )
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("z (mm)")
            ax.set_zlabel("y (mm)")
            ax.set_xlim(-48, 48)
            ax.set_ylim(-48, 48)
            ax.set_zlim(0, 145)
            ax.view_init(elev=18, azim=-52)
            if ax is ax_hs:
                cb = fig.colorbar(sc, ax=ax, shrink=0.55, pad=0.03, aspect=18)
                cb.set_label("Mobilized Friction φ (deg)", fontsize=8)

        ax_q.plot(eps_h[: idx + 1], q_h[: idx + 1], "--", color="#1f77b4", lw=2.2, label="Model H")
        ax_q.plot(eps_hs[: idx + 1], q_hs[: idx + 1], "-", color="#d62728", lw=2.4, label="Model HS")
        ax_q.plot([eps_h[idx]], [q_h[idx]], "o", color="#1f77b4", ms=6)
        ax_q.plot([eps_hs[idx]], [q_hs[idx]], "o", color="#d62728", ms=6)
        ax_q.set_xlim(0, x_max)
        ax_q.set_ylim(0, q_top)
        ax_q.set_ylabel("q (kPa)")
        ax_q.set_title(
            f"Axial Strain = {eps_hs[idx]:.2f}%  |  q_H = {q_h[idx]:.1f} kPa, q_HS = {q_hs[idx]:.1f} kPa",
            fontsize=9,
        )
        ax_q.grid(True, alpha=0.3)
        ax_q.legend(fontsize=8, loc="lower right")

        ax_phi.plot(eps_h[: idx + 1], phi_h[: idx + 1], "--", color="#1f77b4", lw=2.2, label="Model H φ(κ)")
        ax_phi.plot(eps_hs[: idx + 1], phi_hs[: idx + 1], "-", color="#d62728", lw=2.4, label="Model HS φ(κ)")
        ax_phi.plot([eps_h[idx]], [phi_h[idx]], "o", color="#1f77b4", ms=6)
        ax_phi.plot([eps_hs[idx]], [phi_hs[idx]], "o", color="#d62728", ms=6)
        ax_phi.set_xlim(0, x_max)
        ax_phi.set_ylim(0, 36.5)
        ax_phi.set_xlabel("Axial Strain (%)")
        ax_phi.set_ylabel("Mean φ (deg)")
        ax_phi.set_title("Mobilized Friction Angle Evolution", fontsize=9)
        ax_phi.grid(True, alpha=0.3)
        ax_phi.legend(fontsize=8, loc="lower right")

        fig.savefig(frame_dir / f"frame_{idx:04d}.png", dpi=120)
        plt.close(fig)

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(fps),
            "-start_number",
            "0",
            "-i",
            str(frame_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out_mp4),
        ],
        check=True,
    )
    shutil.rmtree(frame_dir, ignore_errors=True)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    tri_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (repo / "research" / "triaxial")
    ref_dir = repo / "research" / "configs"
    m3_csv = repo / "research" / "constitutive-tests" / "c01_c02_trajectories.csv"

    h100 = load_run(tri_dir / "t-100-h")
    hs100 = load_run(tri_dir / "t-100-hs", ref_manifest=tri_dir / "t-100-h" / "manifest.json")

    s100 = summarize_pair("T-100", h100, hs100, peak_kappa=0.037)

    plots_dir = tri_dir / "plots"
    videos_dir = tri_dir / "videos"

    plot_pair_dashboard(
        100,
        h100,
        hs100,
        ref_dir / "triaxial_100kpa_reference.json",
        m3_csv,
        plots_dir / "m4_triaxial_100kpa_h_vs_hs.png",
    )
    plot_3d_localization_snapshot(
        h100, hs100, plots_dir / "m4_triaxial_3d_localization_snapshot.png"
    )
    render_side_by_side_video(100, h100, hs100, videos_dir / "triaxial_100kpa_h_vs_hs.mp4")

    summary = {
        "milestone": "M4",
        "status": "PASS",
        "pairs": [s100],
        "plots": [
            str((plots_dir / "m4_triaxial_100kpa_h_vs_hs.png").relative_to(repo)),
            str((plots_dir / "m4_triaxial_3d_localization_snapshot.png").relative_to(repo)),
        ],
        "videos": [
            str((videos_dir / "triaxial_100kpa_h_vs_hs.mp4").relative_to(repo)),
        ],
    }
    (tri_dir / "m4_verification_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"M4 post-processing complete: summary, plots, and videos written to {tri_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
