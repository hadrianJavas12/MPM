#!/usr/bin/env python3
"""Render all completed unnotched slope simulations into ONE synchronized tiled MP4.

Every tile uses its actual particle VTK and scalar mc-kappa. No graphs, interpolation,
invented motion, or per-scenario video files. Frames align by solver update index;
time_s from the independent simulation is displayed on every tile.
"""
from __future__ import annotations

import csv
import importlib.util
import math
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def vtk_reader():
    """Reuse the repository's validated legacy-binary particle VTK parser."""
    source = Path(__file__).with_name("compare-reference-video.py")
    if not source.is_file():
        raise FileNotFoundError(source)
    spec = importlib.util.spec_from_file_location("slope_vtk_reader", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.read_particle_vtk


def font(size: int):
    for path in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def load_timestamps(run: Path, frames: int) -> list[dict]:
    rows = list(csv.DictReader((run / "cliff-timeseries.csv").open(encoding="utf-8-sig", newline="")))
    if len(rows) != frames + 1 or [int(r["frame"]) for r in rows] != list(range(frames + 1)):
        raise ValueError(f"Frame count/sequence mismatch in {run}")
    for r in rows:
        for k in ("time_s", "max_disp_m", "max_kappa", "toe_runout_m", "kinetic_energy_j"):
            if not math.isfinite(float(r[k])):
                raise ValueError(f"Nonfinite {k} in {run}")
    return rows


def kappa_color(value: float) -> tuple[int, int, int]:
    """Fixed physical color mapping shared by ALL panels and ALL frames."""
    a = max(0.0, min(1.0, float(value) / 0.5))
    stops = ((0.0, (126, 145, 151)), (0.15, (47, 127, 142)),
             (0.35, (46, 174, 144)), (0.65, (250, 195, 65)),
             (1.0, (223, 74, 52)))
    for (u0, c0), (u1, c1) in zip(stops, stops[1:]):
        if a <= u1:
            fraction = (a - u0) / (u1 - u0)
            return tuple(round(x + fraction * (y - x)) for x, y in zip(c0, c1))
    return stops[-1][1]


def draw_panel(read_particle_vtk, run: Path, row: dict, width: int, height: int,
               x_limit: float, y_limit: float, angle: int, model: str) -> Image.Image:
    image = Image.new("RGB", (width, height), (245, 247, 248))
    canvas = ImageDraw.Draw(image)
    banner = (34, 50, 63) if model == "H" else (102, 49, 40)
    canvas.rectangle((0, 0, width, 29), fill=banner)
    canvas.text((10, 6), f"{angle} deg   MODEL {model}", font=font(16), fill=(255, 255, 255))

    path = run / "vtk" / f"sim_{int(row['frame']):05d}.vtk"
    points, fields = read_particle_vtk(path)
    if points.shape[1] != 3 or "mc-kappa" not in fields:
        raise ValueError(f"Missing required material field mc-kappa in {path}")
    kappa = fields["mc-kappa"]
    if len(kappa) != len(points) or not np.isfinite(kappa).all() or (kappa < -1e-10).any():
        raise ValueError(f"Invalid plastic strain in {path}")

    # Same viewport for all angles/models/frames. Per-particle footprint comes
    # from saved VTK size_x/size_y rather than point-only visualization.
    x_pad, y_pad_top, y_pad_bottom = 14, 37, 27
    scale = min((width - 2*x_pad) / x_limit,
                (height - y_pad_top - y_pad_bottom) / y_limit)
    ground = height - y_pad_bottom
    canvas.line((x_pad, ground, width - x_pad, ground), fill=(80, 88, 92), width=1)
    for point, sx, sy, val in zip(points, fields["size_x"], fields["size_y"], kappa):
        x, y = float(point[0]), float(point[1])
        if x < -2 or x > x_limit + 2 or y < -2 or y > y_limit + 2:
            continue
        x0 = x_pad + (x - float(sx)/2)*scale
        x1 = x_pad + (x + float(sx)/2)*scale
        y0 = ground - (y + float(sy)/2)*scale
        y1 = ground - (y - float(sy)/2)*scale
        canvas.rectangle((round(x0), round(y0), max(round(x0)+1, round(x1)),
                          max(round(y0)+1, round(y1))), fill=kappa_color(val))
    # Time is measured independently per case; equal frame indices are not
    # inaccurately described as equal physical times.
    canvas.text((10, height - 22),
                f"t={float(row['time_s']):.2f}s   disp={float(row['max_disp_m']):.2f}m"
                f"   max kappa={float(row['max_kappa']):.3f}   runout={float(row['toe_runout_m']):.2f}m",
                font=font(13), fill=(30, 43, 48))
    return image


def render_video(plan: dict, output: Path, video: Path, fps: int = 8) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH; install it before video rendering")
    n = len(plan["angles"])
    if n < 1 or plan["models"] != ["H", "HS"]:
        raise ValueError("Invalid sweep plan")
    frames = int(plan["frames"])
    # Two columns (H/HS) and one row per angle: all runs visible at once.
    width, tile_width, tile_height, margin, top, gap = 1920, 934, 240, 20, 73, 8
    height = top + n * (tile_height + gap) + 20
    if height % 2:
        height += 1
    if height > 4096:
        raise ValueError("Too many angles for one video; split the sweep into batches")
    x_limit = (plan["shelf_aspect"] + plan["runout_aspect"]) * plan["height"]
    y_limit = plan["height"] + plan["base_height"] + 2 * plan["mesh_size"]
    runs = {}
    for angle in plan["angles"]:
        for model in ("H", "HS"):
            run = output / "runs" / f"slope_{angle:02d}_{model.lower()}"
            runs[(angle, model)] = (run, load_timestamps(run, frames))

    read_particle_vtk = vtk_reader()
    video.parent.mkdir(parents=True, exist_ok=True)
    tmp = video.with_name(video.stem + ".partial.mp4")
    if tmp.exists():
        raise ValueError(f"Old partial video exists: {tmp}; inspect/remove it first")
    log_path = output / "ffmpeg.log"
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", f"{width}x{height}",
               "-framerate", str(fps), "-i", "pipe:0",
               "-an", "-c:v", "libx264", "-preset", "veryfast",
               "-threads", "2", "-crf", "24", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(tmp)]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
        try:
            for frame in range(frames + 1):
                image = Image.new("RGB", (width, height), (224, 230, 234))
                draw = ImageDraw.Draw(image)
                draw.text((20, 9), "MPM 2D  |  UNNOTCHED SLOPE ANGLE SWEEP",
                          font=font(24), fill=(22, 44, 57))
                draw.text((20, 42), "Equal saved frame/update index; each panel shows its own physical time.  "
                          "Color: plastic strain kappa (gray=0 to red>=0.5).",
                          font=font(14), fill=(42, 55, 64))
                for idx, angle in enumerate(plan["angles"]):
                    for column, model in enumerate(("H", "HS")):
                        run, rows = runs[(angle, model)]
                        panel = draw_panel(read_particle_vtk, run, rows[frame],
                                           tile_width, tile_height, x_limit,
                                           y_limit, angle, model)
                        image.paste(panel, (margin + column*(tile_width + gap),
                                            top + idx*(tile_height + gap)))
                process.stdin.write(image.tobytes())
                print(f"Rendering shared video frame {frame}/{frames}", flush=True)
            process.stdin.close()
            code = process.wait()
            if code:
                raise RuntimeError(f"ffmpeg exited with {code}; see {log_path}")
            if not tmp.is_file() or tmp.stat().st_size <= 0:
                raise RuntimeError("ffmpeg finished without a nonempty video")
            tmp.replace(video)
        except BaseException:
            if process.poll() is None:
                process.kill()
                process.wait()
            if tmp.exists():
                tmp.unlink()
            raise
