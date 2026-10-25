"""One authorized synthetic invocation from an exact pre-copied source mirror."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/unnotched-gravity-2026-10-25/refinement-observer-controls-001"
SOURCES = ["tests/analysis/gravity-refinement-observer.py", "scripts/review-gravity-refinement.py",
           "scripts/review-gravity-slope.py", "scripts/plot_m5_cliff_comparison.py",
           "research/references/unnotched-mc-ssr/contract.json",
           "research/references/unnotched-mc-ssr/refinement-contract.json",
           "research/references/unnotched-mc-ssr/refinement-audit-contract.json"]


def write(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def proof():
    rows = []
    for name in SOURCES:
        p = OUTPUT / "source" / name
        payload = p.read_bytes()
        rows.append({"path": "source/" + name, "bytes": len(payload),
                     "sha256": hashlib.sha256(payload).hexdigest()})
    return rows


if OUTPUT.exists():
    raise RuntimeError("Preserve previous attempt; output must be fresh")
OUTPUT.mkdir(parents=True)
shutil.copyfile(__file__, OUTPUT / "executed-orchestration.py")
for name in SOURCES:
    source, target = ROOT / name, OUTPUT / "source" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        raise RuntimeError("Pre-execution source byte mismatch")
before = proof()
write("source-proof-before.json", {"files": before, "phase": "before first synthetic invocation"})
command = [sys.executable, str(OUTPUT / "source/tests/analysis/gravity-refinement-observer.py"), "-v"]
started = datetime.now(timezone.utc).isoformat()
write("command-before-execution.json", {"command": command, "cwd": str(OUTPUT / "source"), "startedUtc": started,
      "scope": "FIRST pure synthetic observer controls; no saved-run reads, solver, material, native replay or rendering"})
with (OUTPUT / "test.log").open("w", encoding="utf-8") as stream:
    result = subprocess.run(command, cwd=OUTPUT / "source", stdout=stream, stderr=subprocess.STDOUT,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
after = proof()
write("source-proof-after.json", {"files": after, "phase": "after first synthetic invocation"})
write("result.json", {"exitCode": result.returncode, "passed": result.returncode == 0,
      "sourceFiles": len(before), "sourceBytesUnchanged": before == after,
      "startedUtc": started, "finishedUtc": datetime.now(timezone.utc).isoformat(),
      "syntheticInvocations": 1, "actualSavedRunAnalysisCalls": 0, "nativeOrMpmCalls": 0,
      "scope": "Only common physical observer helpers on synthetic arrays; not full analysis orchestration/plotting or scientific validation"})
print(json.dumps({"output": str(OUTPUT), "exitCode": result.returncode, "sourceBytesUnchanged": before == after}))
sys.exit(result.returncode if before == after else 2)
