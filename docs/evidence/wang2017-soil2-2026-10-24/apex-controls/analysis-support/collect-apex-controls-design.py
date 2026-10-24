"""Package completed new-model unit controls and historical design separately."""
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
    args = parser.parse_args()
    repo = Path(args.repository).resolve()
    raw = repo / "output/wang2017-soil2-2026-10-24"
    evidence = repo / "docs/evidence/wang2017-soil2-2026-10-24"
    unit = raw / "apex-controls-001"
    result = load(unit / "result.json")
    assert result["passed"] is True and not result["failures"]
    assert result["controlsCount"] == len(result["controlLabels"]) == 11
    assert result["newModelPointCalls"] == 12 and result["newModelNativeConstitutiveCalls"] == 5
    assert result["strictActualCapsuleReplayCalls"] == result["physicalUpdatesExecuted"] == 0
    source_manifest = load(unit / "source/source-manifest.json")
    before = load(unit / "source-proof-before.json")["files"]
    after = load(unit / "source-proof-after.json")["files"]
    assert before == after
    frozen_hashes = {row["path"]: row["sha256"].lower() for row in before}
    assert len(frozen_hashes) == len(source_manifest["files"])
    for row in source_manifest["files"]:
        data = (unit / row["path"]).read_bytes()
        assert len(data) == row["bytes"] and sha(data) == row["sha256"].lower() == frozen_hashes[row["path"]]
    assert (unit / "source/case.lisp").read_bytes() == (repo / "tests/materials/wang2017-apex.lisp").read_bytes()
    fixture_sha = sha((unit / "source/actual-strict-failure-input.json").read_bytes())
    assert fixture_sha == "05835d5429292da0b95190232c0d3fb4d6228d6fd08d975ee1346434ba99242d"
    runtime_before, runtime_after = load(unit / "source-provenance-before.json"), load(unit / "source-provenance.json")
    assert runtime_before["nativeBackend"] == runtime_after["nativeBackend"]
    backend = runtime_after["nativeBackend"]
    assert backend["sha256"].lower() == frozen_hashes["source/libs/kirchoff.dll"]
    assert backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
    summaries = []
    for source_name, target_name in [("apex-controls-001", "apex-controls"), ("apex-flow-design-001", "apex-flow-design")]:
        source = raw / source_name
        target = evidence / target_name
        assert not target.exists(), "Evidence target must be fresh: " + str(target)
        target.mkdir(parents=True)
        (target / "analysis-support").mkdir()
        shutil.copy2(__file__, target / "analysis-support/collect-apex-controls-design.py")
        mapped, excluded = [], []
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if ".native-cache" in relative.parts or path.suffix.lower() == ".fasl":
                excluded.append({"path": relative.as_posix(), "bytes": path.stat().st_size})
            else:
                mapped.append((path, source_name + "/" + relative.as_posix()))
        if target_name == "apex-controls":
            mapped.append((repo / "output/wang2017-soil2-2026-10-24-apex-controls-001.log", source_name + "/native.log"))
        archive_path = target / (source_name + ".zip")
        records, inputs = [], {}
        with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, member in mapped:
                data = path.read_bytes()
                inputs[str(path)] = sha(data)
                archive.writestr(member, data)
                records.append({"path": member, "bytes": len(data), "sha256": sha(data)})
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.testzip() is None
            assert sorted(archive.namelist()) == sorted(row["path"] for row in records)
            for row in records:
                data = archive.read(row["path"])
                assert len(data) == row["bytes"] and sha(data) == row["sha256"]
        assert all(sha(Path(path).read_bytes()) == expected for path, expected in inputs.items())
        save(target / "archive-member-manifest.json", {"archive": archive_path.name, "members": records, "excludedPrivateNativeCacheOrFasl": excluded})
        common = {"status": "PASS_ARTIFACT_INTEGRITY", "packagedUtc": datetime.now(timezone.utc).isoformat(),
                  "archive": archive_path.name, "archiveBytes": archive_path.stat().st_size, "archiveSha256": sha(archive_path.read_bytes()),
                  "verifiedMembers": len(records), "originalInputBytesUnchanged": True, "testsOrReplaysExecutedDuringPackaging": 0,
                  "excludedFiles": len(excluded), "excludedBytes": sum(row["bytes"] for row in excluded)}
        if target_name == "apex-controls":
            recovery = {"exitCode": 0, "source": "Original unified exec session10580 final result, recovered without rerun; final chunk4989f2 reports exit_code0.",
                        "command": "windows/cl-mpm.cmd tests/materials/wang2017-apex.lisp output/wang2017-soil2-2026-10-24/apex-controls-001",
                        "resultSha256": sha((unit / "result.json").read_bytes()), "controlsCount": result["controlsCount"],
                        "newModelPointCalls": result["newModelPointCalls"], "newModelNativeConstitutiveCalls": result["newModelNativeConstitutiveCalls"],
                        "strictActualCapsuleReplayCalls": 0, "physicalUpdates": 0}
            save(target / "execution-exit-recovery.json", recovery)
            common.update({"nativeControlExitCode": 0, "controlsCount": result["controlsCount"], "newModelPointCalls": result["newModelPointCalls"],
                           "newModelNativeConstitutiveCalls": result["newModelNativeConstitutiveCalls"], "strictActualCapsuleReplayCalls": 0,
                           "physicalUpdates": 0, "frozenFilesIncludingFixture": len(frozen_hashes), "allFrozenBeforeAfterRetainedHashesMatch": True,
                           "currentTestEqualsExecutedCopy": True, "actualInputFixtureSha256": fixture_sha, "mappedNativeBackend": backend})
            readme = """# Opt-in composite-apex native unit controls

The Windows native command completed with exit0. Its original executor session
10580 was resumed after completion to recover the actual exit code (chunk4989f2);
it was not inferred from PASS lines and the command was not rerun.

Actual result: **11 groups PASS**,12 new-model point calls and5 new-model native
constitutive calls; zero strict actual-capsule replay calls and zero MPM updates.
`execution-exit-recovery.json` records that retained executor observation.

The tests check the formerly rejected actual input under the NEW declared flow,
full elastic compliance, MC/current signed history/cohesion/Cauchy-J consistency,
positive apex volume/work, independent J2, rotation/permutations and owned state.
Regular plastic compression remains analytic and excludes negative apex flow.
The synthetic E0.5MPa coexistence case verifies distinct regular/apex candidates
and requires ambiguity rejection with both branches enumerated. Native ambiguity
failure retains state and declares `materialVariant=composite-apex`. Ordinary
transaction/copy/reinitialize/reset behavior is also checked.

This is a **different constitutive model**, enabled through a separate optional
system/class. Positive hydrostatic plastic flow at the apex changes the strict
zero-dilation baseline. Acceptance of its old failed input does not repair or
invalidate the retained strict rejection. This packet does not demonstrate a
slope collapse, paper-exact physics, scientific validation or all-root uniqueness.

The archive preserves the exact executed test, actual input fixture, all selected
copied sources/DLL/manifest, before/after byte proofs/runtime provenance, result
and raw log. All retained frozen bytes match the pre-load manifest and before/
after proof. The current repository test equals the executed copy. The actual
mapped copied DLL matches the Windows API proof. Third-party dependencies and
arbitrary non-ASDF loads are outside that first-party claim.

Private `.native-cache`/FASL files are excluded and listed by path/size in the
member manifest; original raw folders remain. Every archived member is decoded
and verified for size/SHA256, CRC and complete inventory. No test, replay or solver
was executed during packaging. See `archive-verification.json`,
`archive-member-manifest.json`, `evidence-manifest.json` and `SHA256SUMS`.
Exact collector source is under `analysis-support/`.
"""
        else:
            readme = """# Composite-apex design checkpoint: historical source-only stage

This separate packet preserves `apex-flow-design-001` exactly: the declared
constitutive extension, actual-input algebra diagnostic, synthetic coexistence
fixture and sufficient exclusion bound, historical source-only checkpoint,
original README and SHA index. The archived NOT_RUN/source-only statements refer
to the time of that design checkpoint. Later native unit controls are stored
separately in `../apex-controls/`; this design archive is not rewritten to imply
they had already run.

The model adds positive hydrostatic volumetric flow at the MC apex. It is an
explicit opt-in material change, not a hidden stress clamp or proof that Wang2017
specified that flow. The sufficient no-distinct-apex-versus-regular coexistence
bound near the paper elastic parameters does **not** establish all-root
uniqueness. The soft-elastic synthetic fixture retains the important ambiguity
counterexample. Neither this design nor unit acceptance proves a landslide or
paper/FEM agreement; the strict failed run and its one rejection replay remain
independent negative evidence.

Every member is preserved byte-exact and decoded/verified for size/SHA256, CRC
and complete inventory. No source, numerical test, replay or solver was executed
or changed during packaging. Raw design artifacts remain intact. See
`archive-member-manifest.json`, `archive-verification.json`,
`evidence-manifest.json` and `SHA256SUMS`; exact collector source is retained.
"""
        save(target / "archive-verification.json", common)
        (target / "README.md").write_text(readme, encoding="utf-8")
        (target / ".gitattributes").write_text("* -text -whitespace\n", encoding="ascii")
        artifacts = []
        for path in sorted(target.rglob("*")):
            if path.is_file() and path.name not in {"evidence-manifest.json", "SHA256SUMS"}:
                data = path.read_bytes()
                artifacts.append({"path": path.relative_to(target).as_posix(), "bytes": len(data), "sha256": sha(data)})
        save(target / "evidence-manifest.json", {"scope": "Opt-in composite-apex " + target_name + "; no slope/scientific PASS claim.", "artifacts": artifacts})
        (target / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["path"] + "\n" for row in artifacts), encoding="ascii")
        assert all(sha((target / row["path"]).read_bytes()) == row["sha256"] for row in artifacts)
        summaries.append({"packet": target_name, "archiveSha256": common["archiveSha256"], "verifiedMembers": len(records),
                          "indexedArtifacts": len(artifacts), "archiveBytes": common["archiveBytes"], "frozenFilesIncludingFixture": len(frozen_hashes) if target_name == "apex-controls" else None})
    print(json.dumps({"status": "PASS", "packets": summaries, "testsRepeated": 0}, indent=2))


if __name__ == "__main__":
    main()
