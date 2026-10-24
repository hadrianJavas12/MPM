"""One launch-only provenance capture; never reads active CSV/VTK/logs or runs tests."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data):
    return json.loads(data.decode("utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    repo = Path(args.repository).resolve()
    destination = Path(args.destination).resolve()
    run = repo / "output/wang2017-soil2-2026-10-24/apex-fast-010-001"
    detached = run.with_name(run.name + "-detached")
    assert not destination.exists(), "Launch evidence directory must be fresh."
    capture_time = datetime.now(timezone.utc)
    stamp = capture_time.strftime("%Y%m%dT%H%M%SZ")
    # Read each changing JSON exactly once, then operate on captured bytes.
    status_bytes = run.with_name(run.name + "-status.json").read_bytes()
    manifest_bytes = (run / "manifest.json").read_bytes()
    status = parse(status_bytes)
    manifest = parse(manifest_bytes)
    assert status["sourceCommitAtLaunch"] == "55bc85d9d4567b6677439846035127751fbc4c7f"
    source_manifest_bytes = (run / "source/source-manifest.json").read_bytes()
    provenance_bytes = (run / "source-provenance.json").read_bytes()
    source_manifest = parse(source_manifest_bytes)
    provenance = parse(provenance_bytes)
    assert provenance["sourceSnapshotExactLoadedBytes"] is True
    assert provenance["copiedByteEqualityBeforeLoad"] is True
    destination.mkdir(parents=True)
    (destination / "analysis-support").mkdir()
    shutil.copy2(__file__, destination / "analysis-support/collect-launch-provenance.py")
    members = {}
    static_inputs = {}
    source_checks = []
    def static(path):
        data = path.read_bytes()
        static_inputs[str(path)] = sha(data)
        return data
    for row in source_manifest["files"]:
        frozen = run / row["path"]
        data = static(frozen)
        original = Path(row["originalPath"])
        workspace_data = static(original)
        checked = {"path": row["path"], "originalPath": row["originalPath"], "bytes": len(data),
                   "expectedBytes": row["bytes"], "expectedSha256": row["sha256"].lower(),
                   "frozenSha256": sha(data), "workspaceSha256": sha(workspace_data)}
        assert len(data) == row["bytes"] and sha(data) == row["sha256"].lower(), row["path"]
        assert sha(data) == sha(workspace_data), row["originalPath"]
        source_checks.append(checked)
        members[row["path"]] = data
    assert len(source_checks) == len(provenance["copiedFiles"]) and len(source_checks) > 0
    members["source/source-manifest.json"] = source_manifest_bytes
    members["launch/source-provenance.json"] = provenance_bytes
    members[f"launch/status-snapshot-{stamp}.json"] = status_bytes
    members[f"launch/manifest-snapshot-{stamp}.json"] = manifest_bytes
    launch_json = run.with_name(run.name + "-launch.json")
    members["launch/adjacent-launch.json"] = static(launch_json)
    for name in ["launch-proof.json", "launch-request.json", "launch-request.ps1", "worker-start.json"]:
        members["launch/detached/" + name] = static(detached / name)
    proof = parse(members["launch/detached/launch-proof.json"])
    request = parse(members["launch/detached/launch-request.json"])
    worker_start = parse(members["launch/detached/worker-start.json"])
    assert sha(members["launch/detached/launch-request.json"]) == proof["requestSha256"].lower()
    assert sha(members["launch/detached/launch-request.ps1"]) == proof["workerScriptSha256"].lower()
    assert proof["returnValue"] == 0 and proof["startupObserved"]
    assert proof["workerProcessId"] == worker_start["processId"] == 23904
    assert proof["workerCreationUtc"] == worker_start["creationUtc"]
    assert proof["workerSessionId"] == worker_start["sessionId"] == 11
    wrapper_path = Path(request["wrapperPath"])
    members["support/run-wang2017-trial.ps1"] = static(wrapper_path)
    members["support/start-wang2017-detached.ps1"] = static(repo / "scripts/start-wang2017-detached.ps1")
    assert sha(members["support/run-wang2017-trial.ps1"]) == request["wrapperSha256"].lower()
    post_checks = []
    for relative, expected in sorted(status["postprocessorSha256"].items()):
        data = static(repo / relative)
        assert sha(data) == expected.lower(), relative
        post_checks.append({"path": relative, "bytes": len(data), "sha256": sha(data), "launchRecordedSha256": expected.lower()})
        members["support/" + relative] = data
    assert len(post_checks) == 3
    backend = provenance["nativeBackend"]
    assert Path(backend["modulePath"]).resolve() == (run / "source/libs/kirchoff.dll").resolve()
    assert sha(members["source/libs/kirchoff.dll"]) == backend["sha256"].lower()
    assert backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW" and backend["nativeMcEntryPresent"]
    # One identity observation, not a polling loop; no command line/environment read.
    expected_identities = status["processIdentity"]
    pids = [proof["workerProcessId"]] + [int(item["pid"]) for item in expected_identities.values()]
    query = "Get-CimInstance Win32_Process -Filter '" + " OR ".join("ProcessId=" + str(pid) for pid in pids) + "' | Select-Object ProcessId,ParentProcessId,Name,SessionId,@{n='creationUtc';e={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json"
    observed = subprocess.run([shutil.which("pwsh"), "-NoProfile", "-NonInteractive", "-Command", query], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    assert observed.returncode == 0, observed.stderr
    identity_data = json.loads(observed.stdout)
    if isinstance(identity_data, dict):
        identity_data = [identity_data]
    by_pid = {int(item["ProcessId"]): item for item in identity_data}
    assert sorted(by_pid) == sorted(pids)
    assert all(item["SessionId"] == 11 for item in identity_data)
    assert by_pid[23904]["ParentProcessId"] == proof["workerParentProcessId"]
    for name, expected in expected_identities.items():
        actual = by_pid[expected["pid"]]
        assert datetime.fromisoformat(actual["creationUtc"].replace("Z", "+00:00")) == datetime.fromisoformat(expected["createdUtc"].replace("Z", "+00:00")), name
    identity_record = {"scope": "Single process-identity observation during launch capture; not a health monitor or completion proof.", "observedUtc": datetime.now(timezone.utc).isoformat(), "processes": identity_data, "command": query}
    members["launch/process-identities-at-capture.json"] = (json.dumps(identity_record, indent=2) + "\n").encode()
    members["launch/source-workspace-checks.json"] = (json.dumps(source_checks, indent=2) + "\n").encode()
    members["launch/postprocessor-checks.json"] = (json.dumps(post_checks, indent=2) + "\n").encode()
    archive_path = destination / "frozen-launch-sources.zip"
    member_records = []
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            archive.writestr(name, data)
            member_records.append({"path": name, "bytes": len(data), "sha256": sha(data)})
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == sorted(members)
        for row in member_records:
            data = archive.read(row["path"])
            assert len(data) == row["bytes"] and sha(data) == row["sha256"]
    unchanged = all(sha(Path(path).read_bytes()) == expected for path, expected in static_inputs.items())
    assert unchanged
    save(destination / "archive-member-manifest.json", {"archive": archive_path.name, "members": member_records})
    verification = {
        "status": "LAUNCH_PROVENANCE_VERIFIED_ONLY", "captureUtc": capture_time.isoformat(),
        "sourceCommitAtLaunch": status["sourceCommitAtLaunch"], "nativeStatusAtCapture": status["status"],
        "manifestCompleteAtCapture": manifest.get("complete"), "phaseAtCapture": manifest.get("phase"),
        "sourceFiles": len(source_checks), "frozenManifestAndWorkspaceBytesMatch": True,
        "sourceSnapshotExactLoadedBytesClaim": provenance["sourceSnapshotExactLoadedBytes"],
        "copiedByteEqualityBeforeLoadClaim": provenance["copiedByteEqualityBeforeLoad"],
        "nativeBackend": backend, "postprocessors": post_checks, "singleIdentityObservation": identity_record,
        "staticInputsUnchangedDuringCapture": unchanged, "archive": archive_path.name,
        "archiveBytes": archive_path.stat().st_size, "archiveSha256": sha(archive_path.read_bytes()),
        "verifiedArchiveMembers": len(member_records), "testsOrSolverRunsExecuted": 0,
        "excluded": ["Active CSV/VTK/logs were not read or archived.", "Private native cache/FASL files are excluded; runtime provenance references may remain.", "No worker-exit or final audit/render output was requested or represented as completion."],
        "completionClaim": False, "scientificValidation": False,
    }
    save(destination / "launch-verification.json", verification)
    (destination / "README.md").write_text("""# Opt-in composite-apex slope: LAUNCH-ONLY provenance

This packet captures the opt-in composite-apex Soil2 slope launch on24October2026,
source `55bc85d9d4567b6677439846035127751fbc4c7f`. It verifies launch identity and selected frozen input bytes only.
**It does not establish simulation completion, a landslide or scientific PASS.**

The case is accelerated0.01m/s loading (100times paper rate), targeting0.06m
over6s. It is not a600s paper-rate run. Soil2 uses the declared signed plastic
tensor norm, incremental polar corotation approximation and monotonic history
scope rejection. This explicitly NEW opt-in model adds positive hydrostatic
apex volumetric flow gA=p. It is different constitutive physics from the retained
strict baseline and is not a paper-specified apex convention. No hidden history
maximum, parameter tuning or baseline switch is implied.

`frozen-launch-sources.zip` preserves the observed selected frozen source/DLL files (count recorded in verification),
source manifest and provenance, exact launch request/worker script and proof,
initial worker identity, the adjacent launch record, and timestamped copies of
status/manifest read once during capture. It also contains the three launch-hashed
postprocessors and trusted wrapper/source snapshots. Request and worker bytes
match the launch-recorded hashes; wrapper bytes match the request hash. The
detached-launcher file is a capture-time support snapshot, not an independently
pre-hashed executed-source claim.

All frozen files match their pre-load manifest hashes/sizes and their original
workspace bytes during this capture. The actual copied `kirchoff.dll` path/hash
is recorded by `GetModuleHandleW/GetModuleFileNameW`. Frozen-byte flags are the
runtime source-provenance claims, supplemented by the independent byte checks.
Third-party sources/FASLs and non-ASDF arbitrary loads are outside that claim.

One narrow Windows process identity observation checks WMI worker23904,
wrapper21136, cmd49564 and SBCL23428, including creation times and SessionId11.
This is not polling or a completion/continued-health guarantee. WMI detachment
does not prove immunity to logoff, sleep, reboot or provider-job policy.

Active CSV, VTK and log files were deliberately **not read or archived**.
Private native cache/FASLs are omitted. The immutable launch documents/source
files were checked unchanged during packaging. Changing status/manifest were
read once and represented only by timestamped snapshots.

Every ZIP member was decoded and checked for exact size/SHA256, complete member
inventory and CRC. `archive-member-manifest.json`, `launch-verification.json`,
`evidence-manifest.json` and `SHA256SUMS` retain the checks. Exact collector source
is under `analysis-support/`. No solver or numerical tests were executed here.
""", encoding="utf-8")
    (destination / ".gitattributes").write_text("* -text -whitespace\n", encoding="ascii")
    artifacts = []
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name not in {"evidence-manifest.json", "SHA256SUMS"}:
            data = path.read_bytes()
            artifacts.append({"path": path.relative_to(destination).as_posix(), "bytes": len(data), "sha256": sha(data)})
    save(destination / "evidence-manifest.json", {"scope": "Launch-only retained source/runtime provenance, no completion or scientific PASS claim.", "artifacts": artifacts})
    (destination / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["path"] + "\n" for row in artifacts), encoding="ascii")
    assert all(sha((destination / row["path"]).read_bytes()) == row["sha256"] for row in artifacts)
    print(json.dumps({"status": verification["status"], "sourceFiles": len(source_checks), "frozenAndWorkspaceBytesMatch": True,
                      "sourceCommitAtLaunch": status["sourceCommitAtLaunch"], "statusAtCapture": status["status"],
                      "completeAtCapture": manifest.get("complete"), "archiveSha256": verification["archiveSha256"],
                      "verifiedArchiveMembers": len(member_records), "indexedArtifacts": len(artifacts), "archiveBytes": archive_path.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
