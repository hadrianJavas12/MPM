"""Package existing pure synthetic observer proof; do not repeat controls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "output/unnotched-gravity-2026-10-25/refinement-observer-controls-001"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/refinement-observer-controls"


def record(path, root):
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write(name, value):
    (PACKET / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


result = json.loads((RUN / "result.json").read_text())
before = json.loads((RUN / "source-proof-before.json").read_text())["files"]
after = json.loads((RUN / "source-proof-after.json").read_text())["files"]
log = (RUN / "test.log").read_text()
if (result["exitCode"] != 0 or not result["sourceBytesUnchanged"] or before != after or len(before) != 7
        or "Ran 9 tests" not in log or "\nOK\n" not in log or result["syntheticInvocations"] != 1):
    raise RuntimeError("Expected retained successful FIRST9 synthetic controls with unchanged frozen bytes")
for row in before:
    if record(RUN / row["path"], RUN) != row:
        raise RuntimeError("Frozen synthetic source changed")
if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
    raise RuntimeError("Use a fresh packet inside workspace")
PACKET.mkdir(parents=True)
(PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
shutil.copyfile(__file__, PACKET / "executed-pack-script.py")
members = {p.relative_to(RUN).as_posix(): p for p in sorted(RUN.rglob("*"))
           if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
archive = PACKET / "exact-synthetic-source-command-and-result.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    for name, source in members.items():
        z.write(source, name)
decoded = []
with zipfile.ZipFile(archive) as z:
    if z.testzip() is not None or sorted(z.namelist()) != sorted(members):
        raise RuntimeError("Archive CRC/member failure")
    for name, source in members.items():
        payload = z.read(name)
        if payload != source.read_bytes():
            raise RuntimeError("Decoded member byte mismatch")
        decoded.append({"path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
        destination = PACKET / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if destination.read_bytes() != payload:
            raise RuntimeError("Direct copied artifact mismatch")
write("archive-member-verification.json", {"crcPass": True, "allDecodedBytesMatchOriginals": True,
       "decodedMembers": len(decoded), "members": decoded})
write("summary.json", {"createdUtc": datetime.now(timezone.utc).isoformat(), "syntheticGroupsPassed": 9,
       "syntheticInvocations": 1, "frozenSourceFiles": 7, "beforeAfterAndCurrentFrozenBytesMatch": True,
       "actualSavedRunAnalysisCalls": 0, "nativeOrMpmCalls": 0,
       "scope": "Fixed-metre observer helpers only; not full orchestration guards, saved native integrity, fine/coarse result or scientific validation",
       "packaging": "Read/copy/hash/ZIP/CRC/decoded-byte comparison only; no tests or numerical analysis repeated"})
(PACKET / "README.md").write_text(
    "# Fixed physical refinement observer: synthetic controls\n\n"
    "The FIRST invocation passes9pure synthetic groups, exit0. Seven exact sources (test, new wrapper, old reviewer, imported reader and three contracts) were copied before execution into a private mirrored tree; all before/after/current hashes match. "
    "The test loads copied modules and creates only synthetic particle arrays; no actual saved-run data, native material, MPM, replay or render is executed.\n\n"
    "Controls cover equivalent coarse/fine mass, false apparent h-scaled motion, fixed physical cohort/adjacency, post2s displacement reference, insufficient persistence, strict velocity/toe thresholds, contract drift and unchanged inputs. "
    "They do not test every CLI/orchestration failure path or establish actual landslide, refinement convergence or scientific validation. No failed/repeated invocation occurred.\n\n"
    "Exact command/stdout/exit, orchestration and source mirror remain retained. The ZIP was CRC-tested and every decoded member compared byte for byte against the original. Packaging repeated no test or analysis; originals remain in output/.\n",
    encoding="utf-8")
files = [record(p, PACKET) for p in sorted(PACKET.rglob("*")) if p.is_file()]
write("artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
       "note": "Index excludes itself. * -text preserves exact indexed source/log bytes."})
for row in files:
    if record(PACKET / row["path"], PACKET) != row:
        raise RuntimeError("Final indexed artifact changed")
print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files), "decodedZipMembers": len(decoded), "groupsPassed": 9}))
