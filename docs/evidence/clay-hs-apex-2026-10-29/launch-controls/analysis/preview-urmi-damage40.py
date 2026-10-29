#!/usr/bin/env python3
"""Read-only preview of a completed saved prefix while Urmi MPM keeps running.

This is a separate ACTIVE_PARTIAL_NOT_FULL_VALIDATION observer. It never calls
the terminal reviewer entry point, changes the native manifest, or runs MPM.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import numpy as np

SCOPE = "ACTIVE_PARTIAL_NOT_FULL_VALIDATION"
MINIMUM_FRAMES, MAXIMUM_FRAMES, PARTICLES = 6, 11, 6714


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def record(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def preview_count(manifest):
    """A completed prefix is announced only after native save/flush finishes."""
    frames = manifest.get("savedFrames", 0)
    if (manifest.get("scenario") != "urmi-damage40"
            or manifest.get("phase") != "undrained-dynamic"
            or manifest.get("status") != "running"
            or manifest.get("complete") is not False
            or type(frames) is not int or frames < MINIMUM_FRAMES):
        return None
    require(manifest.get("particleCount") == PARTICLES, "Preview particle contract differs")
    return min(frames, MAXIMUM_FRAMES)


def copy_closed(source, destination):
    """Copy an already closed immutable output, preserving every original byte."""
    before = record(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    copied, after = record(destination), record(source)
    require(before["bytes"] == after["bytes"] == copied["bytes"]
            and before["sha256"] == after["sha256"] == copied["sha256"],
            f"Closed saved input changed during copy: {source}")
    return {"mode": "CLOSED_FILE_EXACT_COPY", "sourceBefore": before,
            "sourceAfter": after, "copy": copied}


def _number(value):
    result = float(value.replace("D", "e").replace("d", "e"))
    require(math.isfinite(result), "Nonfinite selected CSV prefix")
    return result


def copy_csv_prefix(source, destination, frames, particles=None):
    """Copy complete raw lines only; ignore later frames and an active writer tail.

    Selected rows must already end in a newline. Re-reading exactly the copied
    byte count proves that the selected prefix was unchanged, while later file
    growth is permitted. No CSV value/newline is re-serialized.
    """
    count = particles if particles is not None else 1
    require(frames > 0 and count > 0, "Empty prefix is not a preview")
    digest, copied_bytes = hashlib.sha256(), 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as original, destination.open("xb") as target:
        header = original.readline()
        require(header.endswith(b"\n"), "Incomplete selected CSV header")
        columns = next(csv.reader([header.decode("utf-8-sig")]))
        require(columns and len(columns) == len(set(columns)) and "frame" in columns,
                "Missing or duplicate prefix header")
        frame_index = columns.index("frame")
        id_index = columns.index("particle_id") if particles is not None else None
        target.write(header)
        digest.update(header)
        copied_bytes += len(header)
        for frame in range(frames):
            for identity in range(count):
                line = original.readline()
                require(line.endswith(b"\n"), f"Selected frame {frame} is not fully flushed")
                row = next(csv.reader([line.decode("utf-8")]))
                require(len(row) == len(columns) and all(row), "Incomplete selected CSV row")
                values = [_number(value) for value in row]
                require(values[frame_index] == frame, "Selected prefix frame/order differs")
                if id_index is not None:
                    require(values[id_index] == identity, "Selected prefix particle IDs differ")
                target.write(line)
                digest.update(line)
                copied_bytes += len(line)
    expected, reread, remaining = digest.hexdigest(), hashlib.sha256(), copied_bytes
    with source.open("rb") as stream:
        while remaining:
            block = stream.read(min(1024 * 1024, remaining))
            require(block, "Selected CSV prefix was truncated during copy")
            reread.update(block)
            remaining -= len(block)
    copied = record(destination)
    require(reread.hexdigest() == expected == copied["sha256"] and copied["bytes"] == copied_bytes,
            "Selected CSV prefix changed during copy")
    return {"mode": "EXACT_COMPLETE_RAW_PREFIX", "sourcePath": str(source.resolve()),
            "copiedBytes": copied_bytes, "prefixSha256Before": expected,
            "prefixSha256After": reread.hexdigest(), "copy": copied,
            "frames": frames, "dataRows": frames * count, "particlesPerFrame": particles,
            "laterNativeRowsExcluded": True, "nativeFileNeverWritten": True}


def imported(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def checked_relative(run, relative):
    require(isinstance(relative, str), "Missing native relative input path")
    require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
            "Native input must be a contained relative path")
    path = (run / relative).resolve()
    require(path.is_relative_to(run), "Native input path escapes run")
    return path


def snapshot_prefix(run, output, observed, frames):
    data = output / "saved-prefix"
    data.mkdir()
    # Native manifest is an unchanged historical observation, never a fabricated
    # terminal/failed/complete run and never fed to the terminal inspector.
    shutil.copyfile(output / "observed-native-manifest.json", data / "manifest.json")
    bindings = []
    for key in ("preparationHistoryFile", "preparationStateFile", "preparationParticleFile",
                "initialVtk", "drainedVtk", "transferLedgerFile"):
        relative = observed[key]
        source = checked_relative(run, relative)
        bindings.append(copy_closed(source, data / relative))
    for key, particles in (("historyFile", None), ("particleFile", PARTICLES)):
        relative = observed[key]
        bindings.append(copy_csv_prefix(checked_relative(run, relative), data / relative, frames, particles))
    for frame in range(frames):
        relative = observed["dynamicVtkPattern"] % frame
        bindings.append(copy_closed(checked_relative(run, relative), data / relative))
    write(output / "saved-prefix-binding.json", {"scope": SCOPE, "copiedUtc": now(),
          "sourceRun": str(run), "selectedFrames": frames, "records": bindings,
          "nativeManifestRewritten": False, "activeTailNeverParsed": True})
    return data, bindings


def inspect_prefix(run, data, manifest, contract, frames, helper, read_vtk):
    require(contract["serialization"] == {"absolute": helper.ATOL, "relative": helper.RTOL,
            "timeAbsolute": helper.TIME_ATOL, "timeRelative": helper.TIME_RTOL}, "Frozen tolerances differ")
    for key, expected in contract["configuration"].items():
        require(key in manifest["config"] and helper.close(manifest["config"][key], expected),
                f"Observed native configuration differs: {key}")
    sources = helper.verified_sources(run)
    helper.verify_law_source(run, contract["material"])
    nodes, bound = helper.reference_table(contract["material"])
    require(manifest["model"]["referencePdfSha256"] == contract["referencePdfSha256"]
            and helper.close(manifest["model"]["tableNodes_s_kappa_cPa"], nodes)
            and helper.close(manifest["model"]["maximumErrorBoundPa"], bound), "Frozen law identity differs")
    preparation = helper.preparation_check(data / manifest["preparationHistoryFile"], contract, True)
    prep_history = helper.history_rows(data / manifest["preparationStateFile"])
    require(set(prep_history) == {0, 1}, "Closed preparation lacks both actual snapshots")
    baseline, previous, drained, prep_audits = None, None, None, []
    for frame, values in helper.csv_frames(data / manifest["preparationParticleFile"]):
        require(frame == len(prep_audits) and frame in (0, 1), "Preparation snapshot order differs")
        vtk = data / manifest["initialVtk" if frame == 0 else "drainedVtk"]
        baseline, audit, _, _, _ = helper.audit_frame(values, prep_history[frame], vtk, read_vtk,
                baseline, previous, frame, contract, sources["constants"], nodes)
        require(audit["particleCount"] == PARTICLES, "Preparation particle count differs")
        prep_audits.append(audit)
        if frame == 1:
            drained = {key: value.copy() for key, value in values.items()}
        previous = {key: values[key].copy() for key in ("mc_kappa", "plastic_work_pa")}
    require(len(prep_audits) == 2 and drained is not None, "Incomplete closed preparation snapshots")
    history = helper.history_rows(data / manifest["historyFile"])
    require(set(history) == set(range(frames)), "Selected history prefix differs")
    audits, transfer = [], None
    for frame, values in helper.csv_frames(data / manifest["particleFile"]):
        require(frame == len(audits) and frame < frames, "Selected dynamic frame order differs")
        phase = 2 if frame == 0 else 3
        baseline, audit, _, _, _ = helper.audit_frame(values, history[frame],
                data / (manifest["dynamicVtkPattern"] % frame), read_vtk, baseline, previous,
                phase, contract, sources["constants"], nodes)
        require(audit["particleCount"] == PARTICLES, "Selected particle count differs")
        require(helper.close(audit["timeS"], .2 * frame, time=True)
                and helper.close(audit["nativeTimeS"] - manifest["transferNativeTimeS"], audit["timeS"], time=True),
                "Selected physical/native clock differs")
        if frame == 0:
            transfer = helper.transfer_check(data, manifest, drained, values)
        audits.append(audit)
        previous = {key: values[key].copy() for key in ("mc_kappa", "plastic_work_pa")}
    require(len(audits) == frames, "Selected dynamic prefix incomplete")
    # Native unique IDs are preserved identities, not the CSV logical row index.
    # audit_frame already checks uniqueness and exact identity across snapshots.
    return {"schema": "cl-mpm.urmi-strength-damage40.live-preview.v1", "createdUtc": now(),
            "reviewScope": SCOPE, "prefixIntegrity": "PASS", "sourceRun": str(run),
            "sourceProof": sources, "preparation": preparation, "transfer": transfer,
            "preparationSnapshots": prep_audits, "states": audits, "selectedFrames": frames,
            "selectedParticleRows": frames * PARTICLES, "actualDynamicLastTimeS": audits[-1]["timeS"],
            "observedNativeStatus": manifest["status"], "observedNativeComplete": manifest["complete"],
            "observedNativePhase": manifest["phase"], "observedNativeSavedFrames": manifest["savedFrames"],
            "completeNativeRun": False, "landslideVerified": False, "scientificallyValidated": False,
            "automaticMotionVerdict": False, "manualSpatialReviewRequired": True,
            "limitations": contract["limits"] + ["Active saved prefix only; full60s trial remains unfinished",
                "First frame is the actual instantaneous material release, not elapsed dynamic deformation",
                "No whole-run motion/runout or unsaved-state validation is inferred",
                "All saved particles are shown; D_s is strength loss, not fracture opening"]}


def render_preview(report, output, contract, read_vtk, video):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    frames = output / "actual-preview-frames"
    frames.mkdir()
    config, states = contract["configuration"], report["states"]
    for state in states:
        points, fields = read_vtk(Path(state["vtk"]["path"]))
        fig, ax = plt.subplots(figsize=(15, 5.5), constrained_layout=True)
        dots = ax.scatter(points[:, 0], points[:, 1], c=fields["mc-strength-damage"],
                          cmap="inferno", norm=Normalize(0, 1), s=5, linewidths=0)
        ax.set(xlim=(-.5, config["domainWidth"] + .5), ylim=(-.5, config["domainHeight"] + .5),
               xlabel="x (m)", ylabel="y (m)")
        ax.set_aspect("equal", adjustable="box")
        event = "instantaneous material release; no clock advance" if state["phaseCode"] == 2 else "actual undrained dynamics"
        ax.set_title(f"ACTIVE PARTIAL PREVIEW: first {states[-1]['timeS']:.1f}s of requested60s; no full validation\n"
                     f"{event}; dynamic t={state['timeS']:.3f}s, native t={state['nativeTimeS']:.6f}s; all6714 particles / scale1")
        fig.colorbar(dots, ax=ax, label="MC strength loss D_s=1-c/40.5kPa (not crack opening)", shrink=.75)
        fig.savefig(frames / f"frame_{state['frame']:04d}.png", dpi=120)
        if state is states[-1]:
            fig.savefig(output / "first-strength-damage-preview.png", dpi=150)
        plt.close(fig)
    media = {"status": "PASS", "scope": SCOPE, "actualStates": len(states), "interpolation": False,
             "coordinateScale": 1, "colourRange": [0, 1], "allParticlesShown": True,
             "summary": record(output / "first-strength-damage-preview.png")}
    if video:
        executable = shutil.which("ffmpeg")
        if executable is None:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        destination = output / "first-strength-damage-preview.mp4"
        fps = contract["media"]["framesPerSecond"]
        command = [executable, "-v", "error", "-y", "-framerate", str(fps), "-i", str(frames / "frame_%04d.png"),
                   "-frames:v", str(len(states)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                   "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", str(destination)]
        write(output / "video-command.json", command)
        encoded = subprocess.run(command, capture_output=True, text=True)
        (output / "video.stderr.log").write_text(encoded.stderr, encoding="utf-8")
        require(encoded.returncode == 0, "Preview encoding failed; saved prefix retained")
        decode_command = [executable, "-v", "error", "-nostats", "-progress", "pipe:1", "-i", str(destination), "-f", "null", "-"]
        write(output / "video-decode-command.json", decode_command)
        decoded = subprocess.run(decode_command, capture_output=True, text=True)
        (output / "video-decode.stdout.log").write_text(decoded.stdout, encoding="utf-8")
        (output / "video-decode.stderr.log").write_text(decoded.stderr, encoding="utf-8")
        decoded_counts = [int(line.split("=", 1)[1]) for line in decoded.stdout.splitlines() if line.startswith("frame=")]
        require(decoded.returncode == 0 and not decoded.stderr.strip() and decoded_counts and decoded_counts[-1] == len(states),
                "Preview full decode/frame count failed")
        media.update(video=record(destination), decodedFrames=decoded_counts[-1], fullDecodeExitCode=0,
                     framesPerSecond=fps, playbackDurationS=len(states) / fps)
    return media


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preparation-dir", type=Path, help="Default RUN-launch-preparation; exact existing prepared bytes")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--frozen-analysis-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    run, output = args.run_dir.resolve(), args.output_dir.resolve()
    preparation = (args.preparation_dir or Path(str(run) + "-launch-preparation")).resolve()
    if args.frozen_analysis_dir is None:
        # Do not create any preview directory or parse active CSV/VTK until the
        # native producer declares at least six finished dynamic frames.
        try:
            observed_bytes = (run / "manifest.json").read_bytes()
            observed = json.loads(observed_bytes.decode("utf-8-sig"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            print(json.dumps({"status": "NOT_READY", "reason": f"Native manifest unavailable during write: {type(error).__name__}", "previewCreated": False}))
            return 0
        frames = preview_count(observed)
        if frames is None:
            print(json.dumps({"status": "NOT_READY", "phase": observed.get("phase"), "savedFrames": observed.get("savedFrames"),
                              "requiredDynamicFrames": MINIMUM_FRAMES, "previewCreated": False}))
            return 0
        require(not output.exists(), "Choose a fresh preview directory")
        # Require the original launch preparation's hash binding, not merely a
        # current repository helper that may have changed after launch.
        prepared = load(preparation / "preparation.json")
        selected = [Path(__file__).resolve(), preparation / "analysis/review-urmi-damage40.py",
                    preparation / "analysis/plot_m5_cliff_comparison.py", preparation / "protocol/contract.json"]
        bindings = {Path(row["copy"]["path"]).resolve(): row["copy"] for row in prepared["support"]}
        for path in selected[1:]:
            actual = record(path)
            require(path.resolve() in bindings and actual["sha256"] == bindings[path.resolve()]["sha256"]
                    and actual["bytes"] == bindings[path.resolve()]["bytes"], f"Original prepared support binding differs: {path}")
        frozen = output / "analysis-source"
        frozen.mkdir(parents=True)
        (output / "observed-native-manifest.json").write_bytes(observed_bytes)
        records = [copy_closed(path, frozen / path.name) for path in selected]
        write(output / "preview-plan.json", {"scope": SCOPE, "observedUtc": now(), "selectedFrames": frames,
              "observedManifest": record(output / "observed-native-manifest.json"), "sourceRun": str(run),
              "launchPreparation": record(preparation / "preparation.json"), "requestedSeconds": 60})
        write(output / "analysis-freeze.json", {"createdUtc": now(), "records": records,
              "scope": "New preview and original prepared helper/reader/contract copied before child execution; preview itself was not pre-native"})
        command = [sys.executable, str(frozen / Path(__file__).name), "--run-dir", str(run), "--output-dir", str(output),
                   "--preparation-dir", str(preparation), "--frozen-analysis-dir", str(frozen)]
        if args.video:
            command.append("--video")
        write(output / "command.json", command)
        with (output / "stdout.log").open("w", encoding="utf-8") as stdout, (output / "stderr.log").open("w", encoding="utf-8") as stderr:
            child = subprocess.run(command, stdout=stdout, stderr=stderr)
        write(output / "exit.json", {"exitCode": child.returncode, "finishedUtc": now(), "nativeSolverRerun": False})
        return child.returncode
    stage = "saved-prefix-copy"
    try:
        frozen = args.frozen_analysis_dir.resolve()
        helper = imported(frozen / "review-urmi-damage40.py", "urmi_preview_frozen_audit")
        reader = imported(frozen / "plot_m5_cliff_comparison.py", "urmi_preview_frozen_reader")
        manifest, plan, contract = load(output / "observed-native-manifest.json"), load(output / "preview-plan.json"), load(frozen / "contract.json")
        frames = preview_count(manifest)
        require(frames == plan["selectedFrames"], "Captured preview selection differs")
        data, bindings = snapshot_prefix(run, output, manifest, frames)
        stage = "saved-prefix-audit"
        report = inspect_prefix(run, data, manifest, contract, frames, helper, reader.read_cliff_vtk)
        report["savedPrefixBinding"] = record(output / "saved-prefix-binding.json")
        report["analysisBinding"] = load(output / "analysis-freeze.json")
        write(output / "prefix-integrity.json", report)
        stage = "saved-prefix-media"
        report["media"] = render_preview(report, output, contract, reader.read_cliff_vtk, args.video)
        write(output / "preview.json", report)
        print(json.dumps({"status": "PREVIEW_READY", "scope": SCOPE, "actualFrames": frames,
              "actualLastTimeS": report["actualDynamicLastTimeS"], "completeNativeRun": False, "scientificallyValidated": False}))
        return 0
    except Exception as error:
        write(output / "stage-failure.json", {"scope": SCOPE, "stage": stage, "error": str(error),
              "traceback": traceback.format_exc(), "nativeSolverRerun": False, "savedInputsPreserved": True})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
