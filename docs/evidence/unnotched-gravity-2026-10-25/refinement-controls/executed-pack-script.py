"""Read/copy/hash/ZIP completed new-grid native controls; never rerun them."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
RUN = RAW / "refnative-controls-001"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/refinement-controls"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"
spec = importlib.util.spec_from_file_location("refinement_copy_helpers", HELPER)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
common.PACKET = PACKET
read_json, record, copy, write_json = common.read_json, common.record, common.copy, common.write_json


def main():
    result = read_json(RUN / "result.json")
    exit_record = read_json(RAW / "refnative-controls-001-exit.json")
    if (not result["passed"] or exit_record["exitCode"] != 0
            or set(result["passedGroups"]) != {"case-delta", "grid-contract", "runner", "csv-vtk"}
            or result["physicalUpdatesExecuted"] != 2
            or result["materialCallsAttempted"] != 7040 or result["materialCallsAccepted"] != 7040):
        raise RuntimeError("Wait for actual terminal four-group success; preserve any failure separately")
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Packet must be fresh inside workspace")
    manifest = read_json(RUN / "source/source-manifest.json")
    sources = {r["path"]: r for r in manifest["files"]}
    if len(sources) != 285 or len(manifest["files"]) != 285:
        raise RuntimeError("Expected285 distinct actual frozen native/input sources")
    for path, expected in sources.items():
        source = RUN / path
        if not source.resolve().is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Source escapes frozen tree")
        actual = record(source)
        if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
            raise RuntimeError("Frozen source mismatch")
    wanted = {p: r["sha256"] for p, r in sources.items()}
    for phase in ("before", "after"):
        proof = read_json(RUN / f"source-proof-{phase}.json")
        if {r["path"]: r["sha256"] for r in proof["files"]} != wanted:
            raise RuntimeError("Recorded before/after proof does not match frozen sources")
    provenance = read_json(RUN / "source-provenance.json")
    if (not provenance["sourceSnapshotExactLoadedBytes"] or not provenance["copiedByteEqualityBeforeLoad"]
            or provenance["nativeBackend"]["sha256"] != sources["source/libs/kirchoff.dll"]["sha256"]):
        raise RuntimeError("Loaded source/native DLL provenance mismatch")
    required = ["source/inputs/cases/benchmarks/gravity-slope-mc-srf-1p4.lisp",
                "source/inputs/cases/benchmarks/gravity-slope-mc-srf-1p4-h05.lisp",
                "source/inputs/research/references/unnotched-mc-ssr/refinement-contract.json"]
    if any(p not in sources for p in required):
        raise RuntimeError("Both executable cases and refinement contract must be frozen")
    coarse_bytes = (RUN / required[0]).read_bytes()
    refined_bytes = (RUN / required[1]).read_bytes()
    if (coarse_bytes.count(b":mesh-size 1d0") != 1
            or coarse_bytes.replace(b":mesh-size 1d0", b":mesh-size .5d0") != refined_bytes):
        raise RuntimeError("Frozen cases differ beyond the one assigned mesh literal")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    copy(HELPER, PACKET / "executed-pack-copy-helpers.py")
    members = {p: RUN / p for p in sources}
    members["source/source-manifest.json"] = RUN / "source/source-manifest.json"
    direct = {}
    for source in sorted(RUN.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(RUN)
        if "source" in relative.parts or "__pycache__" in relative.parts or source.suffix == ".pyc":
            continue
        members[relative.as_posix()] = source
        direct[relative.as_posix()] = source
    for source in [RAW / "refnative-controls-001.log", RAW / "refnative-controls-001-exit.json"]:
        members["adjacent/" + source.name] = source
        direct["adjacent/" + source.name] = source
    archive = common.archive("executed-source-raw-and-runtime", members)
    for relative, source in direct.items():
        copy(source, PACKET / relative)
    copy(RUN / "source/source-manifest.json", PACKET / "source/source-manifest.json")
    for relative in required:
        copy(RUN / relative, PACKET / relative)
    write_json(PACKET / "archive-member-verification.json", archive)
    write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.gravity-refinement.controls.evidence.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
        "nativeExit": exit_record["exitCode"], "passedGroups": result["passedGroups"],
        "actualFrozenSourceFiles": len(sources), "allSourceBeforeAfterAndCurrentBytesMatch": True,
        "physicalUpdatesExecuted": 2, "materialCallsAttempted": 7040, "materialCallsAccepted": 7040,
        "refinedParticles": 3520, "savedParticleStates": 3, "materialCsvRows": 10560,
        "productionCaseOnlyAssignedChange": "meshSize1m->0.5m; exact full compiled/spec comparison in native controls",
        "frozenCaseBytesDifferOnlyMeshLiteral": True,
        "tinyFixtureOverrides": {"durationS": 2e-5, "gravityRampDurationS": 1e-5, "frames": 3, "maxUpdates": 2},
        "nativeBackend": provenance["nativeBackend"], "fullRefinedRunExecuted": False,
        "landslideVerified": False, "scientificallyValidated": False,
        "operations": "Read/copy/hash/ZIP/CRC/decoded-byte comparison only; no controls, native solver, material, replay or analysis repeated"})
    (PACKET / "README.md").write_text(
        "# Native h0.5 refinement controls\n\nFour new grid-specific groups complete Windows native exit0. "
        "Both actual executable cases, refinement contract and285project/native inputs were copied before loading; all before/after/current frozen hashes and mapped DLL proof match. "
        "Full production configuration/spec differences are mesh size1m to0.5m only; material, geometry, BCs, loading/ramp/duration, dt scale, damping, PPC, frames and cap remain unchanged.\n\n"
        "The new grid has3520MPs versus880 with equal mass/polygon. The isolated tiny fixture explicitly overrides duration/ramp/frames/cap, executes exactly two genuine USF updates and7040attempted=accepted constitutive calls, "
        "and retains three actual particle VTKs/10560material CSV rows with positive F/J, stable IDs, mass and independent VTK readback. No old input suite or Node controls were rerun. "
        "This is a bounded grid integration gate, not the full6s refined simulation or a landslide/scientific validation claim.\n\n"
        "Original source/raw/native outputs remain in output/. This packet uses byte-preserving attributes; its ZIP was CRC-tested, decoded and compared byte for byte against every original member. "
        "Packaging repeated no numerical work. Indexed ignored VTK files must be explicitly staged and Git blob hashes verified before commit.\n", encoding="utf-8", newline="\n")
    files = [record(p, PACKET) for p in sorted(PACKET.rglob("*")) if p.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
               "note": "Index excludes itself; * -text preserves raw bytes. Stage indexed ignored VTK and verify Git blob bytes."})
    for row in files:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
                      "actualFrozenSources": len(sources), "decodedZipMembers": archive["decodedMembers"]}))


if __name__ == "__main__":
    main()
