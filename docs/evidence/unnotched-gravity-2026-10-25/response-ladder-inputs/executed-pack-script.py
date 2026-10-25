"""Retain the completed new input-only native gate without repeating it."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
RUN = RAW / "response-ladder-inputs-001"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/response-ladder-inputs"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"
spec = importlib.util.spec_from_file_location("response_input_copy_helpers", HELPER)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
common.PACKET = PACKET
read_json, record, copy, write = common.read_json, common.record, common.copy, common.write_json


def main():
    result = read_json(RUN / "result.json")
    exit_record = read_json(RAW / "response-ladder-inputs-001-exit.json")
    if (not result["passed"] or len(result["passedGroups"]) != 3 or exit_record["exitCode"] != 0
            or result["physicalUpdatesExecuted"] != 0 or result["constitutiveUpdates"] != 0
            or result["constructedParticles"] != 3):
        raise RuntimeError("Expected actual successful new input-only gate; preserve failure separately")
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Packet must be fresh inside workspace")
    rows = read_json(RUN / "source/source-manifest.json")["files"]
    expected = {r["path"]: r for r in rows}
    if len(rows) != 287 or len(expected) != 287:
        raise RuntimeError("Expected287 distinct frozen sources/inputs")
    for name, row in expected.items():
        source = RUN / name
        if not source.resolve().is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Frozen source escapes source directory")
        actual = record(source)
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise RuntimeError("Executed frozen source mismatch")
    for phase in ("before", "after"):
        proof = read_json(RUN / f"source-proof-{phase}.json")["files"]
        if {r["path"]: r["sha256"] for r in proof} != {p: r["sha256"] for p, r in expected.items()}:
            raise RuntimeError("Recorded source proof mismatch")
    provenance = read_json(RUN / "source-provenance.json")
    if (not provenance["sourceSnapshotExactLoadedBytes"] or not provenance["copiedByteEqualityBeforeLoad"]
            or provenance["nativeBackend"]["sha256"] != expected["source/libs/kirchoff.dll"]["sha256"]):
        raise RuntimeError("Actual mapped DLL/loaded-byte proof mismatch")
    inputs = [name for name in expected if name.startswith("source/inputs/cases/benchmarks/gravity-slope-mc-srf-")
              or name.startswith("source/inputs/research/references/unnotched-mc-ssr/response-ladder-")]
    if len(inputs) != 5:
        raise RuntimeError("Actual original/two new cases and two preregistered contracts required")
    original = (RUN / "source/inputs/cases/benchmarks/gravity-slope-mc-srf-1p4.lisp").read_bytes()
    for filename, literal in (("gravity-slope-mc-srf-1p6.lisp", b"(srf 1.6d0)"), ("gravity-slope-mc-srf-2.lisp", b"(srf 2d0)")):
        if original.count(b"(srf 1.4d0)") != 1 or original.replace(b"(srf 1.4d0)", literal) != (RUN / "source/inputs/cases/benchmarks" / filename).read_bytes():
            raise RuntimeError("Frozen executable cases differ beyond SRF literal")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    copy(HELPER, PACKET / "executed-pack-copy-helpers.py")
    write(PACKET / "native-command.json", {
        "workingDirectory": "D:/MPM",
        "command": "windows/cl-mpm.cmd tests/benchmarks/gravity-slope-response-inputs.lisp output/unnotched-gravity-2026-10-25/response-ladder-inputs-001",
        "nativeExit": exit_record["exitCode"],
        "recordedAfterExecution": True,
        "scope": "Actual completed invocation transcribed from retained tool execution; not a pre-launch command attestation"})
    members = {p: RUN / p for p in expected}
    members["source/source-manifest.json"] = RUN / "source/source-manifest.json"
    direct = {}
    for name, source in common.tree_files(RUN).items():
        if not name.startswith("source/"):
            direct[name] = source
            members[name] = source
    for source in (RAW / "response-ladder-inputs-001.log", RAW / "response-ladder-inputs-001-exit.json"):
        members["adjacent/" + source.name] = direct["adjacent/" + source.name] = source
    archive = common.archive("executed-source-native-input-and-runtime", members)
    for name, source in direct.items():
        copy(source, PACKET / name)
    for name in inputs + ["source/source-manifest.json"]:
        copy(RUN / name, PACKET / name)
    write(PACKET / "archive-member-verification.json", archive)
    write(PACKET / "summary.json", {"schema": "cl-mpm.response-ladder.inputs.evidence.v1",
          "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeExit": 0,
          "passedGroups": result["passedGroups"], "actualFrozenSources": len(expected),
          "allOriginalSourceBeforeAfterCurrentBytesMatched": True,
          "nativeBackend": provenance["nativeBackend"], "constructedParticles": 3,
          "constitutiveUpdates": 0, "physicalUpdatesExecuted": 0,
          "onlyExecutableDifference": "Literal SRF1.4->1.6 or2.0; all remaining case bytes identical",
          "onlyCompiledConfigDifferences": ["strengthReductionFactor", "cohesionPa", "frictionRad"],
          "screeningStatus": "NOT_RUN", "landslideVerified": False, "scientificallyValidated": False,
          "operations": "Copy/hash/ZIP/CRC/decoded-byte verification only; no input gate or numerical work repeated"})
    (PACKET / "README.md").write_text(
        "# Finite SSR response ladder: native input gate\n\n"
        "Three NEW input-only groups pass Windows native exit0. All287project/native/input files, including original SRF1.4 case, new SRF1.6/2.0 cases and both preregistered contracts, were copied before project loading. "
        "Recorded before/after/current frozen hashes and actual mapped DLL proof match. New executable case bytes differ only at the one visible SRF literal; compiled configurations differ only in SRF/derived cohesion/friction. "
        "Material class/perfect Cauchy law, elasticity/density/dilation, geometry/BCs/grid/loading/ramp/solver/defaults remain unchanged.\n\n"
        "Three actual native particle constructors verify c=10000/SRF, phi=atan(tan20deg/SRF), psi0 and unchanged class/law with zero initial state. "
        "Constitutive and MPM calls are trapped: both counters remain0. No old passed test suite, tiny solver, full screen, rendering or scientific validation is repeated or claimed. "
        "The declared finite study screens1.6 then2.0, caps at2.0 and stops for integrity-valid coherent motion before same-factor fine confirmation. This input gate does not execute or prove that future response.\n\n"
        "Original source/raw/provenance/log/exit files remain in output/. The ZIP is CRC-tested and every decoded member matches its original byte for byte. "
        "Byte-preserving attributes and artifact index support staged Git blob verification; packaging itself repeats no native/material/MPM work.\n",
        encoding="utf-8", newline="\n")
    files = [record(p, PACKET) for p in sorted(PACKET.rglob("*")) if p.is_file()]
    write(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
          "note": "Index excludes itself; * -text preserves exact raw/source bytes for Git blob verification"})
    for row in files:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Final indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files), "decodedZipMembers": archive["decodedMembers"], "sources": len(expected)}))


if __name__ == "__main__":
    main()
