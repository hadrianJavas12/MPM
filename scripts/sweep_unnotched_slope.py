#!/usr/bin/env python3
"""Headless no-notch Mohr-Coulomb H/HS slope-angle sweep and single montage MP4.

Runs each native CL-MPM case using the existing Windows source-snapshot CLI.
No Studio, fabricated frames, or chart/plot generation.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANGLES = (45, 65, 85)
BRANCH_SCOPE = "unnotched-slope-angle-urmi-long-h-vs-hs-v3-6cases"
MODELS = ("H", "HS")


def lisp_double(number: float) -> str:
    """Emit a non-reader-evaluating double-float token for a finite scalar."""
    number = float(number)
    if not math.isfinite(number):
        raise ValueError("Nonfinite Lisp parameter")
    return f"{number:.8f}d0"


def case_content(angle: int, model: str, plan: dict) -> str:
    if model not in MODELS:
        raise ValueError(f"Unsupported material model: {model}")
    variant = "h" if model == "H" else "hs"
    material = "mc-h" if model == "H" else "mc-hs"
    # Identical geometry, peak strength, initial state and loading in both models.
    # The H law arrests its evolution at peak; HS follows the residual branch.
    return f"""(in-package :cl-mpm/framework)
(let ((params (make-hash-table :test #'equal)))
  (setf (gethash "substeps" params) {plan['substeps']}
        (gethash "settleSteps" params) {plan['settle_steps']}
        (gethash "cflScale" params) {lisp_double(plan['cfl_scale'])}
        (gethash "elongatedShelfAspect" params) {lisp_double(plan['shelf_aspect'])}
        (gethash "runoutAspect" params) {lisp_double(plan['runout_aspect'])})
  (setf *simulation*
        (make-simulation
         :scenario :cliff
         :parameters params
         :material (make-material :{material}
                    :youngs-modulus 5.25d6
                    :poisson-ratio 0.2d0
                    :density 1917.07d0
                    :evolution-law
                    (cl-mpm/models/mc-evolution:make-urmi-evolution-law
                     :variant :{variant}
                     :prepeak-points '((0d0 15.0d0) (0.05d0 20.0d0))
                     :prepeak-cohesion-points '((0d0 5000d0) (0.05d0 7000d0))
                     :peak-kappa 0.05d0
                     :residual-kappa 0.20d0
                     :phi-peak-deg 20.0d0
                     :phi-post-rupture-deg 16.0d0
                     :phi-residual-deg 13.0d0
                     :c-peak-pa 7000d0
                     :c-post-rupture-pa 4000d0
                     :c-residual-pa 2000d0
                     :beta -5.0d0
                     :postpeak-segments 8
                     :psi 1.0d0
                     :strain-assumption "Urmi Long M5 baseline; gravity-only, unnotched angle sweep; exploratory"))
         :geometry (make-geometry :cliff
                    :height {lisp_double(plan['height'])}
                    :shelf-aspect {lisp_double(plan['shelf_aspect'])}
                    :slope {lisp_double(angle)}
                    :base-height {lisp_double(plan['base_height'])}
                    :notch-height 0d0
                    :notch-depth 0d0)
         :boundary (make-boundary :rollers)
         :loading (make-loading :gravity)
         :solver (make-solver :explicit
                  :mesh-size {lisp_double(plan['mesh_size'])}
                  :mps-per-cell {plan['mps_per_cell']}
                  :frames {plan['frames']}
                  :workers {plan['workers']}))))
"""


def make_plan(args: argparse.Namespace) -> dict:
    angles = sorted(set(args.angles))
    if len(angles) != len(args.angles):
        raise ValueError("Angle values must be unique")
    if not angles or any(not 45 <= a <= 90 for a in angles):
        raise ValueError("Current canonical cliff schema accepts slope angles 45..90 degrees")
    if args.height <= 0 or args.base_height < 0 or args.mesh_size <= 0 or args.shelf_aspect <= 0:
        raise ValueError("Invalid geometric dimension")
    if not 0.05 <= args.mesh_size <= 20:
        raise ValueError("mesh-size outside shared schema range [0.05,20]")
    if not 0.5 <= args.shelf_aspect <= 5 or not 0 <= args.base_height <= 100:
        raise ValueError("Shelf aspect or base-height outside canonical schema")
    if not 10 <= args.height <= 500:
        raise ValueError("Height outside canonical schema [10,500]")
    if not 1 <= args.mps_per_cell <= 4 or not 1 <= args.workers <= 64:
        raise ValueError("Invalid particle or worker count")
    if not 1 <= args.frames <= 2000 or not 1 <= args.substeps <= 1000:
        raise ValueError("Invalid frame/substep count")
    if args.settle_steps < 1 or not 0 < args.cfl_scale <= 1:
        raise ValueError("Invalid settle-steps or CFL scale")
    if args.runout_aspect < 0.1 or args.runout_aspect > 5:
        raise ValueError("Runout aspect outside canonical schema")
    if args.parallel not in (1, 2):
        raise ValueError("Use --parallel 1 (recommended) or --parallel 2")
    crest_x = args.height * args.shelf_aspect - args.height / math.tan(math.radians(min(angles)))
    if crest_x <= args.mesh_size:
        raise ValueError("Crest too close to left edge; increase --shelf-aspect")
    return {
        "scope": BRANCH_SCOPE, "angles": angles, "models": list(MODELS),
        "height": args.height, "base_height": args.base_height,
        "shelf_aspect": args.shelf_aspect, "runout_aspect": args.runout_aspect,
        "mesh_size": args.mesh_size, "mps_per_cell": args.mps_per_cell,
        "frames": args.frames, "substeps": args.substeps, "settle_steps": args.settle_steps,
        "cfl_scale": args.cfl_scale, "workers": args.workers,
        "reference": "M5 Urmi Long-Duration: cases/cliff/cliff-urmi-long-mc-{h,hs}.lisp (only slope, notch, optional solver/geometry overrides)",
        "synchronization": "equal saved frame/update number; actual physical time shown per panel",
    }


def entries(plan: dict, output: Path):
    for angle in plan["angles"]:
        for model in MODELS:
            name = f"slope_{angle:02d}_{model.lower()}"
            yield angle, model, output / "cases" / f"{name}.lisp", output / "runs" / name


def prepare(plan: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "plan.json"
    if plan_path.exists():
        existing = json.loads(plan_path.read_text(encoding="utf-8"))
        if existing != plan:
            raise ValueError(f"{plan_path} has different parameters; use --output for a new batch")
    else:
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (output / "cases").mkdir(exist_ok=True)
    for angle, model, case, _ in entries(plan, output):
        source = case_content(angle, model, plan)
        if case.exists():
            if case.read_text(encoding="utf-8") != source:
                raise ValueError(f"Existing case differs: {case}")
        else:
            case.write_text(source, encoding="utf-8")


def verified_run(run_dir: Path, frames: int) -> bool:
    manifest = run_dir / "manifest.json"
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        if data.get("complete") is not True or data.get("frames") != frames:
            return False
        csv_path = run_dir / "cliff-timeseries.csv"
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != frames + 1:
            return False
        if [int(row["frame"]) for row in rows] != list(range(frames + 1)):
            return False
        return all((run_dir / "vtk" / f"sim_{i:05d}.vtk").is_file()
                   for i in range(frames + 1))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False


def run_one(item: tuple, frames: int) -> str:
    angle, model, case, run_dir = item
    if verified_run(run_dir, frames):
        return f"SKIP  {angle} deg {model} (verified completed outputs)"
    if run_dir.exists() and any(run_dir.iterdir()):
        raise RuntimeError(f"Partial/unverified run at {run_dir}; preserve for investigation, then use a fresh --output")
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir.parent / f"{run_dir.name}.log"
    launcher = ROOT / "windows" / "cl-mpm.cmd"
    if os.name != "nt":
        raise RuntimeError("The snapshot-protected native CLI requires Windows")
    if not launcher.exists():
        raise FileNotFoundError(launcher)
    command = [str(launcher), str(ROOT / "scripts" / "run-case.lisp"),
               str(case), str(run_dir)]
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0 or not verified_run(run_dir, frames):
        raise RuntimeError(f"Simulation failed for {angle} deg {model}; inspect {log} (exit={result.returncode})")
    return f"DONE  {angle} deg {model} | {run_dir}"


def save_comparison(plan: dict, output: Path) -> None:
    out_path = output / "comparison.csv"
    names = ("max_disp_m", "toe_runout_m", "crest_settlement_m", "max_kappa",
             "softened_fraction", "kinetic_energy_j", "max_vel_m_s", "time_s")
    with out_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["angle_deg", "model", *names])
        for angle, model, _, run_dir in entries(plan, output):
            with (run_dir / "cliff-timeseries.csv").open(encoding="utf-8-sig", newline="") as source:
                last = list(csv.DictReader(source))[-1]
            writer.writerow([angle, model, *[last[name] for name in names]])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angles", type=int, nargs="+", default=list(DEFAULT_ANGLES))
    parser.add_argument("--height", type=float, default=12)
    parser.add_argument("--base-height", type=float, default=4)
    parser.add_argument("--shelf-aspect", type=float, default=4.0)
    parser.add_argument("--runout-aspect", type=float, default=4.5)
    parser.add_argument("--mesh-size", type=float, default=0.5)
    parser.add_argument("--mps-per-cell", type=int, default=2)
    parser.add_argument("--frames", type=int, default=80)
    parser.add_argument("--substeps", type=int, default=40)
    parser.add_argument("--settle-steps", type=int, default=220)
    parser.add_argument("--cfl-scale", type=float, default=0.35)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--parallel", type=int, choices=(1, 2), default=1,
                        help="Number of simultaneous native simulations; 1 uses less RAM")
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "slope-angle-sweep-urmi-long-6")
    parser.add_argument("--dry-run", action="store_true", help="Generate files without running solver or video")
    parser.add_argument("--render-only", action="store_true", help="Only render existing, completed VTK runs")
    args = parser.parse_args(argv)
    if args.dry_run and args.render_only:
        parser.error("--dry-run and --render-only are mutually exclusive")
    if args.fps <= 0 or args.fps > 60:
        parser.error("--fps must be 1..60")
    output = args.output.resolve()
    if args.render_only:
        plan = json.loads((output / "plan.json").read_text(encoding="utf-8"))
        if plan.get("scope") != BRANCH_SCOPE:
            raise ValueError("Output plan is not from this sweep")
    else:
        plan = make_plan(args)
        prepare(plan, output)
    items = list(entries(plan, output))
    if args.dry_run:
        print(f"DRY RUN: {len(items)} cases generated in {output / 'cases'}")
        return 0
    if not args.render_only:
        failures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
            tasks = {executor.submit(run_one, item, plan["frames"]): item for item in items}
            for future in concurrent.futures.as_completed(tasks):
                try:
                    print(future.result(), flush=True)
                except Exception as exc:
                    failures.append(str(exc))
                    print(f"ERROR {exc}", file=sys.stderr, flush=True)
        if failures:
            raise RuntimeError(f"{len(failures)} runs failed; montage not produced. See output/runs logs.")
    missing = [f"{angle} deg {model}" for angle, model, _, run in items
               if not verified_run(run, plan["frames"])]
    if missing:
        raise RuntimeError("Unverified/incomplete runs: " + ", ".join(missing))
    save_comparison(plan, output)
    from render_slope_montage import render_video
    video = output / "all_angles_H_vs_HS.mp4"
    render_video(plan, output, video, fps=args.fps)
    print(f"VIDEO READY: {video}")
    print(f"METRICS CSV: {output / 'comparison.csv'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
