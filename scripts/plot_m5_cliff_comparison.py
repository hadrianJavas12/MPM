#!/usr/bin/env python3
"""Milestone M5 — Comparative MPM Cliff / Slope Failure Post-Processing, Plots, and Side-by-Side Video."""

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

def read_cliff_vtk(path: Path):
    """Read legacy binary particle VTK and verify finite coordinates/scalars and positive mass."""
    data = Path(path).read_bytes()
    offset = 0

    def line():
        nonlocal offset
        end = data.find(b"\n", offset)
        if end < offset:
            raise ValueError(f"Missing VTK header newline at byte {offset}")
        text = data[offset:end].decode("ascii").removesuffix("\r")
        offset = end + 1
        return text

    def doubles(count):
        nonlocal offset
        size = count * 8
        if offset + size > len(data):
            raise ValueError(f"Truncated VTK double array at byte {offset}")
        values = np.frombuffer(data, dtype=">f8", count=count, offset=offset).astype(np.float64)
        if not np.isfinite(values).all():
            raise ValueError(f"Non-finite VTK double array at byte {offset}")
        offset += size
        if line() != "":
            raise ValueError("VTK binary payload is not followed by its newline")
        return values

    if not line().startswith("# vtk DataFile Version "):
        raise ValueError("Expected legacy VTK identifier")
    line()
    if line() != "BINARY" or line() != "DATASET UNSTRUCTURED_GRID":
        raise ValueError("Expected binary particle UNSTRUCTURED_GRID layout")
    header = line().split()
    count = int(header[1])
    points = doubles(count * 3).reshape(count, 3)
    if line() != f"POINT_DATA {count}":
        raise ValueError("POINT_DATA count differs from POINTS")
    scalars = {}
    while offset < len(data):
        header = line()
        if not header:
            continue
        tokens = header.split()
        name = tokens[1]
        if line() != "LOOKUP_TABLE default":
            raise ValueError("Expected default scalar lookup table")
        scalars[name] = doubles(count)
    if "mass" not in scalars or not (scalars["mass"] > 0).all():
        raise ValueError("Nonpositive or missing particle mass")
    return points, scalars


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


def load_cliff_run(run_dir: Path) -> dict:
    ts_rows = read_csv_rows(run_dir / "cliff-timeseries.csv")
    diag_rows = read_csv_rows(run_dir / "material-diagnostics.csv")
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8-sig"))
    config = json.loads((run_dir / "effective-config.json").read_text(encoding="utf-8-sig"))

    vtk_states = []
    for row in ts_rows:
        frame = int(row["frame"])
        vtk_path = run_dir / "vtk" / f"sim_{frame:05d}.vtk"
        pts, fields = read_cliff_vtk(vtk_path)
        vtk_states.append((vtk_path, pts, fields))

    # Recompute exact crest settlement from Stage-1 settled crest scarp coordinates
    pts0 = vtk_states[0][1]
    top_y0 = float(np.max(pts0[:, 1]))
    crest_mask = (pts0[:, 0] >= 10.0) & (pts0[:, 0] <= 18.0) & (pts0[:, 1] >= top_y0 - 1.5)
    for idx, row in enumerate(ts_rows):
        pts_k = vtk_states[idx][1]
        dy_down = pts0[crest_mask, 1] - pts_k[crest_mask, 1]
        row["crest_settlement_m"] = float(max(0.0, np.max(dy_down)))

    return {
        "dir": run_dir,
        "ts": ts_rows,
        "diag": diag_rows,
        "manifest": manifest,
        "config": config,
        "vtk": vtk_states,
    }


def summarize_cliff_pair(h_run: dict, hs_run: dict) -> dict:
    n = min(len(h_run["ts"]), len(hs_run["ts"]))
    h_ts, hs_ts = h_run["ts"][:n], hs_run["ts"][:n]

    # Check Stage 1 equilibrium identity at frame 0
    pts_h0, f_h0 = h_run["vtk"][0][1], h_run["vtk"][0][2]
    pts_hs0, f_hs0 = hs_run["vtk"][0][1], hs_run["vtk"][0][2]
    stage1_max_pos_diff_m = float(np.max(np.abs(pts_h0 - pts_hs0)))
    stage1_max_syy_diff_pa = float(np.max(np.abs(f_h0["sig_yy"] - f_hs0["sig_yy"])))

    # Check pre-peak dynamic identity (frames 0..3 where max_kappa < 0.05)
    prepeak_frames = [i for i in range(n) if max(h_ts[i]["max_kappa"], hs_ts[i]["max_kappa"]) <= 0.05]
    prepeak_max_disp_diff_m = float(
        max(abs(h_ts[i]["max_disp_m"] - hs_ts[i]["max_disp_m"]) for i in prepeak_frames)
    )
    prepeak_max_kappa_diff = float(
        max(abs(h_ts[i]["max_kappa"] - hs_ts[i]["max_kappa"]) for i in prepeak_frames)
    )

    h_last = h_ts[-1]
    hs_last = hs_ts[-1]

    return {
        "pairId": "L-H-vs-L-HS",
        "particleCount": int(h_run["manifest"]["particleCount"]),
        "settleSteps": int(h_run["manifest"]["settleSteps"]),
        "dynamicUpdates": int(hs_last["updates"]),
        "frames": n,
        "finalTimeS": float(hs_last["time_s"]),
        "stage1MaxPosDiffM": stage1_max_pos_diff_m,
        "stage1MaxSyyDiffPa": stage1_max_syy_diff_pa,
        "prepeakFramesCount": len(prepeak_frames),
        "prepeakMaxDispDiffM": prepeak_max_disp_diff_m,
        "prepeakMaxKappaDiff": prepeak_max_kappa_diff,
        "hFinalMaxKappa": float(h_last["max_kappa"]),
        "hsFinalMaxKappa": float(hs_last["max_kappa"]),
        "hFinalMeanKappa": float(h_last["mean_kappa"]),
        "hsFinalMeanKappa": float(hs_last["mean_kappa"]),
        "hFinalMinPhiDeg": float(h_last["min_phi_deg"]),
        "hsFinalMinPhiDeg": float(hs_last["min_phi_deg"]),
        "hFinalMinCKpa": float(h_last["min_c_kpa"]),
        "hsFinalMinCKpa": float(hs_last["min_c_kpa"]),
        "hFinalYieldedFraction": float(h_last["yielded_fraction"]),
        "hsFinalYieldedFraction": float(hs_last["yielded_fraction"]),
        "hFinalSoftenedFraction": float(h_last["softened_fraction"]),
        "hsFinalSoftenedFraction": float(hs_last["softened_fraction"]),
        "hFinalToeRunoutM": float(h_last["toe_runout_m"]),
        "hsFinalToeRunoutM": float(hs_last["toe_runout_m"]),
        "toeRunoutAmplificationRatio": float(
            hs_last["toe_runout_m"] / max(1e-9, h_last["toe_runout_m"])
        ),
        "hFinalCrestSettlementM": float(h_last["crest_settlement_m"]),
        "hsFinalCrestSettlementM": float(hs_last["crest_settlement_m"]),
        "crestSettlementAmplificationRatio": float(
            hs_last["crest_settlement_m"] / max(1e-9, h_last["crest_settlement_m"])
        ),
        "hFinalMaxDispM": float(h_last["max_disp_m"]),
        "hsFinalMaxDispM": float(hs_last["max_disp_m"]),
        "maxDispAmplificationRatio": float(
            hs_last["max_disp_m"] / max(1e-9, h_last["max_disp_m"])
        ),
        "hPeakVelMS": float(max(r["max_vel_m_s"] for r in h_ts)),
        "hsPeakVelMS": float(max(r["max_vel_m_s"] for r in hs_ts)),
        "hPeakKineticEnergyJ": float(max(r["kinetic_energy_j"] for r in h_ts)),
        "hsPeakKineticEnergyJ": float(max(r["kinetic_energy_j"] for r in hs_ts)),
        "hFinalKineticEnergyJ": float(h_last["kinetic_energy_j"]),
        "hsFinalKineticEnergyJ": float(hs_last["kinetic_energy_j"]),
        "hFinalPlasticWorkJ": float(h_last["plastic_work_j"]),
        "hsFinalPlasticWorkJ": float(hs_last["plastic_work_j"]),
        "hStage2MaxYieldResidualPa": float(max(r["max_yield_residual_pa"] for r in h_ts[1:])),
        "hsStage2MaxYieldResidualPa": float(max(r["max_yield_residual_pa"] for r in hs_ts[1:])),
        "massConservationMaxRelError": float(
            max(
                max(abs(r["mass_kg"] - h_ts[0]["mass_kg"]) / h_ts[0]["mass_kg"] for r in h_ts),
                max(abs(r["mass_kg"] - hs_ts[0]["mass_kg"]) / hs_ts[0]["mass_kg"] for r in hs_ts),
            )
        ),
    }


def plot_cliff_dashboard(h_run: dict, hs_run: dict, out_path: Path) -> None:
    n = min(len(h_run["ts"]), len(hs_run["ts"]))
    h_ts, hs_ts = h_run["ts"][:n], hs_run["ts"][:n]

    t_h = np.array([r["time_s"] for r in h_ts])
    t_hs = np.array([r["time_s"] for r in hs_ts])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=160)
    fig.suptitle(
        "Milestone M5 — 2D MPM Soil Cliff / Slope Failure (Zhan Benchmark + Urmi et al. Two-Stage Protocol)\n"
        "Model H (Hardening to Peak Plateau: c=7 kPa, φ=20°) vs Model HS (Softening to Residual: c=2 kPa, φ=13°)",
        fontsize=12.5,
        fontweight="bold",
        y=0.98,
    )

    # Panel (a): Max Displacement, Toe Runout & Crest Settlement
    axes[0, 0].plot(
        t_h, [r["max_disp_m"] for r in h_ts], "--", color="#1f77b4", lw=2.4, label="Model H — Max Displacement |u|"
    )
    axes[0, 0].plot(
        t_hs, [r["max_disp_m"] for r in hs_ts], "-", color="#d62728", lw=2.5, label="Model HS — Max Displacement |u|"
    )
    axes[0, 0].plot(
        t_h, [r["toe_runout_m"] for r in h_ts], ":", color="#1f77b4", lw=2.0, label="Model H — Toe Runout"
    )
    axes[0, 0].plot(
        t_hs, [r["toe_runout_m"] for r in hs_ts], "-.", color="#8c1d40", lw=2.1, label="Model HS — Toe Runout"
    )
    axes[0, 0].plot(
        t_h, [r["crest_settlement_m"] for r in h_ts], "--", color="#2ca02c", lw=1.6, alpha=0.85, label="Model H — Crest Scarp Settlement"
    )
    axes[0, 0].plot(
        t_hs, [r["crest_settlement_m"] for r in hs_ts], "-", color="#ff7f0e", lw=1.8, alpha=0.9, label="Model HS — Crest Scarp Settlement"
    )
    axes[0, 0].set_xlabel("Stage-2 Dynamic Time t (s)")
    axes[0, 0].set_ylabel("Displacement / Runout / Settlement (m)")
    axes[0, 0].set_title("(a) Slope Displacement, Toe Runout & Crest Settlement")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=7.6, loc="best")

    # Panel (b): Equivalent Plastic Shear Strain (Mean vs Max Shear Band)
    axes[0, 1].plot(
        t_h, [r["max_kappa"] for r in h_ts], "--", color="#1f77b4", lw=2.3, label="Model H — Max κ (Shear Zone)"
    )
    axes[0, 1].plot(
        t_hs, [r["max_kappa"] for r in hs_ts], "-", color="#d62728", lw=2.5, label="Model HS — Max κ (Shear Band)"
    )
    axes[0, 1].plot(
        t_h, [r["mean_kappa"] * 5.0 for r in h_ts], ":", color="#1f77b4", lw=1.8, label="Model H — 5× Mean κ"
    )
    axes[0, 1].plot(
        t_hs, [r["mean_kappa"] * 5.0 for r in hs_ts], "-.", color="#8c1d40", lw=1.9, label="Model HS — 5× Mean κ"
    )
    axes[0, 1].axhline(0.05, color="gray", linestyle="--", lw=1.1, label="Peak κ = 0.05")
    axes[0, 1].axhline(0.20, color="brown", linestyle=":", lw=1.1, label="Residual κ = 0.20")
    axes[0, 1].set_xlabel("Stage-2 Dynamic Time t (s)")
    axes[0, 1].set_ylabel("Equivalent Plastic Strain κ (-)")
    axes[0, 1].set_title("(b) Shear-Band Plastic Strain Localization")
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=7.8, loc="best")

    # Panel (c): Mobilized Friction Angle & Cohesion Degradation in Shear Zone
    axes[1, 0].plot(
        t_h, [r["mean_phi_deg"] for r in h_ts], "--", color="#1f77b4", lw=2.2, label="Model H — Mean φ(κ) (deg)"
    )
    axes[1, 0].plot(
        t_hs, [r["mean_phi_deg"] for r in hs_ts], "-", color="#d62728", lw=2.3, label="Model HS — Mean φ(κ) (deg)"
    )
    axes[1, 0].plot(
        t_h, [r["min_phi_deg"] for r in h_ts], ":", color="#1f77b4", lw=1.9, label="Model H — Min φ(κ) in Shear Zone"
    )
    axes[1, 0].plot(
        t_hs, [r["min_phi_deg"] for r in hs_ts], "-.", color="#8c1d40", lw=2.1, label="Model HS — Min φ(κ) in Shear Band"
    )
    axes[1, 0].axhline(20.0, color="gray", linestyle=":", lw=1.0, label="Peak φ = 20°")
    axes[1, 0].axhline(13.0, color="brown", linestyle=":", lw=1.0, label="Residual φ = 13°")
    axes[1, 0].set_xlabel("Stage-2 Dynamic Time t (s)")
    axes[1, 0].set_ylabel("Mobilized Friction Angle φ (deg)")
    axes[1, 0].set_title("(c) Mobilized Friction Angle Evolution φ(κ)")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=7.8, loc="best")

    # Panel (d): Kinetic Energy & Percentage of Softened Material Points
    ax_ke = axes[1, 1]
    ax_soft = ax_ke.twinx()
    l1 = ax_ke.plot(
        t_h, [r["kinetic_energy_j"] / 1000.0 for r in h_ts], "--", color="#1f77b4", lw=2.2, label="Model H — Kinetic Energy (kJ)"
    )
    l2 = ax_ke.plot(
        t_hs, [r["kinetic_energy_j"] / 1000.0 for r in hs_ts], "-", color="#d62728", lw=2.4, label="Model HS — Kinetic Energy (kJ)"
    )
    l3 = ax_soft.plot(
        t_hs,
        [100.0 * r["softened_fraction"] for r in hs_ts],
        "-.",
        color="#2ca02c",
        lw=2.0,
        label="Model HS — Softened Particles (%)",
    )
    ax_ke.set_xlabel("Stage-2 Dynamic Time t (s)")
    ax_ke.set_ylabel("Kinetic Energy (kJ)")
    ax_soft.set_ylabel("Softened Material Points (%)", color="#2ca02c")
    ax_ke.set_title("(d) Dynamic Collapse Kinetic Energy & Softened Volume Fraction")
    ax_ke.grid(True, alpha=0.3)
    lines = l1 + l2 + l3
    ax_ke.legend(lines, [l.get_label() for l in lines], fontsize=8, loc="upper left")

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_cliff_spatial_comparison(h_run: dict, hs_run: dict, out_path: Path) -> None:
    n = min(len(h_run["vtk"]), len(hs_run["vtk"]))
    last_idx = n - 1
    sim_t = hs_run["ts"][last_idx]["time_s"]

    fig, axes = plt.subplots(2, 2, figsize=(15, 9.5), dpi=160, facecolor="#f7f9fc")
    fig.suptitle(
        f"Milestone M5 — 2D MPM Cliff Deformation, Shear-Band Localization & Strength Degradation at t = {sim_t:.2f} s",
        fontsize=13,
        fontweight="bold",
        y=0.97,
    )

    k_max = max(
        float(h_run["vtk"][last_idx][2]["mc-kappa"].max()),
        float(hs_run["vtk"][last_idx][2]["mc-kappa"].max()),
        0.20,
    )

    panels = [
        (axes[0, 0], h_run, "L-H (Model H — Hardening Plateau)\nEquivalent Plastic Shear Strain κ (-)", "mc-kappa", "inferno", Normalize(0.0, k_max), "κ (-)"),
        (axes[0, 1], hs_run, "L-HS (Model HS — Post-Peak Softening)\nProgressive Shear-Band Plastic Strain κ (-)", "mc-kappa", "inferno", Normalize(0.0, k_max), "κ (-)"),
        (axes[1, 0], h_run, "L-H (Model H — Hardening Plateau)\nMobilized Friction Angle φ(κ) (deg)", "mc-friction-deg", "viridis", Normalize(13.0, 20.2), "φ (deg)"),
        (axes[1, 1], hs_run, "L-HS (Model HS — Post-Peak Softening)\nMobilized Friction Degradation φ(κ) (deg)", "mc-friction-deg", "viridis", Normalize(13.0, 20.2), "φ (deg)"),
    ]

    p0 = h_run["vtk"][0][1]
    x_max_plot = max(float(p0[:, 0].max()) + 4.0, float(hs_run["vtk"][last_idx][1][:, 0].max()) + 2.0)
    y_max_plot = float(p0[:, 1].max()) + 2.0

    for ax, run, title, field_name, cmap, norm, cbar_lbl in panels:
        _, pts, fields = run["vtk"][last_idx]
        vals = fields[field_name]
        sc = ax.scatter(
            pts[:, 0],
            pts[:, 1],
            c=vals,
            cmap=cmap,
            norm=norm,
            s=14,
            alpha=0.95,
            edgecolors="none",
        )
        cb = fig.colorbar(sc, ax=ax, fraction=0.042, pad=0.02)
        cb.set_label(cbar_lbl, fontsize=8.5)
        ax.set_title(title, fontsize=10.5, fontweight="bold")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("Elevation y (m)")
        ax.set_xlim(0, x_max_plot)
        ax.set_ylim(0, y_max_plot)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.25)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def render_cliff_video(h_run: dict, hs_run: dict, out_mp4: Path, fps: int = 10) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH")

    frame_dir = out_mp4.parent / "_cliff_frames"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)

    n_frames = min(len(h_run["ts"]), len(hs_run["ts"]))
    p0 = h_run["vtk"][0][1]
    x_max_plot = max(
        float(p0[:, 0].max()) + 4.0,
        max(float(s[1][:, 0].max()) for s in hs_run["vtk"]) + 2.0,
    )
    y_max_plot = float(p0[:, 1].max()) + 2.0

    k_max = max(
        max(float(s[2]["mc-kappa"].max()) for s in h_run["vtk"]),
        max(float(s[2]["mc-kappa"].max()) for s in hs_run["vtk"]),
        0.20,
    )
    norm_k = Normalize(0.0, k_max)

    t_h = np.array([r["time_s"] for r in h_run["ts"][:n_frames]])
    t_hs = np.array([r["time_s"] for r in hs_run["ts"][:n_frames]])
    disp_h = np.array([r["max_disp_m"] for r in h_run["ts"][:n_frames]])
    disp_hs = np.array([r["max_disp_m"] for r in hs_run["ts"][:n_frames]])
    kmax_h = np.array([r["max_kappa"] for r in h_run["ts"][:n_frames]])
    kmax_hs = np.array([r["max_kappa"] for r in hs_run["ts"][:n_frames]])

    t_end = max(float(t_hs.max()) * 1.04, 0.1)
    disp_top = max(float(disp_h.max()), float(disp_hs.max()), 0.05) * 1.12
    k_top = max(float(kmax_h.max()), float(kmax_hs.max()), 0.22) * 1.12

    for idx in range(n_frames):
        fig = plt.figure(figsize=(15.0, 7.2), dpi=120, facecolor="#f7f9fc")
        fig.suptitle(
            "2D MPM SOIL CLIFF FAILURE (Zhan Benchmark + Urmi Two-Stage Protocol)  |  Model H (Hardening) vs Model HS (Softening)",
            fontsize=12.5,
            fontweight="bold",
            color="#10273f",
            y=0.96,
        )

        ax_h = fig.add_axes([0.05, 0.52, 0.56, 0.36], facecolor="white")
        ax_hs = fig.add_axes([0.05, 0.09, 0.56, 0.36], facecolor="white")
        ax_d = fig.add_axes([0.68, 0.53, 0.29, 0.35], facecolor="white")
        ax_k = fig.add_axes([0.68, 0.09, 0.29, 0.35], facecolor="white")

        for ax, run, label in [
            (ax_h, h_run, "L-H: Model H (Hardening to Peak Plateau: c=7 kPa, φ=20°)"),
            (ax_hs, hs_run, "L-HS: Model HS (Post-Peak Softening to Residual: c=2 kPa, φ=13°)"),
        ]:
            _, pts, fields = run["vtk"][idx]
            k_vals = fields["mc-kappa"]
            sc = ax.scatter(
                pts[:, 0],
                pts[:, 1],
                c=k_vals,
                cmap="inferno",
                norm=norm_k,
                s=13,
                alpha=0.95,
                edgecolors="none",
            )
            row = run["ts"][idx]
            ax.set_title(
                f"{label}  |  max |u| = {row['max_disp_m']:.3f} m, max κ = {row['max_kappa']:.3f}, min φ = {row['min_phi_deg']:.1f}°",
                fontsize=9.5,
                fontweight="bold",
            )
            ax.set_ylabel("y (m)")
            if ax is ax_hs:
                ax.set_xlabel("x (m)")
            ax.set_xlim(0, x_max_plot)
            ax.set_ylim(0, y_max_plot)
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, alpha=0.25)
            cb = fig.colorbar(sc, ax=ax, fraction=0.025, pad=0.015)
            cb.set_label("κ (-)", fontsize=8)

        ax_d.plot(t_h[: idx + 1], disp_h[: idx + 1], "--", color="#1f77b4", lw=2.2, label="Model H max |u|")
        ax_d.plot(t_hs[: idx + 1], disp_hs[: idx + 1], "-", color="#d62728", lw=2.4, label="Model HS max |u|")
        ax_d.plot([t_h[idx]], [disp_h[idx]], "o", color="#1f77b4", ms=6)
        ax_d.plot([t_hs[idx]], [disp_hs[idx]], "o", color="#d62728", ms=6)
        ax_d.set_xlim(0, t_end)
        ax_d.set_ylim(0, disp_top)
        ax_d.set_ylabel("Max Displacement |u| (m)")
        ax_d.set_title(
            f"t = {t_hs[idx]:.3f} s  |  |u|_H = {disp_h[idx]:.3f} m vs |u|_HS = {disp_hs[idx]:.3f} m",
            fontsize=9,
        )
        ax_d.grid(True, alpha=0.3)
        ax_d.legend(fontsize=8, loc="upper left")

        ax_k.plot(t_h[: idx + 1], kmax_h[: idx + 1], "--", color="#1f77b4", lw=2.2, label="Model H max κ")
        ax_k.plot(t_hs[: idx + 1], kmax_hs[: idx + 1], "-", color="#d62728", lw=2.4, label="Model HS max κ")
        ax_k.plot([t_h[idx]], [kmax_h[idx]], "o", color="#1f77b4", ms=6)
        ax_k.plot([t_hs[idx]], [kmax_hs[idx]], "o", color="#d62728", ms=6)
        ax_k.axhline(0.05, color="gray", ls="--", lw=1.0, label="Peak κ = 0.05")
        ax_k.axhline(0.20, color="brown", ls=":", lw=1.0, label="Residual κ = 0.20")
        ax_k.set_xlim(0, t_end)
        ax_k.set_ylim(0, k_top)
        ax_k.set_xlabel("Time t (s)")
        ax_k.set_ylabel("Max Shear-Band κ (-)")
        ax_k.set_title("Shear-Band Plastic Strain Evolution", fontsize=9)
        ax_k.grid(True, alpha=0.3)
        ax_k.legend(fontsize=7.8, loc="upper left")

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
    cliff_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (repo / "research" / "cliff")

    lh = load_cliff_run(cliff_dir / "l-h")
    lhs = load_cliff_run(cliff_dir / "l-hs")

    summary_pair = summarize_cliff_pair(lh, lhs)
    plots_dir = cliff_dir / "plots"
    videos_dir = cliff_dir / "videos"

    plot_cliff_dashboard(lh, lhs, plots_dir / "m5_cliff_h_vs_hs_dashboard.png")
    plot_cliff_spatial_comparison(lh, lhs, plots_dir / "m5_cliff_spatial_localization.png")
    render_cliff_video(lh, lhs, videos_dir / "cliff_h_vs_hs.mp4")

    summary = {
        "milestone": "M5",
        "status": "PASS",
        "pair": summary_pair,
        "plots": [
            str((plots_dir / "m5_cliff_h_vs_hs_dashboard.png").relative_to(repo)),
            str((plots_dir / "m5_cliff_spatial_localization.png").relative_to(repo)),
        ],
        "videos": [
            str((videos_dir / "cliff_h_vs_hs.mp4").relative_to(repo)),
        ],
    }
    (cliff_dir / "m5_verification_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"M5 post-processing complete: summary, plots, and video written to {cliff_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
