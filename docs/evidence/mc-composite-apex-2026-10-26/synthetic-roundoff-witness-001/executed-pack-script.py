"""Collect the FIRST existing synthetic witness only; no witness/native rerun."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
NAME = "synthetic-roundoff-witness-001"
RUN = RAW / NAME
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26" / NAME
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def main():
    if PACKET.exists():
        raise RuntimeError("Preserve previous witness packet; no overwrite")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; no historical main call.
    h.PACKET = PACKET
    result = h.read_json(RUN / "result.json")
    command = h.read_json(RAW / (NAME + "-command.json"))
    native_exit = h.read_json(RAW / (NAME + "-exit.json"))
    observations = result["observations"]
    production = observations["productionOutcome"]
    floating = observations["floatingGuardReconstruction"]
    exact = observations["exactRationalWitness"]
    failed_guards = [row["name"] for row in floating["checks"] if row["passed"] is False]
    if not (native_exit["exitCode"] == 0 and native_exit.get("endedUtc")
            and result["passed"] is True and result["failure"] is None
            and result["explicitProductionProjectorCalls"] == 1
            and result["physicalUpdateAttempts"] == result["nativeConstitutiveCalls"] == 0
            and result["oldControlsCalled"] == result["actualFailedTrialReplayCalls"] == 0
            and production["accepted"] is False and production["materialError"] is True
            and production["reason"] == "Composite apex compliance, flow, yield or work identity failed"
            and production["details"] == "NIL" and production["diagnosticPresent"] is False
            and failed_guards == ["work-identity"] and len(floating["checks"]) == 8
            and exact["allIdentitiesHold"] is True and exact["checks"] == [True] * 5):
        raise RuntimeError("Original one-fixture negative production/exact witness scope differs")
    rows = h.read_json(RUN / "source/source-manifest.json")["files"]
    source_index = {row["path"]: row for row in rows}
    if len(source_index) != len(rows) or len(rows) != 290:
        raise RuntimeError("Original witness source membership differs")
    checked = []
    for row in rows:
        path = (RUN / row["path"]).resolve()
        if not path.is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Original source path escaped witness snapshot")
        actual = h.record(path)
        if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError("Original source payload changed: " + row["path"])
        checked.append(actual)
    before, after = [h.read_json(RUN / name) for name in ("source-proof-before.json", "source-proof-after.json")]
    expected = {name: row["sha256"] for name, row in source_index.items()}
    for proof in (before, after):
        if len(proof["files"]) != 290 or {row["path"]: row["sha256"] for row in proof["files"]} != expected:
            raise RuntimeError("Original before/after witness source proof differs from original preload manifest")
    backend = result["nativeBackend"]
    dll = source_index["source/libs/kirchoff.dll"]
    for name in ("source-provenance-before.json", "source-provenance.json"):
        provenance = h.read_json(RUN / name)
        if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
                and provenance["nativeBackend"] == backend and backend["sha256"] == dll["sha256"]
                and Path(backend["modulePath"]).resolve() == (RUN / dll["path"]).resolve()
                and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"):
            raise RuntimeError("Original witness stored DLL/runtime proof differs")
    protocol = h.read_json(RUN / "source/inputs/protocol.json")
    if protocol != observations["protocol"]:
        raise RuntimeError("Original frozen protocol differs from result's protocol")
    for loaded, data, key in (
            ("source/materials/models/plastic/mc-composite-apex/projection.lisp", "source/inputs/failed-optional-projector.lisp", "optionalProjectorSha256"),
            ("source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp", "source/inputs/failed-shared-projector.lisp", "sharedProjectorSha256")):
        if source_index[loaded]["sha256"] != source_index[data]["sha256"] or source_index[loaded]["sha256"] != protocol[key]:
            raise RuntimeError("Called unchanged projector differs from original frozen failed-source DATA")
    members = {name: path for name, path in h.tree_files(RUN).items()
               if ".native-cache" not in Path(name).parts}
    actual_sources = {name for name in members if name.startswith("source/") and name != "source/source-manifest.json"}
    if actual_sources != set(source_index):
        raise RuntimeError("Complete witness source archive membership differs")
    runtime = {"adjacent/" + p.name: p for p in sorted(RAW.glob(NAME + "*")) if p.is_file()}
    members.update(runtime)
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.write_json(PACKET / "packaging-invocation.json", {"argv": sys.argv, "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "Collect existing witness only; read/copy/hash/ZIP/CRC/decoded-byte comparison; no native/projector/test/replay/MPM rerun"})
    archive = h.archive("complete-native-source-result-runtime-and-negative-rejection", members)
    decoded = {row["path"]: row for row in archive["members"]}
    for name, row in source_index.items():
        if (decoded[name]["bytes"], decoded[name]["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError("Archived original witness source changed")
    for name, path in members.items():
        if not name.startswith("source/"):
            h.copy(path, PACKET / "original-records" / name)
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    h.copy(RUN / "source/case.lisp", PACKET / "original-test-and-protocol/mc-composite-apex-roundoff-witness.lisp")
    h.copy(RUN / "source/inputs/protocol.json", PACKET / "original-test-and-protocol/mc-composite-apex-roundoff-witness.protocol.json")
    h.write_json(PACKET / "recorded-byte-bindings.json", {"originalSourceRows": checked, "allMatched": True,
        "originalBeforeAfterSourceProofsMatchPreloadManifest": True, "originalRuntimeBackendAsRecorded": backend,
        "scope": "Original recorded source and DLL proof bound to retained payloads; no new native/module mapping or arithmetic reconstruction"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": [archive],
        "actualNativeSourceMembers": len(rows), "totalDecodedMembers": archive["decodedMembers"],
        "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {"schema": "cl-mpm.mc-composite-apex.synthetic-roundoff.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeSourceCommit": command["sourceCommit"],
        "nativeExit": native_exit["exitCode"], "nativeEndedUtc": native_exit["endedUtc"], "nativeSourceFiles": len(rows),
        "originalResultPassed": result["passed"], "explicitProductionProjectorCalls": 1,
        "physicalUpdateAttempts": 0, "nativeConstitutiveCalls": 0, "oldControlsCalled": 0,
        "actualFailedTrialReplayCalls": 0, "negativeProductionOutcomeAsReceived": production,
        "soleFailedFloatingGuardAsReceived": failed_guards, "exactRationalWitnessAsReceived": exact,
        "scope": result["scope"], "landslideVerified": False, "scientificallyValidated": False,
        "operations": "Collect existing original record bytes only; no witness/projector/native/MPM/test/replay/audit/render or process query repeated"})
    (PACKET / "README.md").write_text(
        "# ONE synthetic roundoff witness: original native evidence\n\n"
        "FIRST synthetic witness completes native exit0 on26October2026. It makes one explicit unchanged production projector call, zero native constitutive calls, zero MPM updates, zero old controls and zero actual failed-trial replay calls. The expected production result is rejection, with the retained material-error reason and NIL/no diagnostic. The independently reconstructed floating guards fail only work-identity; the five exact rational identities all hold.\n\n"
        "This is a preregistered synthetic arithmetic fixture on exact binary64 trial values and evaluated binary64 cap/G/K. It demonstrates a cancellation-sensitive rejection mechanism; it does not identify the unavailable actual failed fine-run trial, evaluate transcendental functions exactly, establish a full-MPM restart or validate scientific landslide behavior. No production tolerance or source was changed by collection.\n\n"
        "One ZIP retains all290original frozen source/input files, original test and protocol, source manifest, before/after source and runtime proofs, mapped DLL record, exact command, native exit/log and the complete negative production result. Original test/protocol are also directly inspectable. Private caches are excluded. Every archived member is CRC-tested, decoded and byte-compared; all source bytes bind to their original pre-load and before/after hashes. Stored runtime mapping remains the original record, without an after-exit process query. No witness, arithmetic reconstruction, native, test or MPM operation was repeated.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself. * -text preserves exact bytes; single complete source ZIP."})
    for row in artifacts:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed witness artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
        "decodedZipMembers": archive["decodedMembers"], "nativeSourceFiles": len(rows),
        "nativeExit": native_exit["exitCode"], "projectorCalls": 1, "physicalUpdates": 0, "actualReplayCalls": 0}, indent=2))


if __name__ == "__main__":
    main()
