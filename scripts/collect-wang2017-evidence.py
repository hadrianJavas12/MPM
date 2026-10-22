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
    with destination.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as tar:
            for relative, path in sorted(files):
                data = path.read_bytes()
                info = tarfile.TarInfo(relative)
                info.size, info.mtime = len(data), 0
                tar.addfile(info, io.BytesIO(data))


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
    for name in ("manifest.json", "output-audit.json", "source-provenance.json", "descent-overview.png", "slope-descent.mp4"):
        path = run / name
        if path.exists():
            shutil.copyfile(path, dest / name)
    archive(dest / "native-output.tar.gz", [(p.relative_to(run).as_posix(), p)
            for p in run.rglob("*") if p.is_file() and "source" not in p.relative_to(run).parts
            and "rendered-frames" not in p.relative_to(run).parts
            and p.suffix not in (".png", ".mp4")])
    archive(dest / "executed-source.tar.gz", [(p.relative_to(run / "source").as_posix(), p)
            for p in (run / "source").rglob("*") if p.is_file()
            and ".native-cache" not in p.parts])
    support = dest / "support"
    support.mkdir()
    for name in ("plot-wang2017-descent.py", "plot_m5_cliff_comparison.py", "collect-wang2017-evidence.py"):
        shutil.copyfile(ROOT / "scripts" / name, support / name)
    contract_status = run.parent / "contracts-002-status.json"
    if contract_status.exists():
        commit = read(contract_status)["sourceCommitAtLaunch"]
        test_bytes = subprocess.check_output(["git", "show", commit + ":tests/benchmarks/wang2017-descent.lisp"], cwd=ROOT)
        (support / "executed-contracts-test.lisp").write_bytes(test_bytes)
    controls = [(status_path.name, status_path),
                (run.name + ".log", run.parent / (run.name + ".log"))]
    for pattern in ("contracts-002*", "framework-components*", "node-*"):
        controls.extend((p.name, p) for p in run.parent.glob(pattern) if p.is_file())
    failed = run.parent / "expected-gravity-failure-001/manifest.json"
    if failed.exists():
        controls.append(("expected-gravity-failure-manifest.json", failed))
    estimate = run.parent / "runtime-estimate.json"
    if estimate.exists():
        controls.append((estimate.name, estimate))
    archive(dest / "control-logs.tar.gz", controls)
    summary = {"scope": "Completed physical-speed pilot; not full Figure3 reproduction",
               "sourceCommitAtNativeLaunch": status["sourceCommitAtLaunch"],
               "nativeExitCode": status["exitCode"], "pilot": audit,
               "fullTargetRun": "NOT_RUN", "reliefHeightM": manifest["config"]["height"],
               "reliefHeightSource": "ASSUMPTION: not numerically dimensioned in Figure2",
               "referenceCurveAgreement": "NOT_VERIFIED: short prefix and initial reaction transients",
               "scientificValidation": False}
    (dest / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (dest / "README.md").write_text(
        "# Wang2017 prescribed descent pilot\n\n"
        "Real Windows MPM output; physical velocity 1e-4 m/s, 1-second pilot. "
        "The 0.1 m / 1000 s case was not run. See summary.json for actual native source commit. "
        "Relief height 10 m is an assumption; finite penalty compliance is measured separately. "
        "Exact executed source (except private compiled cache) and raw VTK/CSV are archived. "
        "Control logs include an expected one-step gravity failure, not a successful physical run. "
        "No FEM local-arc solver equivalence, peak-load reproduction or laboratory validation is claimed.\n",
        encoding="utf-8")
    entries = [{"path": p.relative_to(dest).as_posix(), "sha256": digest(p), "bytes": p.stat().st_size}
               for p in sorted(dest.rglob("*")) if p.is_file()]
    (dest / "evidence-manifest.json").write_text(json.dumps({"entries": entries}, indent=2) + "\n", encoding="utf-8")
    assert all(digest(dest / row["path"]) == row["sha256"] for row in entries)
    print(json.dumps({"verifiedArtifacts": len(entries), "path": str(dest)}))


if __name__ == "__main__":
    main()
