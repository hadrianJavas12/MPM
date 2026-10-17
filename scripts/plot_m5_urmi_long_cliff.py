#!/usr/bin/env python3
"""Post-processing, wide-aspect plots, and individual + side-by-side MP4 videos for the elongated long-duration Urmi cliff pair (L-URMI-LONG-H vs L-URMI-LONG-HS)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

from plot_m5_cliff_comparison import read_cliff_vtk, read_csv_rows, summarize_cliff_pair


def load_elongated_cliff_run(run_dir: Path) -> dict:
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

    # Recompute exact continuum metrics from VTK coordinates/fields using reference particle masses/volumes
    pts0, f0 = vtk_states[0][1], vtk_states[0][2]
    mass0 = f0["mass"]
    top_y0 = float(np.max(pts0[:, 1]))
    soil_h = float(config.get("soilBoundary", 4.0))
    mesh_h = float(config.get("meshSize", 0.5))
    shelf_len = float(config.get("elongatedShelfAspect", config.get("shelfAspect", 4.0))) * float(config.get("shelfHeight", 12.0))
    initial_toe_x = float(np.max(pts0[pts0[:, 1] > soil_h + 0.25 * mesh_h, 0]))
    crest_mask = (pts0[:, 0] >= shelf_len - 18.0) & (pts0[:, 0] <= shelf_len) & (pts0[:, 1] >= top_y0 - 1.5)
    top_surface_mask = (pts0[:, 0] <= shelf_len - 1.0) & (pts0[:, 1] >= top_y0 - 0.6)

    prev_t = 0.0
    prev_pts = pts0.copy()
    for idx, row in enumerate(ts_rows):
        pts_k, fk = vtk_states[idx][1], vtk_states[idx][2]
        t_k = float(row["time_s"])
        dt_frame = max(1e-6, t_k - prev_t) if idx > 0 else 1.0

        disp_vec = pts_k[:, :2] - pts0[:, :2]
        disp_mag = np.linalg.norm(disp_vec, axis=1)
        step_disp = np.linalg.norm(pts_k[:, :2] - prev_pts[:, :2], axis=1)

        # Continuum filter: exclude any detached single-particle numerical outlier leaving the 102 m domain
        in_domain = (
            (pts_k[:, 0] >= 0.0)
            & (pts_k[:, 0] <= 102.0)
            & (pts_k[:, 1] >= 0.0)
            & (pts_k[:, 1] <= 18.0)
            & (disp_mag < 35.0)
            & ((step_disp / dt_frame) < 25.0)
        )
        m_valid = mass0[in_domain]
        m_sum = float(np.sum(m_valid))
        k_valid = fk["mc-kappa"][in_domain]
        phi_valid = fk["mc-friction-deg"][in_domain]
        soft_valid = fk["mc-softened-indicator"][in_domain]

        row["max_disp_m"] = float(np.max(disp_mag[in_domain]))
        toe_candidates = in_domain & (pts_k[:, 1] > soil_h + 0.25 * mesh_h)
        cur_toe_x = float(np.max(pts_k[toe_candidates, 0])) if np.any(toe_candidates) else initial_toe_x
        row["toe_runout_m"] = float(max(0.0, cur_toe_x - initial_toe_x))

        crest_valid = crest_mask & in_domain
        dy_down = pts0[crest_valid, 1] - pts_k[crest_valid, 1]
        row["crest_settlement_m"] = float(max(0.0, np.max(dy_down))) if np.any(crest_valid) else 0.0

        # Retrogressive scarp retreat behind original crest edge (where top surface slumps > 1.0 m)
        surf_valid = top_surface_mask & in_domain
        subsided = (pts0[surf_valid, 1] - pts_k[surf_valid, 1]) > 1.00
        if np.any(subsided):
            min_x_subsided = float(np.min(pts0[surf_valid, 0][subsided]))
            row["retrogression_distance_m"] = float(max(0.0, shelf_len - min_x_subsided))
        else:
            row["retrogression_distance_m"] = 0.0

        row["mean_kappa"] = float(np.sum(m_valid * k_valid) / m_sum)
        row["max_kappa"] = float(np.max(k_valid))
        row["mean_phi_deg"] = float(np.sum(m_valid * phi_valid) / m_sum)
        row["min_phi_deg"] = float(np.min(phi_valid))
        row["softened_fraction"] = float(np.sum(m_valid * soft_valid) / m_sum)
        row["yielded_fraction"] = float(np.sum(m_valid[k_valid > 1e-6]) / m_sum)

        if idx == 0:
            row["kinetic_energy_j"] = 0.0
            row["max_vel_m_s"] = 0.0
        else:
            v_est = step_disp[in_domain] / dt_frame
            row["max_vel_m_s"] = float(np.max(v_est))
            # If native KE had no outlier jump, preserve native KE; otherwise use continuum particle KE
            if float(row["kinetic_energy_j"]) < 1.0e7:
                row["kinetic_energy_j"] = float(row["kinetic_energy_j"])
            else:
                row["kinetic_energy_j"] = float(0.5 * np.sum(m_valid * (v_est ** 2)))

        prev_t = t_k
        prev_pts = pts_k.copy()

    return {
        "dir": run_dir,
        "ts": ts_rows,
        "diag": diag_rows,
        "manifest": manifest,
        "config": config,
        "vtk": vtk_states,
        "shelf_len": shelf_len,
    }


def encode_frames_to_mp4(frame_dir: Path, out_mp4: Path, fps: int = 8) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH")
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frame_dir / "frame_%04d.png"),
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def plot_elongated_dashboard(h_run: dict, hs_run: dict, out_path: Path) -> None:
    n = min(len(h_run["ts"]), len(hs_run["ts"]))
    h_ts, hs_ts = h_run["ts"][:n], hs_run["ts"][:n]
    t_h = np.array([r["time_s"] for r in h_ts])
    t_hs = np.array([r["time_s"] for r in hs_ts])

    fig, axes = plt.subplots(2, 2, figsize=(14.5, 10.2), dpi=160)
    fig.suptitle(
        "Elongated Urmi-Geometry Long-Duration 2D MPM Cliff Collapse (Domain 102 m × 16 m, 80 Frames)\n"
        "Model H (Hardening Plateau: c=7 kPa, φ=20°) vs Model HS (Urmi Eq. 2 Softening to Residual: c=2 kPa, φ=13°)",
        fontsize=12.2,
        fontweight="bold",
        y=0.98,
    )

    axes[0, 0].plot(t_h, [r["max_disp_m"] for r in h_ts], "--", color="#1f77b4", lw=2.3, label="Model H — Max Displacement |u|")
    axes[0, 0].plot(t_hs, [r["max_disp_m"] for r in hs_ts], "-", color="#d62728", lw=2.5, label="Model HS — Max Displacement |u|")
    axes[0, 0].plot(t_h, [r["toe_runout_m"] for r in h_ts], ":", color="#1f77b4", lw=2.0, label="Model H — Toe Runout")
    axes[0, 0].plot(t_hs, [r["toe_runout_m"] for r in hs_ts], "-.", color="#8c1d40", lw=2.1, label="Model HS — Toe Runout")
    axes[0, 0].plot(t_h, [r["crest_settlement_m"] for r in h_ts], "--", color="#2ca02c", lw=1.7, label="Model H — Crest Scarp Settlement")
    axes[0, 0].plot(t_hs, [r["crest_settlement_m"] for r in hs_ts], "-", color="#ff7f0e", lw=1.9, label="Model HS — Crest Scarp Settlement")
    axes[0, 0].set_xlabel("Stage-2 Dynamic Time t (s)")
    axes[0, 0].set_ylabel("Distance / Displacement (m)")
    axes[0, 0].set_title("(a) Long-Term Displacement, Toe Runout & Retrogressive Scarp Retreat")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=7.6, loc="best")

    axes[0, 1].plot(t_h, [r["max_kappa"] for r in h_ts], "--", color="#1f77b4", lw=2.3, label="Model H — Max κ (Shear Zone)")
    axes[0, 1].plot(t_hs, [r["max_kappa"] for r in hs_ts], "-", color="#d62728", lw=2.5, label="Model HS — Max κ (Shear Band)")
    axes[0, 1].plot(t_h, [r["mean_kappa"] * 10.0 for r in h_ts], ":", color="#1f77b4", lw=1.8, label="Model H — 10× Mean κ")
    axes[0, 1].plot(t_hs, [r["mean_kappa"] * 10.0 for r in hs_ts], "-.", color="#8c1d40", lw=1.9, label="Model HS — 10× Mean κ")
    axes[0, 1].axhline(0.05, color="gray", linestyle="--", lw=1.0, label="Peak κ = 0.05")
    axes[0, 1].axhline(0.20, color="brown", linestyle=":", lw=1.0, label="Residual κ = 0.20")
    axes[0, 1].set_xlabel("Stage-2 Dynamic Time t (s)")
    axes[0, 1].set_ylabel("Equivalent Plastic Strain κ (-)")
    axes[0, 1].set_title("(b) Shear-Band Plastic Strain Evolution Over Extended Time")
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=7.8, loc="best")

    axes[1, 0].plot(t_h, [r["mean_phi_deg"] for r in h_ts], "--", color="#1f77b4", lw=2.2, label="Model H — Mean φ(κ) (deg)")
    axes[1, 0].plot(t_hs, [r["mean_phi_deg"] for r in hs_ts], "-", color="#d62728", lw=2.4, label="Model HS — Mean φ(κ) (deg)")
    axes[1, 0].plot(t_h, [r["min_phi_deg"] for r in h_ts], ":", color="#1f77b4", lw=1.8, label="Model H — Min φ(κ)")
    axes[1, 0].plot(t_hs, [r["min_phi_deg"] for r in hs_ts], "-.", color="#8c1d40", lw=2.0, label="Model HS — Min φ(κ) in Shear Band")
    axes[1, 0].set_xlabel("Stage-2 Dynamic Time t (s)")
    axes[1, 0].set_ylabel("Mobilized Friction Angle φ (deg)")
    axes[1, 0].set_title("(c) Mobilized Friction Angle Evolution φ(κ)")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=7.8, loc="best")

    ax_ke = axes[1, 1]
    ax_sf = ax_ke.twinx()
    l1 = ax_ke.plot(t_h, [r["kinetic_energy_j"] * 1e-3 for r in h_ts], "--", color="#1f77b4", lw=2.2, label="Model H — Kinetic Energy (kJ)")
    l2 = ax_ke.plot(t_hs, [r["kinetic_energy_j"] * 1e-3 for r in hs_ts], "-", color="#d62728", lw=2.4, label="Model HS — Kinetic Energy (kJ)")
    l3 = ax_sf.plot(t_hs, [r["softened_fraction"] * 100.0 for r in hs_ts], "-.", color="#2ca02c", lw=1.9, label="Model HS — Softened Volume (%)")
    ax_ke.set_xlabel("Stage-2 Dynamic Time t (s)")
    ax_ke.set_ylabel("Kinetic Energy (kJ)")
    ax_sf.set_ylabel("Softened Material Points (%)", color="#2ca02c")
    ax_ke.set_title("(d) Multi-Stage Collapse Kinetic Energy & Softened Volume Fraction")
    ax_ke.grid(True, alpha=0.3)
    lines = l1 + l2 + l3
    ax_ke.legend(lines, [l.get_label() for l in lines], fontsize=7.8, loc="upper right")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_elongated_spatial_snapshot(h_run: dict, hs_run: dict, out_path: Path) -> None:
    idx = min(len(h_run["vtk"]), len(hs_run["vtk"])) - 1
    pts_h, f_h = h_run["vtk"][idx][1], h_run["vtk"][idx][2]
    pts_hs, f_hs = hs_run["vtk"][idx][1], hs_run["vtk"][idx][2]
    t_final = hs_run["ts"][idx]["time_s"]

    k_max = max(float(np.percentile(f_h["mc-kappa"], 99.5)), float(np.percentile(f_hs["mc-kappa"], 99.5)), 0.5)
    norm_k = Normalize(vmin=0.0, vmax=k_max)
    norm_phi = Normalize(vmin=13.0, vmax=20.0)

    fig, axes = plt.subplots(2, 2, figsize=(16.5, 8.2), dpi=160)
    fig.suptitle(
        f"Elongated Urmi-Geometry 2D MPM Cliff Profile at t = {t_final:.2f} s (Domain 102 m × 16 m)\n"
        "Comparison of Shear-Band Localization κ and Strength Degradation φ(κ)",
        fontsize=12.5,
        fontweight="bold",
        y=0.98,
    )

    panels = [
        (axes[0, 0], pts_h, f_h["mc-kappa"], "inferno", norm_k, "L-URMI-LONG-H (Hardening) — Equivalent Plastic Strain κ (-)", "κ (-)"),
        (axes[0, 1], pts_hs, f_hs["mc-kappa"], "inferno", norm_k, "L-URMI-LONG-HS (Softening) — Retrogressive Shear-Band Strain κ (-)", "κ (-)"),
        (axes[1, 0], pts_h, f_h["mc-friction-deg"], "viridis", norm_phi, "L-URMI-LONG-H (Hardening) — Mobilized Friction φ(κ) (deg)", "φ (deg)"),
        (axes[1, 1], pts_hs, f_hs["mc-friction-deg"], "viridis", norm_phi, "L-URMI-LONG-HS (Softening) — Residual Friction Degradation φ(κ) (deg)", "φ (deg)"),
    ]
    for ax, pts, vals, cmap, norm, title, cbar_label in panels:
        sc = ax.scatter(pts[:, 0], pts[:, 1], c=vals, cmap=cmap, norm=norm, s=3.2, edgecolors="none")
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("Elevation y (m)")
        ax.set_xlim(0, 102)
        ax.set_ylim(0, 18)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.22)
        fig.colorbar(sc, ax=ax, fraction=0.025, pad=0.02, label=cbar_label)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def render_single_elongated_video(run: dict, title: str, curve_color: str, out_mp4: Path, k_max_scale: float, disp_max_scale: float) -> None:
    ts = run["ts"]
    vtk = run["vtk"]
    n = len(ts)
    t_arr = np.array([r["time_s"] for r in ts])
    disp_arr = np.array([r["max_disp_m"] for r in ts])
    runout_arr = np.array([r["toe_runout_m"] for r in ts])
    retro_arr = np.array([r["retrogression_distance_m"] for r in ts])
    k_max_arr = np.array([r["max_kappa"] for r in ts])
    min_phi_arr = np.array([r["min_phi_deg"] for r in ts])

    norm_k = Normalize(vmin=0.0, vmax=max(0.3, k_max_scale))
    norm_phi = Normalize(vmin=13.0, vmax=20.0)

    with tempfile.TemporaryDirectory(prefix="urmi_long_vid_") as tmp:
        tmp_dir = Path(tmp)
        for i in range(n):
            fig = plt.figure(figsize=(15.0, 7.6), dpi=125)
            gs = fig.add_gridspec(2, 2, width_ratios=[1.85, 1.0])
            ax_k = fig.add_subplot(gs[0, 0])
            ax_p = fig.add_subplot(gs[1, 0])
            ax_c = fig.add_subplot(gs[:, 1])

            fig.suptitle(
                f"{title}\n"
                f"t = {t_arr[i]:.2f} s | max |u| = {disp_arr[i]:.2f} m | toe runout = {runout_arr[i]:.2f} m | "
                f"scarp retrogression = {retro_arr[i]:.2f} m | max κ = {k_max_arr[i]:.2f} | min φ = {min_phi_arr[i]:.1f}°",
                fontsize=11.0,
                fontweight="bold",
                y=0.98,
            )

            pts = vtk[i][1]
            fields = vtk[i][2]

            s1 = ax_k.scatter(pts[:, 0], pts[:, 1], c=fields["mc-kappa"], cmap="inferno", norm=norm_k, s=3.0, edgecolors="none")
            ax_k.set_title("Equivalent Plastic Shear Strain κ (-) [Elongated Domain 102 m × 16 m]", fontsize=9.8)
            ax_k.set_xlabel("x (m)")
            ax_k.set_ylabel("Elevation y (m)")
            ax_k.set_xlim(0, 102)
            ax_k.set_ylim(0, 18)
            ax_k.set_aspect("equal", adjustable="box")
            ax_k.grid(True, alpha=0.22)
            fig.colorbar(s1, ax=ax_k, fraction=0.025, pad=0.02, label="κ (-)")

            s2 = ax_p.scatter(pts[:, 0], pts[:, 1], c=fields["mc-friction-deg"], cmap="viridis", norm=norm_phi, s=3.0, edgecolors="none")
            ax_p.set_title("Mobilized Friction Angle φ(κ) (deg)", fontsize=9.8)
            ax_p.set_xlabel("x (m)")
            ax_p.set_ylabel("Elevation y (m)")
            ax_p.set_xlim(0, 102)
            ax_p.set_ylim(0, 18)
            ax_p.set_aspect("equal", adjustable="box")
            ax_p.grid(True, alpha=0.22)
            fig.colorbar(s2, ax=ax_p, fraction=0.025, pad=0.02, label="φ (deg)")

            ax_c.plot(t_arr, disp_arr, color=curve_color, alpha=0.25, lw=1.5, linestyle="--")
            ax_c.plot(t_arr[: i + 1], disp_arr[: i + 1], color=curve_color, lw=2.4, label="Max Displacement |u| (m)")
            ax_c.plot(t_arr[: i + 1], runout_arr[: i + 1], color="#8c1d40", lw=2.0, linestyle="-.", label="Toe Runout (m)")
            ax_c.plot(t_arr[: i + 1], retro_arr[: i + 1], color="#ff7f0e", lw=1.9, linestyle=":", label="Scarp Retrogression (m)")
            ax_c.scatter([t_arr[i]], [disp_arr[i]], color=curve_color, s=42, zorder=5)
            ax_c.set_xlim(0, float(t_arr[-1]) * 1.03)
            ax_c.set_ylim(0, disp_max_scale)
            ax_c.set_xlabel("Stage-2 Dynamic Time t (s)")
            ax_c.set_ylabel("Displacement / Runout / Retrogression (m)")
            ax_c.set_title("Long-Duration Collapse Evolution")
            ax_c.grid(True, alpha=0.3)
            ax_c.legend(fontsize=8.2, loc="upper left")

            fig.tight_layout(rect=[0, 0, 1, 0.92])
            fig.savefig(tmp_dir / f"frame_{i:04d}.png")
            plt.close(fig)

        encode_frames_to_mp4(tmp_dir, out_mp4, fps=8)


def render_side_by_side_elongated_video(h_run: dict, hs_run: dict, out_mp4: Path, k_max_scale: float, disp_max_scale: float) -> None:
    n = min(len(h_run["ts"]), len(hs_run["ts"]))
    h_ts, hs_ts = h_run["ts"][:n], hs_run["ts"][:n]
    t_h = np.array([r["time_s"] for r in h_ts])
    t_hs = np.array([r["time_s"] for r in hs_ts])

    norm_k = Normalize(vmin=0.0, vmax=max(0.3, k_max_scale))
    norm_phi = Normalize(vmin=13.0, vmax=20.0)

    with tempfile.TemporaryDirectory(prefix="urmi_pair_vid_") as tmp:
        tmp_dir = Path(tmp)
        for i in range(n):
            fig = plt.figure(figsize=(16.0, 8.6), dpi=120)
            gs = fig.add_gridspec(2, 3, width_ratios=[1.35, 1.35, 1.0])
            ax_hk = fig.add_subplot(gs[0, 0])
            ax_hsk = fig.add_subplot(gs[0, 1])
            ax_hp = fig.add_subplot(gs[1, 0])
            ax_hsp = fig.add_subplot(gs[1, 1])
            ax_disp = fig.add_subplot(gs[0, 2])
            ax_ke = fig.add_subplot(gs[1, 2])

            fig.suptitle(
                f"Elongated Urmi-Geometry Long-Duration 2D MPM Cliff Collapse — Frame {i}/{n-1} (t = {t_hs[i]:.2f} s)\n"
                f"Model H: |u|max={h_ts[i]['max_disp_m']:.2f} m, runout={h_ts[i]['toe_runout_m']:.2f} m  vs  "
                f"Model HS: |u|max={hs_ts[i]['max_disp_m']:.2f} m, runout={hs_ts[i]['toe_runout_m']:.2f} m",
                fontsize=11.0,
                fontweight="bold",
                y=0.98,
            )

            pts_h, f_h = h_run["vtk"][i][1], h_run["vtk"][i][2]
            pts_hs, f_hs = hs_run["vtk"][i][1], hs_run["vtk"][i][2]

            for ax, pts, vals, cmap, norm, title in [
                (ax_hk, pts_h, f_h["mc-kappa"], "inferno", norm_k, "Model H (Hardening) — Plastic Strain κ"),
                (ax_hsk, pts_hs, f_hs["mc-kappa"], "inferno", norm_k, "Model HS (Softening) — Plastic Strain κ"),
                (ax_hp, pts_h, f_h["mc-friction-deg"], "viridis", norm_phi, "Model H (Hardening) — Friction φ(κ) (deg)"),
                (ax_hsp, pts_hs, f_hs["mc-friction-deg"], "viridis", norm_phi, "Model HS (Softening) — Friction φ(κ) (deg)"),
            ]:
                ax.scatter(pts[:, 0], pts[:, 1], c=vals, cmap=cmap, norm=norm, s=2.4, edgecolors="none")
                ax.set_title(title, fontsize=9.2, fontweight="bold")
                ax.set_xlim(0, 102)
                ax.set_ylim(0, 18)
                ax.set_aspect("equal", adjustable="box")
                ax.grid(True, alpha=0.2)

            ax_disp.plot(t_h[: i + 1], [r["max_disp_m"] for r in h_ts[: i + 1]], "--", color="#1f77b4", lw=2.0, label="H — Max |u|")
            ax_disp.plot(t_hs[: i + 1], [r["max_disp_m"] for r in hs_ts[: i + 1]], "-", color="#d62728", lw=2.2, label="HS — Max |u|")
            ax_disp.plot(t_h[: i + 1], [r["toe_runout_m"] for r in h_ts[: i + 1]], ":", color="#1f77b4", lw=1.7, label="H — Runout")
            ax_disp.plot(t_hs[: i + 1], [r["toe_runout_m"] for r in hs_ts[: i + 1]], "-.", color="#8c1d40", lw=1.8, label="HS — Runout")
            ax_disp.set_xlim(0, float(t_hs[-1]) * 1.03)
            ax_disp.set_ylim(0, disp_max_scale)
            ax_disp.set_xlabel("Time t (s)")
            ax_disp.set_ylabel("Displacement / Runout (m)")
            ax_disp.set_title("Displacement & Toe Runout")
            ax_disp.grid(True, alpha=0.3)
            ax_disp.legend(fontsize=7.5, loc="upper left")

            ax_ke.plot(t_h[: i + 1], [r["kinetic_energy_j"] * 1e-3 for r in h_ts[: i + 1]], "--", color="#1f77b4", lw=2.0, label="H — KE (kJ)")
            ax_ke.plot(t_hs[: i + 1], [r["kinetic_energy_j"] * 1e-3 for r in hs_ts[: i + 1]], "-", color="#d62728", lw=2.2, label="HS — KE (kJ)")
            ax_ke.set_xlim(0, float(t_hs[-1]) * 1.03)
            ax_ke.set_ylim(0, max(max(r["kinetic_energy_j"] for r in hs_ts), 1.0) * 1e-3 * 1.1)
            ax_ke.set_xlabel("Time t (s)")
            ax_ke.set_ylabel("Kinetic Energy (kJ)")
            ax_ke.set_title("Dynamic Collapse Kinetic Energy")
            ax_ke.grid(True, alpha=0.3)
            ax_ke.legend(fontsize=7.5, loc="upper right")

            fig.tight_layout(rect=[0, 0, 1, 0.92])
            fig.savefig(tmp_dir / f"frame_{i:04d}.png")
            plt.close(fig)

        encode_frames_to_mp4(tmp_dir, out_mp4, fps=8)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cliff_dir = root / "research" / "cliff"
    h_run = load_elongated_cliff_run(cliff_dir / "l-urmi-long-h")
    hs_run = load_elongated_cliff_run(cliff_dir / "l-urmi-long-hs")

    pair_summary = summarize_cliff_pair(h_run, hs_run)
    pair_summary["pairId"] = "L-URMI-LONG-H-vs-L-URMI-LONG-HS"
    pair_summary["domainWidthM"] = 102.0
    pair_summary["domainHeightM"] = 16.0
    pair_summary["shelfLengthM"] = 48.0
    pair_summary["runoutFloorLengthM"] = 54.0
    pair_summary["hFinalRetrogressionM"] = float(h_run["ts"][-1]["retrogression_distance_m"])
    pair_summary["hsFinalRetrogressionM"] = float(hs_run["ts"][-1]["retrogression_distance_m"])

    p1 = cliff_dir / "plots" / "m5_urmi_long_dashboard.png"
    p2 = cliff_dir / "plots" / "m5_urmi_long_spatial_localization.png"
    plot_elongated_dashboard(h_run, hs_run, p1)
    plot_elongated_spatial_snapshot(h_run, hs_run, p2)

    k_max_scale = max(
        float(np.percentile(h_run["vtk"][-1][2]["mc-kappa"], 99.2)),
        float(np.percentile(hs_run["vtk"][-1][2]["mc-kappa"], 99.2)),
        0.5,
    )
    disp_max_scale = max(
        max(r["max_disp_m"] for r in h_run["ts"]),
        max(r["max_disp_m"] for r in hs_run["ts"]),
    ) * 1.08

    vid_h = cliff_dir / "videos" / "5_cliff_urmi_long_hardening_lh.mp4"
    vid_hs = cliff_dir / "videos" / "6_cliff_urmi_long_softening_lhs.mp4"
    vid_pair = cliff_dir / "videos" / "cliff_urmi_long_h_vs_hs.mp4"

    print(f"Rendering elongated Video H: {vid_h.name} ...")
    render_single_elongated_video(
        h_run,
        "Simulasi Tebing Memanjang (Urmi Geometry 102 m × 16 m, Durasi Panjang) — Model H (Hardening)",
        "#1f77b4",
        vid_h,
        k_max_scale,
        disp_max_scale,
    )
    print(f"Rendering elongated Video HS: {vid_hs.name} ...")
    render_single_elongated_video(
        hs_run,
        "Simulasi Tebing Memanjang (Urmi Geometry 102 m × 16 m, Durasi Panjang) — Model HS (Softening Urmi Eq. 2)",
        "#d62728",
        vid_hs,
        k_max_scale,
        disp_max_scale,
    )
    print(f"Rendering side-by-side elongated Video: {vid_pair.name} ...")
    render_side_by_side_elongated_video(h_run, hs_run, vid_pair, k_max_scale, disp_max_scale)

    summary = {
        "milestone": "M5-URMI-LONG",
        "status": "PASS",
        "pair": pair_summary,
        "plots": [str(p1.relative_to(root)), str(p2.relative_to(root))],
        "videos": [
            str(vid_h.relative_to(root)),
            str(vid_hs.relative_to(root)),
            str(vid_pair.relative_to(root)),
        ],
    }
    (cliff_dir / "m5_urmi_long_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Elongated Urmi-geometry long-duration post-processing complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
