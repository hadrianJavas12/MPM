#!/usr/bin/env python3
"""Compare particle VTK geometry with a calibrated reference-video frame.

This is an image geometry proxy, not a damage-law or scientific accuracy score.
Defaults describe the provided 1280x720 reference video. Requires Pillow/numpy.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


def read_particle_vtk(path):
    """Read this engine's legacy ASCII declarations/big-endian double payloads."""
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
    line()  # title
    if line() != "BINARY" or line() != "DATASET UNSTRUCTURED_GRID":
        raise ValueError("Expected binary particle UNSTRUCTURED_GRID layout")
    header = line().split()
    if len(header) != 3 or header[0] != "POINTS" or header[2] != "double":
        raise ValueError("Expected POINTS n double")
    count = int(header[1])
    if count <= 0:
        raise ValueError("Particle output is empty")
    points = doubles(count * 3).reshape(count, 3)
    if line() != f"POINT_DATA {count}":
        raise ValueError("POINT_DATA count differs from POINTS")
    scalars = {}
    while offset < len(data):
        header = line()
        if not header:
            continue
        tokens = header.split()
        if len(tokens) != 4 or tokens[0] != "SCALARS" or tokens[2:] != ["double", "1"]:
            raise ValueError(f"Unexpected scalar declaration: {header!r}")
        name = tokens[1]
        if name in scalars:
            raise ValueError(f"Duplicate VTK scalar: {name}")
        if line() != "LOOKUP_TABLE default":
            raise ValueError("Expected default scalar lookup table")
        scalars[name] = doubles(count)
    for field in ("mass", "size_x", "size_y"):
        if field not in scalars:
            raise ValueError(f"Missing required geometry scalar: {field}")
        if not (scalars[field] > 0).all():
            raise ValueError(f"Nonpositive particle {field}")
    return points, scalars


def particle_occupancy(points, scalars, xs, ys, footprint):
    """Rasterise full size_x/y diameters on a shared subcell sampling grid."""
    occupied = np.zeros((len(ys), len(xs)), dtype=bool)
    for point, size_x, size_y in zip(points, scalars["size_x"], scalars["size_y"]):
        x, y = point[:2]
        rx, ry = size_x * 0.5, size_y * 0.5
        x0, x1 = np.searchsorted(xs, (x - rx, x + rx), side="left")
        y0, y1 = np.searchsorted(ys, (y - ry, y + ry), side="left")
        if x0 == x1 or y0 == y1:
            continue
        if footprint == "rectangle":
            occupied[y0:y1, x0:x1] = True
        else:
            ellipse = ((xs[x0:x1] - x) / rx)[None, :] ** 2 + ((ys[y0:y1] - y) / ry)[:, None] ** 2 <= 1
            occupied[y0:y1, x0:x1] |= ellipse
    return occupied


def reference_occupancy(frame, xs, ys, args):
    """Bilinearly sample RGB at world subcell centres, then identify coloured ink."""
    pixels = np.asarray(frame.convert("RGB"), dtype=np.float64)
    # Whole grid cells can extend beyond the stated window. Do not sample those
    # padded subcells outside the image; they are excluded from both masks.
    output = np.zeros((len(ys), len(xs)), dtype=bool)
    inside_xs, inside_ys = xs[xs < args.xmax], ys[ys < args.ymax]
    x = args.x_origin_pixel + args.x_pixels_per_metre * inside_xs
    y = args.y_origin_pixel - args.y_pixels_per_metre * inside_ys
    if x.min() < 0 or y.min() < 0 or x.max() >= frame.width - 1 or y.max() >= frame.height - 1:
        raise ValueError("Calibrated comparison window extends outside the reference image")
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    top = pixels[y0[:, None], x0[None, :]] * (1 - fx)[None, :, None] + pixels[y0[:, None], x0[None, :] + 1] * fx[None, :, None]
    bottom = pixels[y0[:, None] + 1, x0[None, :]] * (1 - fx)[None, :, None] + pixels[y0[:, None] + 1, x0[None, :] + 1] * fx[None, :, None]
    rgb = top * (1 - fy)[:, None, None] + bottom * fy[:, None, None]
    output[:len(inside_ys), :len(inside_xs)] = (rgb.max(axis=2) - rgb.min(axis=2) > args.saturation_threshold) & (rgb.min(axis=2) < 245)
    return output


def geometry_metrics(mask, xs, ys, spacing, args):
    above = mask & (ys[:, None] > args.foundation_cutoff)
    indices = np.flatnonzero(above.any(axis=0))
    right = float(xs[indices[-1]] + spacing * 0.5) if indices.size else None
    row_index = int(np.argmin(np.abs(ys - args.plateau_height)))
    row = mask[row_index]
    first = np.flatnonzero(row)
    plateau = None
    raw_plateau = None
    plateau_status = "no_left_connected_material_at_sampling_height"
    internal_gaps = 0
    row_coverage = None
    if first.size and first[0] <= 1:
        gap = max(1, math.ceil(args.plateau_gap / spacing))
        end = len(row)
        for i in range(int(first[0]), len(row) - gap + 1):
            if not row[i:i + gap].any():
                end = i
                break
        raw_plateau = float(xs[min(end, len(xs) - 1)] - spacing * 0.5 if end < len(xs) else xs[-1] + spacing * 0.5)
        span = int(first[-1] - first[0] + 1)
        row_coverage = float(row[first[0]:first[-1] + 1].mean())
        run = 0
        for occupied in row[first[0]:first[-1] + 1]:
            if occupied:
                if run >= gap:
                    internal_gaps += 1
                run = 0
            else:
                run += 1
        # Sparse coarse particle ellipses can repeatedly disconnect a nominally
        # solid top row. Their first gap is not evidence of metres of retreat.
        if internal_gaps >= 3 and end - first[0] < span * 0.5:
            plateau_status = "ambiguous_sparse_discontinuous_sampling_row"
        else:
            plateau, plateau_status = raw_plateau, "detected"
    return {"right_edge_above_foundation_m": right,
            "left_connected_top_plateau_edge_m": plateau,
            "top_plateau_status": plateau_status,
            "raw_first_gap_plateau_edge_m": raw_plateau,
            "large_internal_row_gaps": internal_gaps,
            "occupied_fraction_within_row_span": row_coverage,
            "actual_plateau_sampling_height_m": float(ys[row_index])}


def difference(left, right):
    return None if left is None or right is None else left - right


def compare(args):
    points, scalars = read_particle_vtk(args.vtk)
    frame = Image.open(args.reference_frame)
    spacing, subsamples = args.grid_spacing, args.subsamples
    nx, ny = math.ceil(args.xmax / spacing), math.ceil(args.ymax / spacing)
    # Extend the grid to whole cells, but retain the stated world window in masks.
    fine_xs = (np.arange(nx * subsamples) + 0.5) * spacing / subsamples
    fine_ys = (np.arange(ny * subsamples) + 0.5) * spacing / subsamples
    window = (fine_ys[:, None] < args.ymax) & (fine_xs[None, :] < args.xmax)
    simulation = particle_occupancy(points, scalars, fine_xs, fine_ys, args.footprint) & window
    reference = reference_occupancy(frame, fine_xs, fine_ys, args) & window

    def coverage(mask):
        return mask.reshape(ny, subsamples, nx, subsamples).mean(axis=(1, 3))

    sim_fraction, ref_fraction = coverage(simulation), coverage(reference)
    sim_mask, ref_mask = sim_fraction >= args.coverage_threshold, ref_fraction >= args.coverage_threshold
    xs, ys = (np.arange(nx) + 0.5) * spacing, (np.arange(ny) + 0.5) * spacing
    # Geometry score omits the foundation; the full-window score is also reported.
    above = ys[:, None] > args.foundation_cutoff

    def overlap(sim, ref):
        intersection, union = np.count_nonzero(sim & ref), np.count_nonzero(sim | ref)
        return {"iou": intersection / union if union else None,
                "intersection_area_proxy_m2": intersection * spacing ** 2,
                "union_area_proxy_m2": union * spacing ** 2,
                "simulation_area_proxy_m2": np.count_nonzero(sim) * spacing ** 2,
                "reference_area_proxy_m2": np.count_nonzero(ref) * spacing ** 2}

    sim_geometry = geometry_metrics(sim_mask, xs, ys, spacing, args)
    ref_geometry = geometry_metrics(ref_mask, xs, ys, spacing, args)
    soft_union = np.maximum(sim_fraction, ref_fraction)[above.repeat(nx, axis=1)].sum()
    soft_intersection = np.minimum(sim_fraction, ref_fraction)[above.repeat(nx, axis=1)].sum()
    outside = np.count_nonzero((points[:, 0] < 0) | (points[:, 0] >= args.xmax) | (points[:, 1] < 0) | (points[:, 1] >= args.ymax))
    return {
        "comparison_kind": "approximate_image_geometry_proxy",
        "inputs": {"vtk": str(Path(args.vtk).resolve()), "reference_frame": str(Path(args.reference_frame).resolve()),
                   "vtk_sha256": hashlib.sha256(Path(args.vtk).read_bytes()).hexdigest(),
                   "reference_frame_sha256": hashlib.sha256(Path(args.reference_frame).read_bytes()).hexdigest(),
                   "reference_time_s": args.reference_time, "simulation_time_s": args.simulation_time,
                   "provided_time_values_match": args.reference_time is not None and args.simulation_time is not None and args.reference_time == args.simulation_time,
                   "time_source": "explicit CLI values; titles are not OCR-read; VTK has no inferred clock"},
        "sampling": {"grid_spacing_m": spacing, "subsamples_per_axis": subsamples, "coverage_threshold": args.coverage_threshold,
                     "particle_footprint": args.footprint, "particle_widths": "full size_x and size_y; axis-aligned, rotation not reconstructed",
                     "world_window_m": [0, args.xmax, 0, args.ymax], "foundation_excluded_below_m": args.foundation_cutoff,
                     "reference_colour_detection": f"RGB max-min > {args.saturation_threshold} and min < 245; bilinear world-grid sampling",
                     "world_to_pixel": {"x0": args.x_origin_pixel, "y0": args.y_origin_pixel,
                                        "x_pixels_per_metre": args.x_pixels_per_metre, "y_pixels_per_metre": args.y_pixels_per_metre},
                     "practical_edge_uncertainty_m": [max(0.1, spacing * 0.5), max(0.2, spacing)],
                     "uncertainty_basis": "heuristic video-edge tolerance enlarged for grid quantisation; not a statistical confidence interval"},
        "particle_count": len(points), "finite_scalar_arrays": len(scalars),
        "particle_centres_outside_comparison_window": int(outside),
        "above_foundation_overlap": overlap(sim_mask & above, ref_mask & above),
        "full_window_overlap": overlap(sim_mask, ref_mask),
        "above_foundation_fractional_overlap_iou": float(soft_intersection / soft_union) if soft_union else None,
        "simulation_geometry": sim_geometry, "reference_geometry": ref_geometry,
        "differences_simulation_minus_reference_m": {
            key: difference(sim_geometry[key], ref_geometry[key])
            for key in ("right_edge_above_foundation_m", "left_connected_top_plateau_edge_m")},
        "limitations": ["IoU is not a percentage of physical or numerical accuracy.",
                        "No damage/stress/RGB-value matching: the reference colourbar is adaptive.",
                        "Compressed video, antialiasing, particle footprint and subcell sampling affect the proxy.",
                        "Areas describe image occupancy, not conserved particle mass or material volume.",
                        "This parser supports the engine's points/scalars layout, not arbitrary legacy VTK datasets.",
                        "Match phase and verified simulator times before interpreting deformed-state differences."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vtk", type=Path, required=True)
    parser.add_argument("--reference-frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-time", type=float)
    parser.add_argument("--simulation-time", type=float)
    parser.add_argument("--grid-spacing", type=float, default=0.1)
    parser.add_argument("--subsamples", type=int, default=2)
    parser.add_argument("--coverage-threshold", type=float, default=0.5)
    parser.add_argument("--footprint", choices=("ellipse", "rectangle"), default="ellipse")
    parser.add_argument("--xmax", type=float, default=31.0)
    parser.add_argument("--ymax", type=float, default=17.3)
    parser.add_argument("--x-origin-pixel", type=float, default=31.0)
    parser.add_argument("--y-origin-pixel", type=float, default=637.0)
    parser.add_argument("--x-pixels-per-metre", type=float, default=31.9333333333)
    parser.add_argument("--y-pixels-per-metre", type=float, default=31.9375)
    parser.add_argument("--saturation-threshold", type=float, default=40)
    parser.add_argument("--foundation-cutoff", type=float, default=1.2)
    parser.add_argument("--plateau-height", type=float, default=16.45)
    parser.add_argument("--plateau-gap", type=float, default=0.2)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".json" or args.output.resolve() in (args.vtk.resolve(), args.reference_frame.resolve()):
        parser.error("output must be a separate JSON file; reference inputs are read-only")
    for value in (args.grid_spacing, args.xmax, args.ymax, args.x_pixels_per_metre, args.y_pixels_per_metre, args.plateau_gap):
        if not math.isfinite(value) or value <= 0:
            parser.error("grid/window/calibration/gap values must be finite and positive")
    if not 1 <= args.subsamples <= 8 or not 0 < args.coverage_threshold <= 1:
        parser.error("subsamples must be 1..8 and coverage threshold must be (0,1]")
    if math.ceil(args.xmax / args.grid_spacing) * math.ceil(args.ymax / args.grid_spacing) * args.subsamples ** 2 > 20_000_000:
        parser.error("Sampling grid exceeds 20 million subcells")
    if not 0 <= args.foundation_cutoff < args.ymax or not 0 <= args.plateau_height <= args.ymax:
        parser.error("foundation cutoff and plateau height must be inside the world window")
    for value in (args.x_origin_pixel, args.y_origin_pixel, args.saturation_threshold, args.reference_time, args.simulation_time):
        if value is not None and not math.isfinite(value):
            parser.error("pixel/time/threshold values must be finite")
    if not 0 <= args.saturation_threshold <= 255:
        parser.error("saturation threshold must be 0..255")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = compare(args)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "particle_count": result["particle_count"],
                      "above_foundation_iou": result["above_foundation_overlap"]["iou"],
                      "differences_m": result["differences_simulation_minus_reference_m"]}, indent=2))


if __name__ == "__main__":
    main()
