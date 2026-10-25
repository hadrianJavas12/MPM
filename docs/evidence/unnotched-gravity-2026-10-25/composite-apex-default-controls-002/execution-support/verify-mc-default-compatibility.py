"""Verify existing frozen default-control records; no native/test execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STRICT = "e26b736914a8fa2cc3f4eb7f6619c1331e787f72d365d5bb7c0a5b3f4d8ceda1"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--kind", choices=("strict34", "output"), required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    target = run / "post-run-source-runtime-verification.json"
    if target.exists():
        raise RuntimeError("Preserve existing verification")
    failures, checked, provenance_checks = [], [], []
    rows = read(run / "source/source-manifest.json")["files"]
    if len({row["path"] for row in rows}) != len(rows):
        failures.append("Duplicate source-manifest path")
    for row in rows:
        copied = (run / row["path"]).resolve()
        if not copied.is_relative_to((run / "source").resolve()):
            raise RuntimeError("Copied source escapes frozen tree")
        expected = {key: row[key] for key in ("bytes", "sha256")}
        current = digest(copied)
        original = digest(Path(row["originalPath"]))
        matched = current == expected == original
        checked.append({"path": row["path"], **current, "originalStillMatches": matched})
        if not matched:
            failures.append("Frozen/original source changed: " + row["path"])
    projected = next(row for row in rows if row["path"].endswith("mohr-coulomb-evolution/projection.lisp"))
    if projected["sha256"] != STRICT:
        failures.append("Strict original projector hash changed")
    for filename in ("source-provenance-before.json", "source-provenance.json"):
        evidence = read(run / filename)
        backend = evidence["nativeBackend"]
        dll = run / "source/libs/kirchoff.dll"
        mapped = Path(backend["modulePath"]).resolve() == dll.resolve()
        copied_match = set(evidence["copiedFiles"]) == {row["path"] for row in rows}
        optional = [action for action in evidence["verifiedAsdfActions"]
                    if "mc-composite-apex" in action.get("system", "").lower()
                    or "/mc-composite-apex/" in action.get("source", "").replace("\\", "/").lower()
                    or action.get("source", "").replace("\\", "/").lower().endswith("/materials/adapters/mc-composite-apex.lisp")]
        accepted = (evidence["sourceSnapshotExactLoadedBytes"] and evidence["copiedByteEqualityBeforeLoad"]
                    and copied_match and mapped and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
                    and backend["sha256"] == digest(dll)["sha256"] and not optional)
        provenance_checks.append({"file": filename, "loadedFrozenSourcesRecorded": accepted,
            "allCopiedPathsMatchManifest": copied_match, "actualMappedDll": backend,
            "optionalCompositeAsdfActions": len(optional), "record": digest(run / filename)})
        if not accepted:
            failures.append("Recorded before/after loaded-source/DLL/default-only scope mismatch: " + filename)
    explicit_proofs = []
    for phase in ("before", "after"):
        path = run / f"source-proof-{phase}.json"
        if path.is_file():
            seen = {row["path"]: row["sha256"] for row in read(path)["files"]}
            matched = seen == {row["path"]: row["sha256"] for row in rows}
            explicit_proofs.append({"phase": phase, "allHashesMatch": matched, **digest(path)})
            if not matched:
                failures.append("Explicit source proof mismatch: " + phase)
    result = read(run / "result.json")
    if args.kind == "strict34":
        expected = (result["passed"] and result["exitCode"] == 0 and result["passedCount"] == 34
                    and result["failedCount"] == 0 and result["allSourceHashesVerifiedAfter"]
                    and result["originalTestSha256"] == result["copiedTestSha256"]
                    == "1b824b2f2dafb08ef0090ecdb500953b71dca0444ed65cbb9b790cac58385053")
    else:
        expected = (result["passed"] and result["mode"] == "output" and result["passedCount"] == 4
                    and result["physicalUpdatesExecuted"] == 2 and result["pointCalls"] == 0
                    and result["materialCallsAttempted"] == result["materialCallsAccepted"] == 1760)
        if len(explicit_proofs) != 2:
            failures.append("Bounded fixture lacks both explicit source hash proofs")
    if not expected:
        failures.append("Actual existing control result differs from its declared scope")
    report = {"status": "FAIL" if failures else "PASS", "failures": failures,
        "kind": args.kind, "sourceCount": len(rows), "files": checked,
        "currentFrozenAndOriginalSourceHashesAllMatch": all(row["originalStillMatches"] for row in checked),
        "beforeAfterRuntimeProvenance": provenance_checks, "explicitBeforeAfterSourceProofs": explicit_proofs,
        "strictProjectorSha256": projected["sha256"], "optionalCompositeNotLoaded": all(not row["optionalCompositeAsdfActions"] for row in provenance_checks),
        "beforeHashProofScope": "Pre-load immutable manifest and native snapshot-verify-file checks recorded by before/after runtime provenance; explicit per-file before/after JSON also checked when the existing fixture emits it. No independent external pre-run read is invented.",
        "nativeResult": result, "executedVerifier": {"path": str(Path(__file__).resolve()), **digest(Path(__file__))},
        "scope": "Read/hash saved source/runtime/result records only. No solver, material call, replay, test, render or process query."}
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "kind": args.kind, "sources": len(rows), "result": str(target)}))
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
