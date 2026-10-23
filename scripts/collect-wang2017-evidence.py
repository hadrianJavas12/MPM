"""Archive completed native benchmark evidence without changing any run output."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(destination, files):
    members = []
    with destination.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as tar:
            for relative, path in sorted(files):
                data = path.read_bytes()
                info = tarfile.TarInfo(relative)
                info.size, info.mtime = len(data), 0
                tar.addfile(info, io.BytesIO(data))
                members.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    with tarfile.open(destination, "r:gz") as tar:
        actual = tar.getmembers()
        assert len(actual) == len(members)
        for member, expected in zip(actual, members):
            data = tar.extractfile(member).read()
            assert member.name == expected["path"] and len(data) == expected["bytes"]
            assert hashlib.sha256(data).hexdigest() == expected["sha256"]
    return {"archive": destination.name, "allMemberBytesVerified": True, "members": members}


def existing_run_controls(run, status_path):
    # Older runners used .log; modern Windows wrappers split native and monitor logs.
    controls = {status_path.name: status_path}
    for suffix in ("-launch.json", ".log", ".stdout.log", ".stderr.log", "-plot.log", "-collect.log",
                   "-wrapper.stdout.log", "-wrapper.stderr.log"):
        path = run.parent / (run.name + suffix)
        if path.is_file():
            controls[path.name] = path
    for path in run.parent.glob(run.name + "-monitor-*-ready.json"):
        if path.is_file():
            controls[path.name] = path
    detached = run.parent / (run.name + "-detached")
    if detached.is_dir():
        for path in detached.rglob("*"):
            if path.is_file():
                controls[detached.name + "/" + path.relative_to(detached).as_posix()] = path
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    run, dest = args.run_dir.resolve(), args.destination.resolve()
    run.relative_to(ROOT / "output")
    dest.relative_to(ROOT / "docs/evidence")
    status_path = run.parent / (run.name + "-status.json")
    manifest, audit, status = read(run / "manifest.json"), read(run / "output-audit.json"), read(status_path)
    assert status["exitCode"] == 0 and manifest["complete"] is True
    assert audit["passedConsistencyChecks"] and audit["nativeComplete"]
    dest.mkdir(parents=True, exist_ok=False)
    (dest / ".gitattributes").write_text("* -text -whitespace\n*.gz binary\n", encoding="utf-8")
    for name in ("manifest.json", "output-audit.json", "source-provenance.json", "descent-overview.png", "energy-diagnostics.png", "slope-descent.mp4"):
        path = run / name
        if path.exists():
            shutil.copyfile(path, dest / name)
    archives = [archive(dest / "native-output.tar.gz", [(p.relative_to(run).as_posix(), p)
            for p in run.rglob("*") if p.is_file() and "source" not in p.relative_to(run).parts
            and "rendered-frames" not in p.relative_to(run).parts
            and p.suffix not in (".png", ".mp4")])]
    archives.append(archive(dest / "executed-source.tar.gz", [(p.relative_to(run / "source").as_posix(), p)
            for p in (run / "source").rglob("*") if p.is_file()
            and ".native-cache" not in p.parts]))
    support = dest / "support"
    support.mkdir()
    for name in ("plot-wang2017-descent.py", "plot_m5_cliff_comparison.py", "collect-wang2017-evidence.py"):
        shutil.copyfile(ROOT / "scripts" / name, support / name)
    contract_status = run.parent / "contracts-002-status.json"
    if contract_status.exists():
        commit = read(contract_status)["sourceCommitAtLaunch"]
        test_bytes = subprocess.check_output(["git", "show", commit + ":tests/benchmarks/wang2017-descent.lisp"], cwd=ROOT)
        (support / "executed-contracts-test.lisp").write_bytes(test_bytes)
    fast_status = run.parent / "fast-contracts-status.json"
    if fast_status.exists():
        commit = read(fast_status)["sourceCommitAtLaunch"]
        (support / "executed-fast-contracts-test.lisp").write_bytes(subprocess.check_output(
            ["git", "show", commit + ":tests/benchmarks/wang2017-fast-contracts.lisp"], cwd=ROOT))
    controls = existing_run_controls(run, status_path)
    for pattern in ("*contracts*.json", "*contracts*.log", "framework-components*", "node-*"):
        controls.update((p.name, p) for p in run.parent.glob(pattern) if p.is_file())
    failed = run.parent / "expected-gravity-failure-001/manifest.json"
    if failed.exists():
        controls["expected-gravity-failure-manifest.json"] = failed
    estimate = run.parent / "runtime-estimate.json"
    if estimate.exists():
        controls[estimate.name] = estimate
    archives.append(archive(dest / "control-logs.tar.gz", controls.items()))
    (dest / "archive-verification.json").write_text(json.dumps(
        {"passed": True, "method": "Reopen all archives and compare every member byte length and SHA-256 to the collected input", "archives": archives},
        indent=2) + "\n", encoding="utf-8")
    support_proof = {}
    for name in ("plot-wang2017-descent.py", "plot_m5_cliff_comparison.py", "collect-wang2017-evidence.py"):
        relative = "scripts/" + name
        current_hash = digest(support / name)
        launch_hash = status.get("postprocessorSha256", {}).get(relative)
        matches = current_hash == launch_hash.lower() if launch_hash else None
        if name != "collect-wang2017-evidence.py" and launch_hash:
            assert matches, "Renderer/reader changed since native launch: " + relative
        support_proof[relative] = {"sha256AtCollection": current_hash, "sha256RecordedAtNativeLaunch": launch_hash,
                                  "matchesNativeLaunchHash": matches,
                                  "role": "Executed evidence packager after native completion; not a native-executed source" if name.startswith("collect-") else "Saved-output renderer/reader"}
    (dest / "collection-source-proof.json").write_text(json.dumps(
        {"nativeAlreadyComplete": True, "support": support_proof}, indent=2) + "\n", encoding="utf-8")
    config = manifest["config"]
    rate = config["velocity"] / 1e-4
    full = config["targetDisplacement"] >= .1
    kind = "accelerated-rate trial" if abs(rate - 1) > 1e-10 else ("reference-rate target" if full else "pilot")
    summary = {"scope": "Completed " + kind + "; not verified Figure3 reproduction",
               "sourceCommitAtNativeLaunch": status["sourceCommitAtLaunch"],
               "nativeExitCode": status["exitCode"], "run": audit,
               "loadingRateMultiplier": rate,
               "configuredTargetRun": "COMPLETE",
               "configuredTargetDisplacementM": config["targetDisplacement"],
               "actualCommandedSettlementM": manifest["commandedSettlementM"],
               "actualMeasuredSettlementM": manifest["measuredSettlementM"],
               "configuredDurationS": config["duration"], "actualPhysicalTimeS": manifest["timeS"],
               "historicalFullBenchmarkTargetM": .1,
               "historicalFullBenchmarkTargetSource": "Project comparison endpoint; not newly verified from the paper",
               "fullTargetRun": ("COMPLETE_ACCELERATED" if abs(rate-1)>1e-10 else "COMPLETE_REFERENCE_RATE") if full else "NOT_RUN",
               "referenceRateFullTargetRun": "COMPLETE" if full and abs(rate-1)<1e-10 else "NOT_RUN",
               "reliefHeightM": config["height"],
               "reliefHeightSource": "ASSUMPTION: not numerically dimensioned in Figure2",
               "referenceCurveAgreement": "NOT_VERIFIED: assumed geometry/control, possible dynamics and no digitized reference comparison",
               "scientificValidation": False}
    (dest / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (dest / "README.md").write_text(
        "# Wang2017 prescribed descent evidence\n\n"
        f"Real Windows MPM {kind}; loading velocity {config['velocity']:g} m/s "
        f"({rate:g}x reference), target {config['targetDisplacement']:g} m over {config['duration']:g} s. "
        f"The configured target run is COMPLETE: actual time {manifest['timeS']:g} s, commanded descent {manifest['commandedSettlementM']:g} m. "
        f"The historical project 0.1m full-benchmark status is {summary['fullTargetRun']}; "
        f"the reference-rate full-target status is {summary['referenceRateFullTargetRun']}. "
        "That historical endpoint is not newly verified from the paper. "
        f"Relief height {config['height']:g} m and bottom tangential fixity are assumptions; finite penalty compliance is measured separately. "
        "Exact executed source (except private compiled cache) and raw VTK/CSV are archived. "
        "Every archive member was reopened and checked against collected input bytes. "
        "The collector in support/ was executed after native completion and may differ from the collector hash recorded at native launch; "
        "it is not part of the native-executed source claim. Renderer/reader hashes are checked separately in collection-source-proof.json. "
        "Control logs are attributed separately; an expected negative control is not a successful physical run. "
        "No FEM local-arc solver equivalence, peak-load reproduction or laboratory validation is claimed.\n",
        encoding="utf-8")
    entries = [{"path": p.relative_to(dest).as_posix(), "sha256": digest(p), "bytes": p.stat().st_size}
               for p in sorted(dest.rglob("*")) if p.is_file()]
    (dest / "evidence-manifest.json").write_text(json.dumps({"entries": entries}, indent=2) + "\n", encoding="utf-8")
    assert all(digest(dest / row["path"]) == row["sha256"] for row in entries)
    print(json.dumps({"verifiedArtifacts": len(entries), "path": str(dest)}))


if __name__ == "__main__":
    main()
