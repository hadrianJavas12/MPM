"""Bounded read/copy/hash/ZIP closure of three already-completed FIRST gates.

Never invokes Lisp, Node, npm, a test, solver, renderer or network command.
Run once from any directory. Existing summary/manifest is never overwritten.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import zipfile

DEST = Path(__file__).resolve().parent
ROOT = DEST.parents[3]
RAW = ROOT / "output/urmi-mc-damage40-2026-10-27"
COMMITS = {
    "point-001": "961c17a8992b056c30409f4b670c60d802e51b61",
    "transfer-001": "946dbce7d572a8cf9d610a32d6e02cc633c7612c",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def write_json(relative: str, value):
    path = DEST / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def copy_exact(source: Path, relative: str):
    data = source.read_bytes()
    path = DEST / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    assert path.read_bytes() == data
    return {"path": relative, "originalPath": str(source), "bytes": len(data), "sha256": sha(data)}


def git(*args, stdin=None):
    answer = subprocess.run(["git", "-C", str(ROOT), *args], input=stdin, capture_output=True, check=True)
    return answer.stdout


def git_attribution(commit, rows):
    requests = []
    for row in rows:
        original = Path(row["originalPath"]).resolve().relative_to(ROOT).as_posix()
        requests.append(f"{commit}:{original}")
    data = io.BytesIO(git("cat-file", "--batch", stdin=("\n".join(requests) + "\n").encode()))
    records = []
    for request, row in zip(requests, rows):
        header = data.readline().decode().strip()
        if header.endswith(" missing"):
            records.append({"path": row["path"], "request": request, "status": "not-in-attributed-commit"})
            continue
        oid, kind, size = header.split()
        assert kind == "blob"
        blob = data.read(int(size))
        assert data.read(1) == b"\n"
        frozen = (RAW / current_gate / row["path"]).read_bytes()
        status = "exact-raw-bytes" if frozen == blob else (
            "line-endings-only" if frozen.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n") else "different")
        records.append({"path": row["path"], "request": request, "gitBlob": oid,
                        "gitBlobSha256": sha(blob), "status": status})
    assert not data.read()
    return records


def verify_loaded_paths(provenance, source, manifest):
    actions = provenance["verifiedAsdfActions"]
    source_paths = set()
    inputs = {}
    planned_unhashed = []
    for action in actions:
        if action.get("firstParty"):
            path = Path(action["source"]).resolve()
            relative = path.relative_to(source.parent).as_posix()
            assert relative in manifest, relative
            assert sha(path.read_bytes()) == manifest[relative]["sha256"]
            source_paths.add(relative)
        for item in action.get("loadInputs", []):
            if action.get("event") != "performing" or action.get("operation") != "load-op":
                if item.get("sha256") is None:
                    planned_unhashed.append({"event": action.get("event"), "operation": action.get("operation"),
                                             "firstParty": bool(action.get("firstParty")), "path": item.get("path")})
                continue
            assert item.get("path") and item.get("sha256"), "Actual load input must carry its recorded hash"
            key = (item["path"], item["sha256"], bool(action.get("firstParty")))
            inputs[key] = item
    checked = []
    for (name, expected, first_party), item in sorted(inputs.items()):
        path = Path(name)
        actual = sha(path.read_bytes()) if path.is_file() else None
        checked.append({"path": name, "firstParty": first_party, "expectedSha256": expected,
                        "actualSha256": actual, "matches": actual == expected})
    assert all(row["matches"] for row in checked if row["firstParty"])
    probes = []
    for probe in provenance["externalMathModuleProbes"]:
        actual = sha(Path(probe["path"]).read_bytes())
        probes.append({**probe, "actualSha256": actual, "matches": actual == probe["sha256"]})
    assert all(row["matches"] for row in probes)
    return {"actionRecords": len(actions), "firstPartyActionRecords": sum(bool(x.get("firstParty")) for x in actions),
            "distinctFirstPartySources": len(source_paths), "loadInputHashChecks": checked,
            "plannedUnhashedInputsNotTreatedAsActualLoads": planned_unhashed,
            "externalMathModuleChecks": probes, "scopeLimits": provenance["limits"]}


def archive_tree(gate, source):
    rows = []
    archive = DEST / gate / "source-and-private-cache.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            name = path.relative_to(source.parent).as_posix()
            data = path.read_bytes()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, data)
            rows.append({"path": name, "bytes": len(data), "sha256": sha(data),
                         "privateFaslCache": name.startswith("source/.native-cache/")})
    with zipfile.ZipFile(archive) as check:
        assert sorted(check.namelist()) == sorted(row["path"] for row in rows)
        assert check.testzip() is None
        for row in rows:
            data = check.read(row["path"])
            assert len(data) == row["bytes"] and sha(data) == row["sha256"]
            assert data == (source.parent / row["path"]).read_bytes()
    write_json(f"{gate}/archive-members.json", {"members": rows, "count": len(rows)})
    return {"path": archive.relative_to(DEST).as_posix(), "sha256": sha(archive.read_bytes()),
            "members": len(rows), "privateCacheFiles": sum(x["privateFaslCache"] for x in rows),
            "rawBytes": sum(x["bytes"] for x in rows)}


def main():
    global current_gate
    started = datetime.now(timezone.utc).isoformat()
    assert ROOT.name.lower() == "mpm" and RAW.is_dir(), (ROOT, RAW)
    assert not (DEST / "summary.json").exists() and not (DEST / "evidence-manifest.json").exists()
    assert {p.name for p in DEST.iterdir()} == {"collect.py", ".gitattributes", "collector-attempt-001.json"}, "Fresh closure directory required"
    copied = []
    summaries = []
    for current_gate, commit in COMMITS.items():
        gate = current_gate
        original = RAW / gate
        source = original / "source"
        exit_record = read_json(RAW / f"{gate}.exit.json")
        result = read_json(original / "result.json")
        assert exit_record["exitCode"] == 0 and exit_record["sourceCommit"] == commit
        assert result["passed"] is True and not result["failures"]
        commit_data = git("show", "--no-patch", "--format=%H%n%T%n%cI%n%s", commit).decode().splitlines()
        assert commit_data[0] == commit
        rows = read_json(source / "source-manifest.json")["files"]
        manifest = {row["path"]: row for row in rows}
        assert len(manifest) == len(rows)
        for name, row in manifest.items():
            path = (original / name).resolve()
            path.relative_to(source.resolve())
            data = path.read_bytes()
            assert len(data) == row["bytes"] and sha(data) == row["sha256"], name
        for name in ("source-proof-before.json", "source-proof-after.json"):
            proof = read_json(original / name)["files"]
            assert len(proof) == len(rows)
            assert {x["path"]: x["sha256"] for x in proof} == {k: v["sha256"] for k, v in manifest.items()}
        checks = []
        for name in ("source-provenance-before.json", "source-provenance.json"):
            provenance = read_json(original / name)
            assert provenance["sourceSnapshotExactLoadedBytes"] is True
            assert provenance["copiedByteEqualityBeforeLoad"] is True
            assert set(provenance["copiedFiles"]) == set(manifest)
            native = provenance["nativeBackend"]
            assert Path(native["modulePath"]).resolve() == (source / "libs/kirchoff.dll").resolve()
            assert native["nativeMcEntryPresent"] is True
            assert native["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            assert sha(Path(native["modulePath"]).read_bytes()) == native["sha256"]
            checks.append({"record": name, **verify_loaded_paths(provenance, source, manifest)})
        assert result["nativeBackend"] == provenance["nativeBackend"]
        for path in sorted(original.iterdir()):
            if path.is_file():
                copied.append(copy_exact(path, f"{gate}/{path.name}"))
        copied.append(copy_exact(source / "source-manifest.json", f"{gate}/source-manifest.json"))
        for suffix in ("command.txt", "exit.json", "stdout.log", "stderr.log"):
            copied.append(copy_exact(RAW / f"{gate}.{suffix}", f"{gate}/native.{suffix}"))
        archive = archive_tree(gate, source)
        attribution = git_attribution(commit, rows)
        write_json(f"{gate}/verification.json", {"passed": True, "sourceCommit": commit, "gitCommit": commit_data,
            "frozenPayloadsVerified": len(rows), "beforeAfterHashesIdentical": True,
            "runtimeChecks": checks, "gitAttributionChecks": attribution,
            "gitAttributionCounts": {key: sum(x["status"] == key for x in attribution) for key in
                                      ("exact-raw-bytes", "line-endings-only", "different", "not-in-attributed-commit")},
            "sourceArchive": archive})
        if gate == "point-001":
            assert len(result["passedGroups"]) == 5
            for key, value in {"purePrincipalCallsAttempted": 84, "nativeConstitutiveCallsAttempted": 3,
                               "nativeConstitutiveCallsAccepted": 2, "physicalUpdateAttempts": 0,
                               "ownedReplayAttempts": 3, "syntheticValidOwnedReplayProjectorCalls": 1}.items():
                assert result[key] == value, key
        else:
            assert len(result["passedGroups"]) == 4
            assert result["nativeMaterialAttempts"] == result["nativeMaterialAccepted"] == 6
            assert result["mpmUpdatesAttempted"] == result["physicalTimeAdvancedS"] == 0
        summaries.append({"gate": gate, "sourceCommit": commit, "exit": exit_record,
            "result": {k: v for k, v in result.items() if k not in ("cases", "observations")},
            "sourcePayloads": len(rows), "archive": archive,
            "openblasThreads": provenance["openblasThreads"], "ompThreads": provenance["ompThreads"],
            "compilerPolicy": provenance["compilerPolicy"], "storedGitVersionFile": provenance["storedGitVersionFile"],
            "gitAttributionCounts": {key: sum(x["status"] == key for x in attribution) for key in
                                      ("exact-raw-bytes", "line-endings-only", "different", "not-in-attributed-commit")}})
    node = RAW / "node-baseline-001"
    node_exit = read_json(node / "exit.json")
    assert node_exit["checkExit"] == node_exit["testExit"] == 0
    assert node_exit["sourceCommit"] == COMMITS["point-001"]
    test_log = (node / "test.log").read_text(encoding="utf-8-sig")
    assert "tests 36" in test_log and "pass 36" in test_log and "fail 0" in test_log
    assert test_log.count("✔ SBCL") == 3
    for path in sorted(node.iterdir()):
        assert path.is_file()
        copied.append(copy_exact(path, f"node-baseline-001/{path.name}"))
    node_summary = {"exit": node_exit, "tests": 36, "passed": 36, "failed": 0,
        "actualSbclContractGroupsInNodeLog": 3,
        "commandEvidence": "npm check/test script commands are printed in saved stdout; no separate original invocation record",
        "provenanceLimits": "No saved Node version or pre-run Node source/runtime snapshot. Source commit attribution is the original exit.json; no stronger source-freeze claim."}
    write_json("copy-verification.json", {"passed": True, "exactByteCopies": copied, "count": len(copied)})
    write_json("summary.json", {"scope": "Closure only of actual FIRST point-001, transfer-001 and Node baseline; no solver/tests rerun",
        "gates": summaries, "nodeBaseline": node_summary,
        "limits": ["Point and transfer gates execute zero MPM updates; no equilibrium/full slope/scientific validation.",
                   "Private first-party FASLs are archived; third-party dependencies remain external and have recorded current hash checks.",
                   "Stored native Git version text is invalid; loaded source identity is the frozen SHA256 manifest and launch commit attribution.",
                   "SYNTHETIC replay is not an actual failure replay; large-J returns do not prove global uniqueness."],
        "originalOutputUntouched": True})
    write_json("collection-execution.json", {"startedUtc": started, "finishedUtc": datetime.now(timezone.utc).isoformat(),
        "argv": sys.argv, "pythonExecutable": sys.executable, "collectorSha256": sha(Path(__file__).read_bytes()),
        "operations": "Read completed artifacts; verify hashes/Git objects; copy exact bytes; deterministic source/cache ZIP; no tests/native/network execution"})
    paths = sorted(p for p in DEST.rglob("*") if p.is_file())
    attr_paths = [p.relative_to(ROOT).as_posix() for p in paths] + [
        (DEST / name).relative_to(ROOT).as_posix() for name in ("evidence-manifest.json", "git-attribute-verification.json")]
    attrs = git("check-attr", "--stdin", "text", stdin=("\n".join(attr_paths) + "\n").encode()).decode().splitlines()
    assert len(attrs) == len(attr_paths) and all(x.endswith(": text: unset") for x in attrs)
    write_json("git-attribute-verification.json", {"allTextAttributesUnset": True, "records": attrs,
        "scope": "Scoped .gitattributes preserves original log/JSON/source/archive bytes when Git stores this evidence."})
    rows = []
    for path in sorted(p for p in DEST.rglob("*") if p.is_file()):
        data = path.read_bytes()
        rows.append({"path": path.relative_to(DEST).as_posix(), "bytes": len(data), "sha256": sha(data)})
    write_json("evidence-manifest.json", {"schema": "mpm.exact-byte-evidence-index.v1", "files": rows,
        "indexedFiles": len(rows), "excludedSelf": "evidence-manifest.json"})
    print(json.dumps({"passed": True, "indexedFiles": len(rows), "totalFilesIncludingManifest": len(rows) + 1,
        "archives": [x["archive"] for x in summaries], "nativeSourcesVerified": [x["sourcePayloads"] for x in summaries],
        "nodePass": 36, "manifestSha256": sha((DEST / "evidence-manifest.json").read_bytes())}, indent=2))


if __name__ == "__main__":
    main()
