#!/usr/bin/env python3
"""Render the 4 individual MPM simulation videos (T-100-H, T-100-HS, L-H, L-HS) from saved VTK/CSV outputs."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

from plot_m4_triaxial_comparison import load_run as load_triaxial_run
from plot_m5_cliff_comparison import load_cliff_run


def encode_frames_to_mp4(frame_dir: Path, out_mp4: Path, fps: int) -> None:
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


def render_single_triaxial_video(
    run: dict,
    title: str,
    curve_color: str,
    out_mp4: Path,
    k_max_scale: float,
    q_max_scale: float,
) -> None:
    stress = run["stress"]
    diag = run["diag"]
    vtk = run["vtk"]
    n = len(stress)
    strain_pct = np.array([r["axial_strain_pct"] for r in stress])
    q_kpa = np.array([r["deviatoric_stress_kpa"] for r in stress])
    phi_deg = np.array([r["mean_mc-friction-deg"] for r in diag])
    k_max_arr = np.array([r["max_mc-kappa-max"] for r in diag])

    norm_k = Normalize(vmin=0.0, vmax=max(0.1, k_max_scale))
    norm_phi = Normalize(vmin=16.0, vmax=34.5)

    with tempfile.TemporaryDirectory(prefix="triax_vid_") as tmp:
        tmp_dir = Path(tmp)
        for i in range(n):
            fig = plt.figure(figsize=(13.5, 5.8), dpi=130)
            fig.suptitle(
                f"{title} — εa = {strain_pct[i]:.2f}% | q = {q_kpa[i]:.1f} kPa | "
                f"max κ = {k_max_arr[i]:.4f} | mean φ = {phi_deg[i]:.2f}°",
                fontsize=11.5,
                fontweight="bold",
                y=0.97,
            )

            ax1 = fig.add_subplot(1, 3, 1, projection="3d")
            ax2 = fig.add_subplot(1, 3, 2, projection="3d")
            ax3 = fig.add_subplot(1, 3, 3)

            pts = vtk[i][1]
            fields = vtk[i][2]

            sc1 = ax1.scatter(
                pts[:, 0] * 1e3,
                pts[:, 2] * 1e3,
                pts[:, 1] * 1e3,
                c=fields["mc-kappa"],
                cmap="inferno",
                norm=norm_k,
                s=22,
                alpha=0.92,
                edgecolors="none",
            )
            ax1.set_title("Plastic Shear Strain κ (-)", fontsize=10)
            ax1.set_xlabel("x (mm)", fontsize=8)
            ax1.set_ylabel("z (mm)", fontsize=8)
            ax1.set_zlabel("y (mm)", fontsize=8)
            ax1.set_xlim(0, 42)
            ax1.set_ylim(0, 42)
            ax1.set_zlim(0, 145)
            ax1.view_init(elev=18, azim=38)
            fig.colorbar(sc1, ax=ax1, shrink=0.62, pad=0.08, label="κ (-)")

            sc2 = ax2.scatter(
                pts[:, 0] * 1e3,
                pts[:, 2] * 1e3,
                pts[:, 1] * 1e3,
                c=fields["mc-friction-deg"],
                cmap="viridis",
                norm=norm_phi,
                s=22,
                alpha=0.92,
                edgecolors="none",
            )
            ax2.set_title("Mobilized Friction Angle φ(κ) (deg)", fontsize=10)
            ax2.set_xlabel("x (mm)", fontsize=8)
            ax2.set_ylabel("z (mm)", fontsize=8)
            ax2.set_zlabel("y (mm)", fontsize=8)
            ax2.set_xlim(0, 42)
            ax2.set_ylim(0, 42)
            ax2.set_zlim(0, 145)
            ax2.view_init(elev=18, azim=38)
            fig.colorbar(sc2, ax=ax2, shrink=0.62, pad=0.08, label="φ (deg)")

            ax3.plot(strain_pct, q_kpa, color=curve_color, alpha=0.28, lw=1.8, linestyle="--")
            ax3.plot(strain_pct[: i + 1], q_kpa[: i + 1], color=curve_color, lw=2.6, label="Deviatoric Stress q")
            ax3.scatter([strain_pct[i]], [q_kpa[i]], color=curve_color, s=48, zorder=5)
            ax3.axhline(253.56, color="gray", linestyle=":", lw=1.1, label="Analytical Peak (253.6 kPa)")
            ax3.axhline(78.29, color="brown", linestyle="-.", lw=1.1, label="Analytical Residual (78.3 kPa)")
            ax3.set_xlim(0, max(14.8, float(strain_pct[-1]) * 1.03))
            ax3.set_ylim(0, q_max_scale)
            ax3.set_xlabel("Axial Strain εa (%)")
            ax3.set_ylabel("Deviatoric Stress q (kPa)")
            ax3.set_title("Macroscopic Stress–Strain Response")
            ax3.grid(True, alpha=0.3)
            ax3.legend(fontsize=8, loc="lower right")

            fig.tight_layout(rect=[0, 0, 1, 0.92])
            fig.savefig(tmp_dir / f"frame_{i:04d}.png")
            plt.close(fig)

        encode_frames_to_mp4(tmp_dir, out_mp4, fps=6)


def render_single_cliff_video(
    run: dict,
    title: str,
    curve_color: str,
    out_mp4: Path,
    k_max_scale: float,
    disp_max_scale: float,
) -> None:
    ts = run["ts"]
    vtk = run["vtk"]
    n = len(ts)
    t_arr = np.array([r["time_s"] for r in ts])
    disp_arr = np.array([r["max_disp_m"] for r in ts])
    runout_arr = np.array([r["toe_runout_m"] for r in ts])
    crest_arr = np.array([r["crest_settlement_m"] for r in ts])
    k_max_arr = np.array([r["max_kappa"] for r in ts])
    min_phi_arr = np.array([r["min_phi_deg"] for r in ts])

    norm_k = Normalize(vmin=0.0, vmax=max(0.2, k_max_scale))
    norm_phi = Normalize(vmin=13.0, vmax=20.0)

    with tempfile.TemporaryDirectory(prefix="cliff_vid_") as tmp:
        tmp_dir = Path(tmp)
        for i in range(n):
            fig = plt.figure(figsize=(13.5, 7.6), dpi=130)
            gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1.0])
            ax_k = fig.add_subplot(gs[0, 0])
            ax_p = fig.add_subplot(gs[1, 0])
            ax_c = fig.add_subplot(gs[:, 1])

            fig.suptitle(
                f"{title} — t = {t_arr[i]:.2f} s | max |u| = {disp_arr[i]:.2f} m | "
                f"toe runout = {runout_arr[i]:.2f} m | max κ = {k_max_arr[i]:.2f} | min φ = {min_phi_arr[i]:.1f}°",
                fontsize=11.2,
                fontweight="bold",
                y=0.98,
            )

            pts = vtk[i][1]
            fields = vtk[i][2]

            s1 = ax_k.scatter(
                pts[:, 0], pts[:, 1], c=fields["mc-kappa"], cmap="inferno", norm=norm_k, s=4.8, edgecolors="none"
            )
            ax_k.set_title("Equivalent Plastic Shear Strain κ (-)", fontsize=10)
            ax_k.set_xlabel("x (m)")
            ax_k.set_ylabel("Elevation y (m)")
            ax_k.set_xlim(0, 44)
            ax_k.set_ylim(0, 18)
            ax_k.set_aspect("equal", adjustable="box")
            ax_k.grid(True, alpha=0.22)
            fig.colorbar(s1, ax=ax_k, fraction=0.035, pad=0.02, label="κ (-)")

            s2 = ax_p.scatter(
                pts[:, 0], pts[:, 1], c=fields["mc-friction-deg"], cmap="viridis", norm=norm_phi, s=4.8, edgecolors="none"
            )
            ax_p.set_title("Mobilized Friction Angle φ(κ) (deg)", fontsize=10)
            ax_p.set_xlabel("x (m)")
            ax_p.set_ylabel("Elevation y (m)")
            ax_p.set_xlim(0, 44)
            ax_p.set_ylim(0, 18)
            ax_p.set_aspect("equal", adjustable="box")
            ax_p.grid(True, alpha=0.22)
            fig.colorbar(s2, ax=ax_p, fraction=0.035, pad=0.02, label="φ (deg)")

            ax_c.plot(t_arr, disp_arr, color=curve_color, alpha=0.25, lw=1.6, linestyle="--")
            ax_c.plot(t_arr[: i + 1], disp_arr[: i + 1], color=curve_color, lw=2.5, label="Max Displacement |u| (m)")
            ax_c.plot(t_arr[: i + 1], runout_arr[: i + 1], color="#8c1d40", lw=2.0, linestyle="-.", label="Toe Runout (m)")
            ax_c.plot(t_arr[: i + 1], crest_arr[: i + 1], color="#2ca02c", lw=1.8, linestyle=":", label="Crest Settlement (m)")
            ax_c.scatter([t_arr[i]], [disp_arr[i]], color=curve_color, s=45, zorder=5)
            ax_c.set_xlim(0, float(t_arr[-1]) * 1.03)
            ax_c.set_ylim(0, disp_max_scale)
            ax_c.set_xlabel("Stage-2 Dynamic Time t (s)")
            ax_c.set_ylabel("Displacement / Runout / Settlement (m)")
            ax_c.set_title("Progressive Slope Collapse Evolution")
            ax_c.grid(True, alpha=0.3)
            ax_c.legend(fontsize=8.5, loc="upper left")

            fig.tight_layout(rect=[0, 0, 1, 0.94])
            fig.savefig(tmp_dir / f"frame_{i:04d}.png")
            plt.close(fig)

        encode_frames_to_mp4(tmp_dir, out_mp4, fps=8)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    triax_dir = root / "research" / "triaxial"
    cliff_dir = root / "research" / "cliff"

    # Load matched 30-frame triaxial runs so both cover the same 0..14.26% axial strain window
    t_hs = load_triaxial_run(triax_dir / "t-100-hs")
    n_matched = len(t_hs["stress"])
    t_h = load_triaxial_run(triax_dir / "t-100-h", max_frames=n_matched)

    k_max_triax = max(
        max(r["max_mc-kappa-max"] for r in t_h["diag"]),
        max(r["max_mc-kappa-max"] for r in t_hs["diag"]),
    )
    q_max_triax = 280.0

    vid1 = triax_dir / "videos" / "1_triaxial_3d_hardening_t100h.mp4"
    vid2 = triax_dir / "videos" / "2_triaxial_3d_softening_t100hs.mp4"
    print(f"Rendering Video 1/4: {vid1.name} ...")
    render_single_triaxial_video(
        t_h,
        "Simulasi 1: 3D MPM Triaxial — Model H (Hardening Plateau, σ3=100 kPa)",
        "#1f77b4",
        vid1,
        k_max_triax,
        q_max_triax,
    )
    print(f"Rendering Video 2/4: {vid2.name} ...")
    render_single_triaxial_video(
        t_hs,
        "Simulasi 2: 3D MPM Triaxial — Model HS (Hardening–Softening, σ3=100 kPa)",
        "#d62728",
        vid2,
        k_max_triax,
        q_max_triax,
    )

    l_h = load_cliff_run(cliff_dir / "l-h")
    l_hs = load_cliff_run(cliff_dir / "l-hs")
    k_max_cliff = max(
        max(r["max_kappa"] for r in l_h["ts"]),
        max(r["max_kappa"] for r in l_hs["ts"]),
    )
    disp_max_cliff = max(
        max(r["max_disp_m"] for r in l_h["ts"]),
        max(r["max_disp_m"] for r in l_hs["ts"]),
    ) * 1.08

    vid3 = cliff_dir / "videos" / "3_cliff_2d_hardening_lh.mp4"
    vid4 = cliff_dir / "videos" / "4_cliff_2d_softening_lhs.mp4"
    print(f"Rendering Video 3/4: {vid3.name} ...")
    render_single_cliff_video(
        l_h,
        "Simulasi 3: 2D MPM Tebing — Model H (Hardening Plateau: c=7 kPa, φ=20°)",
        "#1f77b4",
        vid3,
        k_max_cliff,
        disp_max_cliff,
    )
    print(f"Rendering Video 4/4: {vid4.name} ...")
    render_single_cliff_video(
        l_hs,
        "Simulasi 4: 2D MPM Tebing — Model HS (Softening Residual: c=2 kPa, φ=13°)",
        "#d62728",
        vid4,
        k_max_cliff,
        disp_max_cliff,
    )
    print("All 4 individual MPM simulation videos rendered successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
