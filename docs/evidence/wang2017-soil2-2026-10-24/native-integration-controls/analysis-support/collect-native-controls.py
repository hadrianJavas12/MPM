"""Package existing native-control evidence; never rerun a test or mutate inputs."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
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
    repo = Path(args.repository).resolve()
    destination = Path(args.destination).resolve()
    raw_root = repo / "output/wang2017-soil2-2026-10-24"
    assert not destination.exists(), "Evidence destination must be fresh."
    destination.mkdir(parents=True)
    (destination / "archive-member-manifests").mkdir()
    (destination / "analysis-support").mkdir()
    shutil.copy2(__file__, destination / "analysis-support/collect-native-controls.py")
    archives = []
    all_input_hashes = {}
    for name in ["native-controls-001", "native-controls-002", "native-controls-003", "integration-controls-001"]:
        root = raw_root / name
        mapped = []
        excluded = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if ".native-cache" in relative.parts or path.suffix.lower() == ".fasl":
                excluded.append({"path": relative.as_posix(), "bytes": path.stat().st_size})
                continue
            mapped.append((path, name + "/" + relative.as_posix()))
        if name.startswith("native-"):
            mapped.append((repo / "output" / ("wang2017-soil2-2026-10-24-" + name + ".log"), name + "/native.log"))
        zip_path = destination / (name + ".zip")
        records = []
        with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, member in mapped:
                data = path.read_bytes()
                expected = sha(data)
                all_input_hashes[str(path)] = expected
                archive.writestr(member, data)
                records.append({"path": member, "bytes": len(data), "sha256": expected})
        verified = []
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.testzip() is None
            assert sorted(archive.namelist()) == sorted(row["path"] for row in records)
            for row in records:
                data = archive.read(row["path"])
                assert len(data) == row["bytes"] and sha(data) == row["sha256"], row["path"]
                verified.append(row["path"])
        manifest_name = "archive-member-manifests/" + name + ".json"
        save(destination / manifest_name, {"archive": zip_path.name, "scope": "Every archived member verified by decoded bytes/size/SHA256; FASL/cache exclusion listed separately.", "members": records, "excludedNativeCacheOrFasl": excluded})
        archives.append({"path": zip_path.name, "bytes": zip_path.stat().st_size, "sha256": sha(zip_path.read_bytes()), "members": len(records), "verifiedMembers": len(verified), "excludedFiles": len(excluded), "excludedBytes": sum(row["bytes"] for row in excluded), "memberManifest": manifest_name})
    final = raw_root / "native-controls-003"
    before = load(final / "source-proof-before.json")["files"]
    after = load(final / "source-proof-after.json")["files"]
    assert before == after and len(before) == 271
    for row in before:
        assert sha((final / row["path"]).read_bytes()) == row["sha256"].lower()
    unchanged = all(sha(Path(path).read_bytes()) == expected for path, expected in all_input_hashes.items())
    assert unchanged
    save(destination / "archive-verification.json", {
        "status": "PASS", "verifiedUtc": datetime.now(timezone.utc).isoformat(),
        "archives": archives, "totalVerifiedMembers": sum(row["verifiedMembers"] for row in archives),
        "native003FrozenSources": len(before), "native003BeforeAfterAndCurrentFrozenHashesMatch": True,
        "originalInputsUnchangedDuringPackaging": unchanged,
        "testsExecutedByCollector": 0,
        "scope": "Archive-byte integrity only. Native003 full first-party freeze does not extend to the separate unfrozen root integration suite."
    })
    readme = """# Windows native Soil2 integration control evidence

Date: 24 October 2026, Asia/Jakarta. This packet preserves the failed harness
attempts as well as the completed integration controls. Packaging executes no
solver or numerical tests and leaves the original output intact.

| Attempt | Actual result | Evidence and interpretation |
| --- | --- | --- |
| `native-controls-001` | Process exit1; zero controls executed | Test bootstrap loaded its helper inside the form that compiled the context binding. The context was lexical, the native proof encountered NIL, and execution stopped before controls. Copied source files/manifest and raw log remain; no verified frozen execution or PASS is claimed. |
| `native-controls-002` |18 material groups PASS,0 FAIL,0 NOT_RUN; overall process exit1 | Frozen execution and before proof succeeded. After controls completed, the harness attempted to write the fresh-only `source-provenance.json` twice and failed. Result/before proof/raw failure log remain. No successful overall process exit is claimed. |
| `native-controls-003` | Windows native process exit0;18 PASS,0 FAIL,0 NOT_RUN;28 constitutive calls; zero MPM updates | Corrected harness preserves separate before/after provenance. All271 selected frozen source bytes match the before/after SHA256 records and retained files. Actual copied `kirchoff.dll` mapping verified using `GetModuleHandleW/GetModuleFileNameW`. |
| `integration-controls-001` | Three actual Windows native commands exit0:34 existing MC controls,10 framework contracts and3 Soil2 input controls | Raw logs, status/input JSON and the three executed-test source copies are retained. This root suite did **not** use the full first-party source freeze; the271-file frozen-source claim applies only to `native-controls-003`. |

## Scope of the18 native Soil2 groups

The completed adapter checks cover fixed material inputs and owned state,
elastic/analytical plastic return and residual tail, tensor history versus summed
increment history, stress/engineering shear factors, Cauchy/Kirchhoff scaling,
proper polar recovery, nonzero-history rigid rotation, time-varying observer
covariance, noncommuting elastic-rotation refinement, repeated trials, apex and
history-decrease rejection, and snapshot/copy/reinitialize/loadstep transactions.
Committed tensor and embedded baseline arrays are deliberately mutated to test
independent ownership. The outer stress transaction is exercised by production
`:around` dispatch with a test-only primary method that mutates fields then
fails. It is **not** an actual mesh/grid or solver step.

The declared model is an experimental signed-tensor Soil2 accumulator with
incremental polar corotation and a monotonic loading scope gate. There is no
hidden maximum-history or apex adjustment. These controls do not establish a
landslide, paper/FEM curve agreement, irreversible behavior for arbitrary paths,
mesh objectivity, or experimental validation.

## Archive contents and verification

Each attempt has its own ZIP. Retained contents include all available copied
sources and manifests, native DLL, before/after source and runtime proofs,
result/status JSON and raw logs. `native.log` inside each native ZIP is the
unaltered adjacent launcher log. Source snapshots in failed attempts are retained
as historical evidence, not represented as a completed execution proof.

Private `.native-cache` files and any `.fasl` files are excluded to keep the
packet practical. Their original raw folders remain on disk; exclusion paths and
sizes are enumerated per archive. Available runtime provenance still records its
ASDF/FASL references, but these omitted compiled binaries cannot be recovered
from this packet. Third-party dependencies remain external and are outside the
first-party frozen-source claim.

`archive-member-manifests/*.json` records every included member's byte length and
SHA256. The collector decodes every member and verifies both, checks ZIP CRCs,
and checks the complete name inventory. `archive-verification.json` records the
result and confirms inputs were unchanged during packaging. `evidence-manifest.json`
and `SHA256SUMS` index all packet artifacts except those two self-referential
index files. Exact packaging source is under `analysis-support/`.
"""
    (destination / "README.md").write_text(readme, encoding="utf-8")
    (destination / ".gitattributes").write_text("* -text -whitespace\n", encoding="ascii")
    artifacts = []
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name not in {"evidence-manifest.json", "SHA256SUMS"}:
            artifacts.append({"path": path.relative_to(destination).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())})
    save(destination / "evidence-manifest.json", {"schemaVersion": 1, "scope": "Retained Windows native integration control evidence; no numerical tests rerun during packaging.", "artifacts": artifacts})
    (destination / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["path"] + "\n" for row in artifacts), encoding="ascii")
    assert all(sha((destination / row["path"]).read_bytes()) == row["sha256"] and (destination / row["path"]).stat().st_size == row["bytes"] for row in artifacts)
    print(json.dumps({"status": "PASS", "archives": archives, "indexedArtifacts": len(artifacts), "totalVerifiedMembers": sum(row["members"] for row in archives), "packetBytes": sum(path.stat().st_size for path in destination.rglob("*") if path.is_file())}, indent=2))


if __name__ == "__main__":
    main()
