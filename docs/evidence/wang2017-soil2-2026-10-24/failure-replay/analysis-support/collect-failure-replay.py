"""Archive existing actual-capsule replay evidence; no replay/test/solver calls."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    repo, destination = Path(args.repository).resolve(), Path(args.destination).resolve()
    raw_root = repo / "output/wang2017-soil2-2026-10-24"
    failed_run = raw_root / "fast-010-001"
    expected_capsule = "05835d5429292da0b95190232c0d3fb4d6228d6fd08d975ee1346434ba99242d"
    assert not destination.exists(), "Evidence destination must be fresh."
    original_manifest = load(failed_run / "source/source-manifest.json")
    original_records = {row["path"]: row for row in original_manifest["files"]}
    assert len(original_records) == 271
    original_capsule = (failed_run / "mc-integration-failure.json").read_bytes()
    assert sha(original_capsule) == expected_capsule
    source_checks, immutable_inputs = {}, {}
    def read_static(path):
        data = path.read_bytes()
        immutable_inputs[str(path)] = sha(data)
        return data
    for relative, row in original_records.items():
        data = read_static(failed_run / relative)
        assert len(data) == row["bytes"] and sha(data) == row["sha256"].lower(), relative
    destination.mkdir(parents=True)
    (destination / "archive-member-manifests").mkdir()
    (destination / "analysis-support").mkdir()
    shutil.copy2(__file__, destination / "analysis-support/collect-failure-replay.py")
    archives = []
    for name in ["failure-replay-001", "failure-replay-002"]:
        root = raw_root / name
        records = load(root / "source/source-manifest.json")["files"]
        assert len(records) == 272
        by_path = {row["path"]: row for row in records}
        assert set(by_path) == set(original_records) | {"source/replay-driver.lisp"}
        checks = []
        for relative, row in by_path.items():
            data = read_static(root / relative)
            assert len(data) == row["bytes"] and sha(data) == row["sha256"].lower(), relative
            if relative in original_records:
                assert sha(data) == original_records[relative]["sha256"].lower()
                assert data == (failed_run / relative).read_bytes()
            checks.append({"path": relative, "bytes": len(data), "sha256": sha(data), "matchesActualFailedRun": relative in original_records})
        assert (root / "mc-integration-failure.json").read_bytes() == original_capsule
        execution = load(root / "execution.json")
        if name.endswith("001"):
            failure = load(root / "failure.json")
            assert execution["exitCode"] == 1 and failure["actualCapsuleReplayCalls"] == 0
        else:
            result = load(root / "replay-result.json")
            assert execution["exitCode"] == 0 and result["actualCapsuleReplayCalls"] == 1
            assert result["physicalUpdates"] == 0 and result["expectedRejection"] is True
            assert result["capsuleSha256"] == expected_capsule
            before, after = load(root / "source-provenance-before.json"), load(root / "source-provenance-after.json")
            assert before["nativeBackend"] == after["nativeBackend"]
            assert before["nativeBackend"]["sha256"].lower() == by_path["source/libs/kirchoff.dll"]["sha256"].lower()
            driver_current = repo / "tests/benchmarks/wang2017-soil2-failure-replay.lisp"
            assert read_static(driver_current) == (root / "source/replay-driver.lisp").read_bytes()
        source_checks[name] = checks
        members, excluded = [], []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if ".native-cache" in relative.parts or path.suffix.lower() == ".fasl":
                excluded.append({"path": relative.as_posix(), "bytes": path.stat().st_size})
            else:
                members.append((path, name + "/" + relative.as_posix()))
        archive_path = destination / (name + ".zip")
        member_records = []
        with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, member in members:
                data = read_static(path)
                archive.writestr(member, data)
                member_records.append({"path": member, "bytes": len(data), "sha256": sha(data)})
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.testzip() is None
            assert sorted(archive.namelist()) == sorted(row["path"] for row in member_records)
            for row in member_records:
                data = archive.read(row["path"])
                assert len(data) == row["bytes"] and sha(data) == row["sha256"]
        member_manifest = "archive-member-manifests/" + name + ".json"
        save(destination / member_manifest, {"archive": archive_path.name, "members": member_records, "excludedPrivateCacheOrFasl": excluded})
        archives.append({"path": archive_path.name, "bytes": archive_path.stat().st_size, "sha256": sha(archive_path.read_bytes()), "verifiedMembers": len(member_records), "memberManifest": member_manifest, "excludedFiles": len(excluded), "excludedBytes": sum(row["bytes"] for row in excluded)})
    # Direct readable mirrors; archived originals remain byte-exact.
    for source, target in [
        (failed_run / "mc-integration-failure.json", "original-mc-integration-failure.json"),
        (failed_run / "source/source-manifest.json", "original-failed-source-manifest.json"),
        (failed_run / "source-provenance.json", "original-failed-source-provenance.json"),
        (failed_run.with_name(failed_run.name + "-status.json"), "original-failed-run-status.json"),
        (raw_root / "failure-replay-002/diagnosis.md", "diagnosis.md"),
        (raw_root / "failure-replay-002/candidate-admissibility.json", "candidate-admissibility.json"),
        (raw_root / "failure-replay-002/replay-result.json", "replay-result.json"),
    ]:
        (destination / target).write_bytes(read_static(source))
    source_proof_path = destination / "source-integrity-verification.json"
    save(source_proof_path, {"status": "PASS", "actualFailedRunSourceCount": len(original_records), "replaySourcesPerAttempt": 272,
        "failedSourcesRetainedAndMatchedInEachReplay": 271, "exactOriginalCapsuleSha256": expected_capsule,
        "currentReplayTestEqualsExecuted002Driver": True, "sourceFiles": source_checks})
    unchanged = all(sha(Path(path).read_bytes()) == expected for path, expected in immutable_inputs.items())
    assert unchanged
    save(destination / "archive-verification.json", {"status": "PASS", "verifiedUtc": datetime.now(timezone.utc).isoformat(),
        "archives": archives, "totalVerifiedMembers": sum(row["verifiedMembers"] for row in archives),
        "originalInputsUnchangedDuringPackaging": unchanged, "numericalTestsOrReplaysExecutedByCollector": 0,
        "scope": "Archive/hash verification only; native002 exit0 means expected captured rejection reproduced once, not simulation or scientific PASS."})
    (destination / "README.md").write_text("""# Actual Soil2 failure replay evidence

The first full Soil2 slope run `fast-010-001` failed natively with exit1 on source
`621146b`. Its exact failure capsule is retained here unchanged. The last saved
loading state was5.7s/57mm, which is not the exact rejected-substep time.

| Diagnostic attempt | Actual result | Meaning |
| --- | --- | --- |
| `failure-replay-001` | Native exit1; zero actual capsule-replay calls; zero physical updates | A diagnostic helper named BOOLEAN collided with the inherited COMMON-LISP symbol/package lock. The harness failed before replay. Raw log, failure record, exact driver/source and before-runtime proof remain intact. |
| `failure-replay-002` | Native exit0; exactly one actual capsule-replay call; zero physical updates | Renamed diagnostic helper only. The expected rejection was reproduced using the actual failed input. This is a successful diagnostic replay, **not** a successful slope simulation or scientific PASS. |

All271 source files/DLL from the actual failed run match its pre-load manifest.
Each diagnostic archive retains those exact271 files plus its own new driver,
for272 hashed source files per attempt. Current
`tests/benchmarks/wang2017-soil2-failure-replay.lisp` is byte-identical to the
executed002 driver. No EOF trimming or source changes were performed by packaging.
The002 actual mapped copied DLL and its hash match the before/after Windows API
proof. Third-party dependencies remain external to the first-party source claim.

The exact original capsule SHA256 is
`05835d5429292da0b95190232c0d3fb4d6228d6fd08d975ee1346434ba99242d`.
`diagnosis.md` and `candidate-admissibility.json` are readable copies of the
existing002 diagnosis and candidate tables. They explain why the captured
coupled cohesion-softening/zero-dilation return has no admissible solution. The
expected rejection is neither a monotonic-history violation nor an ambiguity
silently resolved by choosing a root. No material parameter, production equation,
tolerance, apex convention or solver trajectory was altered to obtain this result.
It does not prove every smaller-step trajectory or the paper FEM must fail.

The two ZIPs preserve all available diagnostic raw logs, execution/failure/result
records, candidate tables, source manifests/copied sources, capsule and runtime
proofs. Private `.native-cache` and `.fasl` files are excluded and listed by path
and size in each member manifest; their original raw directories remain intact.
Their references in runtime provenance do not mean omitted compiled files are
included. This packet does not archive the full failed run's VTK/CSV/media; that
evidence is collected separately. Packaging reads no raw VTK or process/PID state.

Every archived member is decoded and checked for byte length/SHA256, complete
name inventory and ZIP CRC. All original input bytes were checked unchanged.
`archive-member-manifests/`, `archive-verification.json`,
`source-integrity-verification.json`, `evidence-manifest.json` and `SHA256SUMS`
retain these checks. The final two self-referential index files are excluded
from their own artifact list. Exact collector source is under `analysis-support/`.
No replay, numerical test or solver was executed during packaging.
""", encoding="utf-8")
    (destination / ".gitattributes").write_text("* -text -whitespace\n", encoding="ascii")
    artifacts = []
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name not in {"evidence-manifest.json", "SHA256SUMS"}:
            data = path.read_bytes()
            artifacts.append({"path": path.relative_to(destination).as_posix(), "bytes": len(data), "sha256": sha(data)})
    save(destination / "evidence-manifest.json", {"scope": "Immutable actual-capsule replay evidence; expected rejection reproduced once, no physics PASS claim.", "artifacts": artifacts})
    (destination / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["path"] + "\n" for row in artifacts), encoding="ascii")
    assert all(sha((destination / row["path"]).read_bytes()) == row["sha256"] for row in artifacts)
    print(json.dumps({"status": "PASS", "archives": archives, "indexedArtifacts": len(artifacts), "totalVerifiedMembers": sum(row["verifiedMembers"] for row in archives), "sourceCountPerReplay": 272, "currentTestEquals002": True, "packetBytes": sum(path.stat().st_size for path in destination.rglob("*") if path.is_file())}, indent=2))


if __name__ == "__main__":
    main()
