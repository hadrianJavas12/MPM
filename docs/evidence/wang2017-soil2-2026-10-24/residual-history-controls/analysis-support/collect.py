"""Archive retained residual-policy controls without running Lisp or MPM."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/wang2017-soil2-2026-10-24"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def verify_attempt(number):
    base = OUTPUT / f"residual-history-controls-{number:03}"
    result = read_json(base / "result.json")
    manifest = read_json(base / "source/source-manifest.json")
    before = read_json(base / "source-proof-before.json")
    after = read_json(base / "source-proof-after.json")
    assert before == after
    for row in manifest["files"]:
        assert sha((base / row["path"]).read_bytes()) == row["sha256"], row["path"]
    first = read_json(base / "source-provenance-before.json")
    final = read_json(base / "source-provenance.json")
    assert first["sourceSnapshotExactLoadedBytes"] and final["sourceSnapshotExactLoadedBytes"]
    assert first["nativeBackend"] == final["nativeBackend"]
    dll = final["nativeBackend"]
    assert Path(dll["modulePath"]).resolve() == (base / "source/libs/kirchoff.dll").resolve()
    assert sha(Path(dll["modulePath"]).read_bytes()) == dll["sha256"]
    assert dll["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
    assert dll["nativeMcEntryPresent"]
    exit_code = int(Path(str(base) + ".exit-code.txt").read_text())
    summary = {
        "attempt": number, "actualProcessExitCode": exit_code,
        "passedControlCount": result["controlsCount"], "failedControlCount": len(result["failures"]),
        "newModelPointCalls": result["newModelPointCalls"],
        "newModelNativeConstitutiveCalls": result["newModelNativeConstitutiveCalls"],
        "originalVariantActualCapsuleReplayCalls": result["originalVariantActualCapsuleReplayCalls"],
        "physicalUpdatesExecuted": result["physicalUpdatesExecuted"],
        "frozenFileCount": len(manifest["files"]), "allFrozenFileHashesVerified": True,
        "sourceProofBeforeAfterEqual": True, "mappedCopiedDllVerified": True,
        "nativeBackend": dll,
        "executedTestSha256": sha((base / "source/case.lisp").read_bytes()),
        "capturedFixtureSha256": sha((base / "source/residual-policy-captured-input.json").read_bytes()),
    }
    if not (base / "verification-summary.json").exists():
        write_new(base / "verification-summary.json", summary)
    return base, result, summary


one, result_one, proof_one = verify_attempt(1)
two, result_two, proof_two = verify_attempt(2)
assert proof_one["actualProcessExitCode"] == 1 and proof_two["actualProcessExitCode"] == 0
assert result_one["passed"] is False and result_two["passed"] is True
assert result_one["controlsCount"] == 12 and len(result_one["failures"]) == 1
assert result_two["controlsCount"] == 1 and not result_two["failures"]
assert "0.6108652381980153" in result_one["failures"][0][1]
assert result_two["selection"] == "constructor-only"
assert set(result_two["skippedControlLabels"]) == set(result_one["controlLabels"])
assert result_two["controlLabels"][0] == result_one["failures"][0][0]
assert len(set(result_one["controlLabels"] + result_two["controlLabels"])) == 13
assert result_one["newModelPointCalls"] == 1 and result_one["newModelNativeConstitutiveCalls"] == 9
assert result_two["newModelPointCalls"] == 0 and result_two["newModelNativeConstitutiveCalls"] == 0
assert proof_one["capturedFixtureSha256"] == proof_two["capturedFixtureSha256"] == "3ad314d3416df31122a2a628056b847cbe46e687cb89c90b349964ee892da926"
assert proof_one["nativeBackend"]["sha256"] == proof_two["nativeBackend"]["sha256"]
assert (two / "source/case.lisp").read_bytes() == (ROOT / "tests/materials/wang2017-residual-history.lisp").read_bytes()

payload = []
excluded = []
for number, base in ((1, one), (2, two)):
    prefix = f"attempt-{number:03}"
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(base)
        name = f"{prefix}/{relative.as_posix()}"
        if ".native-cache" in relative.parts or path.suffix.lower() == ".fasl":
            excluded.append({"path": name, "bytes": path.stat().st_size,
                             "reason": "Private native compilation cache/FASL; not retained as portable evidence"})
        else:
            payload.append((name, path))
    for suffix in (".stdout.log", ".exit-code.txt"):
        payload.append((f"{prefix}/execution{suffix}", Path(str(base) + suffix)))

members = [{"path": name, "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
           for name, path in payload]
write_new(PACKET / "archive-member-manifest.json", {"members": members, "excluded": excluded})
archive = PACKET / "residual-history-controls-001-002.zip"
with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
    for name, path in payload:
        target.write(path, name)
with zipfile.ZipFile(archive) as target:
    assert target.testzip() is None
    assert len(target.namelist()) == len(members)
    assert set(target.namelist()) == {row["path"] for row in members}
    for row in members:
        decoded = target.read(row["path"])
        assert len(decoded) == row["bytes"] and sha(decoded) == row["sha256"]
write_new(PACKET / "archive-verification.json", {
    "verifiedAtUtc": datetime.now(timezone.utc).isoformat(), "archive": archive.name,
    "sha256": sha(archive.read_bytes()), "bytes": archive.stat().st_size,
    "decodedMembersVerified": len(members), "crcPass": True, "completeInventoryVerified": True,
    "eachMemberSizeAndSha256Verified": True, "excludedPrivateCacheFiles": len(excluded),
    "testsOrSolverExecutedDuringPackaging": False,
})
write_new(PACKET / "result-summary.json", {
    "scope": "Thirteen distinct control groups passed across two separate processes; not one 13-PASS process",
    "originalFailureRetained": True, "originalFailureCause": "Test expected friction degrees; law-values returns radians",
    "attempts": [proof_one, proof_two], "aggregatePassedDistinctControlGroups": 13,
    "aggregateNewModelPointCalls": 1, "aggregateNewModelNativeConstitutiveCalls": 9,
    "aggregateOriginalVariantActualCapsuleReplayCalls": 0, "aggregatePhysicalUpdatesExecuted": 0,
    "originalFailure": result_one["failures"], "observations": result_one["observations"],
    "processExitObservations": [
        {"attempt": 1, "executorSessionId": 44190, "observedFinalExitCode": 1},
        {"attempt": 2, "executorSessionId": 5812, "observedFinalExitCode": 0},
    ],
})
artifacts = [PACKET / "README.md", Path(__file__), archive, PACKET / "archive-member-manifest.json",
             PACKET / "archive-verification.json", PACKET / "result-summary.json", PACKET / ".gitattributes"]
records = [{"path": path.relative_to(PACKET).as_posix(), "bytes": path.stat().st_size,
            "sha256": sha(path.read_bytes())} for path in artifacts]
write_new(PACKET / "evidence-manifest.json", {"artifacts": records})
with (PACKET / "SHA256SUMS").open("x", encoding="ascii", newline="\n") as stream:
    for row in records:
        stream.write(f"{row['sha256']}  {row['path']}\n")
    manifest = PACKET / "evidence-manifest.json"
    stream.write(f"{sha(manifest.read_bytes())}  evidence-manifest.json\n")
print(json.dumps({"attempts": [proof_one, proof_two], "verifiedArchiveMembers": len(members),
                  "excludedCacheFiles": len(excluded), "archiveSha256": sha(archive.read_bytes())}, indent=2))
