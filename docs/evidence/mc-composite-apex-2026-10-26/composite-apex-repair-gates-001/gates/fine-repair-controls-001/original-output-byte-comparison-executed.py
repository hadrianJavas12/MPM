"""One retained tiny-run byte comparison; never run solver, tests or audits."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
old = root / "output/mc-composite-apex-2026-10-26/fine-controls-001"
new = root / "output/mc-composite-apex-2026-10-26/fine-repair-controls-001"
target = new / "original-output-byte-comparison.json"
assert not target.exists(), "Preserve earlier comparison"
def record(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
before = record(Path(__file__))
rows = []
for name in ["history.csv", "particles.csv"] + [f"vtk/particles_{i:04d}.vtk" for i in range(3)]:
    a, b = old / "observations" / name, new / "observations" / name
    rows.append({"relative": name, "original": record(a), "repaired": record(b),
                 "bytesIdentical": a.read_bytes() == b.read_bytes()})
result = {"status": "PASS" if all(row["bytesIdentical"] for row in rows) else "FAIL",
          "executedScriptBefore": before, "comparedFiles": rows,
          "createdUtc": datetime.now(timezone.utc).isoformat(),
          "scope": "Two CSVs and three VTKs from two existing bounded native gates; no apex activation guaranteed; zero new native, test, audit or rendering calls"}
assert record(Path(__file__)) == before
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "files": len(rows)}))
sys.exit(0 if result["status"] == "PASS" else 1)
