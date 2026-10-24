"""Copy existing zero-update input evidence byte-exact; no native/video calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

repo = Path(__file__).resolve().parents[2]
raw = repo / "output/wang2017-soil2-2026-10-24/apex-100mm-inputs-001"
dest = repo / "docs/evidence/wang2017-soil2-2026-10-24/apex-100mm-inputs"
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
assert not dest.exists(), "Evidence destination must be fresh."
status, report, decode = map(read, [raw / "status.json", raw / "input-report.json", raw / "completed-video-decode.json"])
assert status["exitCode"] == 0 and report["passed"] is True
assert report["controlsCount"] == 3 and report["physicalUpdatesExecuted"] == 0
assert sorted(report["changedKeys"]) == ["duration", "frames", "targetDisplacement"]
assert sha((raw / "executed-driver.lisp").read_bytes()) == status["driverSha256"].lower()
assert sha((raw / "extended-case.lisp").read_bytes()) == status["caseSha256"].lower()
assert decode["exitCode"] == decode["logBytes"] == (raw / "completed-video-decode.log").stat().st_size == 0
assert sha((repo / decode["video"]).read_bytes()) == decode["sha256"].lower()
dest.mkdir(parents=True)
originals = []
for path in sorted(raw.rglob("*")):
    if path.is_file():
        relative = path.relative_to(raw)
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        target.write_bytes(data)
        assert target.read_bytes() == data
        originals.append({"path": relative.as_posix(), "bytes": len(data), "sha256": sha(data)})
(dest / "analysis-support").mkdir()
shutil.copy2(__file__, dest / "analysis-support/collect-apex-100mm-inputs.py")
(dest / "README.md").write_text("""# Apex100mm endpoint input gate

Actual Windows native command: exit0,24October2026,13:46:47–13:47:12WIB.
Three input-control groups PASS; zero physical updates, point projections or
solver/restart calls. The captured workspace was HEAD `dfb9b11` plus the new
uncommitted declarative endpoint case. This gate was **workspace-loaded, not a
fully frozen project execution**. Exact executed driver, previous/new cases,
report, raw log and status are copied byte-exact.

Only three compiled configuration keys differ: target displacement0.06→0.1m,
derived duration6→10s and frames61→101. The opt-in apex class/strength and all
other recorded geometry/numerical settings remain the same, including0.01m/s
loading and45000update cap. This prepares a longer accelerated run; it does
not establish its completion, a landslide,600s paper-rate behavior or scientific
agreement. Positive volumetric apex flow remains an explicitly changed model.

The two `completed-video-decode` artifacts are an already completed full decode
of the earlier6s completed video, exit0 with empty error log. They are retained
without decoding or rendering again; the referenced MP4 hash was checked only.
They do not constitute new simulation evidence for the100mm endpoint.

All original bytes/lengths/SHA256 were checked during this plain-copy package.
`copy-verification.json`, `evidence-manifest.json` and `SHA256SUMS` retain the
verification; exact collector source is under `analysis-support/`. No native
test, solver, replay, render or decode was executed during packaging. Raw inputs
remain intact. The two final index files are excluded from their own index.
""", encoding="utf-8")
(dest / ".gitattributes").write_text("* -text -whitespace\n", encoding="ascii")
verification = {"status": "PASS_BYTE_PRESERVING_COPY", "verifiedUtc": datetime.now(timezone.utc).isoformat(),
                "originalFiles": originals, "nativeExitCode": status["exitCode"], "controlsCount": report["controlsCount"],
                "physicalUpdatesExecuted": 0, "workspaceExecutionNotFullyFrozen": True,
                "existingCompletedVideoDecodeNotRepeated": True, "numericalOrMediaCallsDuringPackaging": 0}
(dest / "copy-verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
entries = []
for path in sorted(dest.rglob("*")):
    if path.is_file():
        data = path.read_bytes()
        entries.append({"path": path.relative_to(dest).as_posix(), "bytes": len(data), "sha256": sha(data)})
(dest / "evidence-manifest.json").write_text(json.dumps({"scope": "Workspace-loaded zero-update endpoint input gate, not a full run or frozen-project proof", "entries": entries}, indent=2) + "\n", encoding="utf-8")
(dest / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["path"] + "\n" for row in entries), encoding="ascii")
assert all((dest / row["path"]).stat().st_size == row["bytes"] and sha((dest / row["path"]).read_bytes()) == row["sha256"] for row in entries)
assert all(sha((raw / row["path"]).read_bytes()) == row["sha256"] for row in originals)
print(json.dumps({"status": verification["status"], "originalFilesCopied": len(originals), "verifiedArtifacts": len(entries), "packetBytes": sum(path.stat().st_size for path in dest.rglob("*") if path.is_file()), "testsOrDecodeRepeated": 0}, indent=2))
