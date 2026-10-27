"""Archive existing closed BC/static diagnostics only; no simulation or numerical search."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "output/urmi-mc-damage40-2026-10-27"
WORK = Path(__file__).resolve().parent
DEST = ROOT / "docs/evidence/urmi-mc-damage40-2026-10-27/bc-mask-and-static-diagnostics"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def put(path, value):
    Path(path).write_text(json.dumps(value, indent=2), encoding="utf-8")


def record(path):
    data = Path(path).read_bytes()
    return {"path": str(Path(path).resolve()), "bytes": len(data), "sha256": digest(data)}


def copy(source, target, copies):
    source, target = Path(source), Path(target)
    assert not target.exists(), target
    target.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    target.write_bytes(data)
    assert source.read_bytes() == data == target.read_bytes(), source
    copies.append({"source": record(source), "copy": {"path": target.relative_to(DEST).as_posix(),
                   "bytes": len(data), "sha256": digest(data)}})


def archive(target, paths, base):
    assert not target.exists(), target
    assert len(paths) == len(set(paths)), "Duplicate archive inputs"
    members = []
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(paths):
            data = path.read_bytes()
            name = path.relative_to(base).as_posix()
            output.writestr(name, data)
            assert path.read_bytes() == data, path
            members.append({"path": name, "bytes": len(data), "sha256": digest(data)})
    with zipfile.ZipFile(target) as check:
        assert check.testzip() is None and len(check.namelist()) == len(members)
        for row in members:
            data = check.read(row["path"])
            assert len(data) == row["bytes"] and digest(data) == row["sha256"], row
    return {"archive": target.relative_to(DEST).as_posix(), "verifiedMemberCount": len(members), "verifiedMembers": members}


def verify_native(name):
    run = RAW / name
    manifest = load(run / "source/source-manifest.json")["files"]
    known, current_differences = {}, []
    for row in manifest:
        path = (run / row["path"]).resolve()
        assert path.is_relative_to((run / "source").resolve()), path
        data = path.read_bytes()
        assert len(data) == row["bytes"] and digest(data) == row["sha256"], path
        assert row["path"] not in known
        known[row["path"]] = row["sha256"]
        original = Path(row["originalPath"])
        if not original.is_file() or digest(original.read_bytes()) != row["sha256"]:
            current_differences.append(str(original))
    before = load(run / "source-proof-before.json")
    assert {row["path"]: row["sha256"] for row in before["files"]} == known
    after_path = run / "source-proof-after.json"
    if after_path.exists():
        assert {row["path"]: row["sha256"] for row in load(after_path)["files"]} == known
    provenance = load(run / ("source-provenance.json" if after_path.exists() else "source-provenance-before.json"))
    assert provenance["sourceSnapshotExactLoadedBytes"] is True
    assert provenance["copiedByteEqualityBeforeLoad"] is True
    dll = provenance["nativeBackend"]
    assert Path(dll["modulePath"]).resolve() == (run / "source/libs/kirchoff.dll").resolve()
    assert dll["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
    assert digest(Path(dll["modulePath"]).read_bytes()) == dll["sha256"]
    loaded = {}
    for action in provenance["verifiedAsdfActions"]:
        if action.get("firstParty") and action.get("event") == "performing" and action.get("operation") == "load-op":
            for item in action.get("loadInputs", []):
                path = Path(item["path"]).resolve()
                assert path.is_relative_to((run / "source").resolve())
                assert digest(path.read_bytes()) == item["sha256"], path
                if str(path) in loaded:
                    assert loaded[str(path)] == item["sha256"]
                loaded[str(path)] = item["sha256"]
    exit_record = load(Path(str(run) + ".exit.json"))
    summary = {"sourceRecordsVerified": len(known), "uniqueLoadedFaslInputsVerified": len(loaded), "mappedDll": dll,
               "currentOriginalDifferences": current_differences, "nativeExit": exit_record,
               "sourceAfterProofPresent": after_path.exists()}
    if name == "bc-mask-001":
        assert exit_record["exitCode"] == 1 and not after_path.exists() and not (run / "result.json").exists()
        error = Path(str(run) + ".stderr.log").read_text(encoding="utf-8-sig")
        assert 'The symbol "NODE-POSITION" is not external' in error
        summary.update(status="RETAINED_READER_FAILURE_BEFORE_DIAGNOSTIC_INVOCATION", acceptedDiagnosticGroups=0,
                       counters="NOT_PRODUCED: diagnostic body not executed; no after-proof invented")
    else:
        result = load(run / "result.json")
        assert exit_record["exitCode"] == 0 and result["passed"] is True and len(result["passedGroups"]) == 4
        assert result["mpmCalls"] == result["materialCalls"] == 0 and result["initialP2gCalls"] == 1
        assert result["nativeBackend"] == dll
        passes = result["observations"]["boundedActualSchedulerPasses"]
        assert len(passes) == 32
        assert sum(row["workers"] == 1 for row in passes) == sum(row["workers"] == 4 for row in passes) == 16
        assert all(not row["physicalConstraintViolations"] for row in passes)
        summary.update(status="PASS_FIRST_EXECUTED_NODAL_DIAGNOSTIC", acceptedDiagnosticGroups=4,
                       mpmCalls=0, materialCalls=0, initialP2gCalls=1,
                       oldFullRelevantSourceHashIdentity=result["observations"]["originalFullRelevantSourceHashIdentity"],
                       limits="Initial P2G/controlled nodal fixtures only; does not establish cause of serial full00120s cap")
    return summary


def verify_static():
    run = RAW / "drained-static-001"
    before, after = load(run / "source-before.json"), load(run / "source-after.json")
    assert before == after and len(before) == 3
    for row in before:
        for key in ("source", "copy"):
            actual = record(Path(row[key]["path"]))
            assert actual == row[key], (key, actual, row[key])
    summary = load(run / "summary.json")
    assert summary["sourceBinding"] == before
    assert load(Path(str(run) + ".exit.json"))["exitCode"] == 0
    assert len(summary["summaries"]) == 2
    assert [row["slices"] for row in summary["summaries"]] == [200, 400]
    assert [row["attempted"] for row in summary["summaries"]] == [1989, 1989]
    return {"status": "EXISTING_STATIC_SEARCH_BYTES_VERIFIED_NO_REEXECUTION", "frozenBeforeAfterCurrentSourcesVerified": 3,
            "attemptedCandidatesAlreadyRecorded": 3978, "summaries": summary["summaries"],
            "limits": "Restricted dry Bishop circle family with retained negative normals; neither physical/global FoS nor proof of MPM stability/instability"}


def collect():
    assert not DEST.exists(), "Preserve earlier packet; use an explicit repair if needed"
    native = {name: verify_native(name) for name in ("bc-mask-001", "bc-mask-002")}
    static = verify_static()
    DEST.mkdir(parents=True)
    (DEST / ".gitattributes").write_text("** -text\n", encoding="utf-8")
    copies, archives = [], []
    copy(Path(__file__), DEST / "collector.py", copies)
    copy(WORK / "invocation-before.json", DEST / "collection-invocation-before.json", copies)
    for name in native:
        run = RAW / name
        archives.append(archive(DEST / (name + "-source-and-cache.zip"),
                                [path for path in (run / "source").rglob("*") if path.is_file()], run))
        for path in sorted(run.iterdir()):
            if path.is_file():
                copy(path, DEST / name / path.name, copies)
        for path in sorted(RAW.glob(name + ".*")):
            if path.is_file():
                copy(path, DEST / name / ("invocation" + path.name.removeprefix(name)), copies)
    static_run = RAW / "drained-static-001"
    static_paths = [path for path in static_run.rglob("*") if path.is_file()]
    static_paths += [path for path in RAW.glob("drained-static-001.*") if path.is_file()]
    archives.append(archive(DEST / "drained-static-001-output-and-source.zip", static_paths, RAW))
    copy(ROOT / "research/notes/urmi-mc-damage40-2026-10-26/bc-mask-diagnostic-result.md",
         DEST / "bc-mask-diagnostic-result.md", copies)
    put(DEST / "archive-members.json", archives)
    put(DEST / "copy-verification.json", copies)
    closure = {"createdUtc": datetime.now(timezone.utc).isoformat(),
               "scope": "Close archival of existing BC001reader failure/002nodal diagnostic and restricted static3978candidate search; no native/test/analysis/research repeated",
               "nativeAttempts": native, "static": static,
               "archiveCount": len(archives), "verifiedDecodedArchiveMembers": sum(row["verifiedMemberCount"] for row in archives),
               "productionChanges": "NONE by this collector; uncommitted test/plan/result preserved for root checkpoint",
               "limits": ["BC fixtures do not prove cause of serial full001 preparation cap", "Static formal roots with negative normal forces are not a physical/global FoS", "No failed001after-proof or runtime counters invented"]}
    put(DEST / "closure.json", closure)
    (DEST / "README.md").write_text(
        "# Existing BC and restricted static diagnostics\n\n"
        "This packet preserves both BC diagnostic attempts and the completed dry Bishop search. No simulation, material update, search or review was rerun for archival.\n\n"
        "BC001 failed during package reading before the diagnostic invocation; its original source/runtime/logs remain. BC002 passed four groups with zero MPM/material calls and one initial P2G. The initial/crafted nodal evidence demonstrates cached-mask classification defects while physical constraints hold. It does not establish the cause of serial full001's preparation cap.\n\n"
        "The static study contains3978already evaluated candidates at200/400slices. Restricted-family formal minima include negative base normals; they are not physical/global factors of safety. Raw candidates, original three frozen sources/contracts and invocation evidence remain in its ZIP.\n\n"
        "Each native attempt has exactly one complete source/private-cache ZIP, with mapped DLL and decoded member hashes. See closure.json, archive-members.json and evidence-manifest.json. Current original-source differences are listed honestly; immutable captured payloads, not later working files, identify executed bytes.\n", encoding="utf-8")
    print(json.dumps({"collection": "complete-awaiting-log-finalization", "nativeSourceRecords": [row["sourceRecordsVerified"] for row in native.values()],
                      "archives": len(archives), "members": closure["verifiedDecodedArchiveMembers"]}))


def finalize():
    assert DEST.exists() and not (DEST / "evidence-manifest.json").exists()
    copies = load(DEST / "copy-verification.json")
    for source_name, name in (("stdout.log", "collection-stdout.log"), ("stderr.log", "collection-stderr.log"), ("exit.json", "collection-exit.json")):
        copy(WORK / source_name, DEST / name, copies)
    assert load(WORK / "exit.json")["exitCode"] == 0
    put(DEST / "copy-verification.json", copies)
    files = sorted(path for path in DEST.rglob("*") if path.is_file())
    closure = load(DEST / "closure.json")
    closure["artifactCountIncludingManifest"] = len(files) + 1
    closure["artifactHashesOmitManifestSelfHash"] = True
    put(DEST / "closure.json", closure)
    records = []
    for path in files:
        data = path.read_bytes()
        records.append({"path": path.relative_to(DEST).as_posix(), "bytes": len(data), "sha256": digest(data)})
    put(DEST / "evidence-manifest.json", {"scope": closure["scope"], "files": records, "selfHashOmitted": True})
    assert len(records) + 1 == len([path for path in DEST.rglob("*") if path.is_file()])
    for row in records:
        data = (DEST / row["path"]).read_bytes()
        assert len(data) == row["bytes"] and digest(data) == row["sha256"]
    print(json.dumps({"packet": str(DEST), "indexedArtifactsExcludingManifest": len(records), "filesIncludingManifest": len(records)+1,
                      "archives": closure["archiveCount"], "decodedMembersVerified": closure["verifiedDecodedArchiveMembers"],
                      "nativeSourceRecords": [row["sourceRecordsVerified"] for row in closure["nativeAttempts"].values()],
                      "staticSources": closure["static"]["frozenBeforeAfterCurrentSourcesVerified"], "staged": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    finalize() if args.finalize else collect()
