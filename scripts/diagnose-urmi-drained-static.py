"""One frozen, restricted static diagnosis after the declared preparation cap."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
from collections import Counter

import numpy as np


def record(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "output/urmi-mc-damage40-2026-10-27/drained-static-001"
    output.mkdir(exist_ok=False)
    frozen = output / "analysis"
    frozen.mkdir()
    sources = [Path(__file__), root / "scripts/analysis/slope_stability.py",
               root / "research/notes/urmi-mc-damage40-2026-10-26/drained-static-contract.json"]
    bindings = []
    for source in sources:
        copy = frozen / source.name
        shutil.copyfile(source, copy)
        assert record(source)["sha256"] == record(copy)["sha256"]
        bindings.append({"source": record(source), "copy": record(copy)})
    write(output / "source-before.json", bindings)
    contract = json.loads((frozen / "drained-static-contract.json").read_text())
    native_manifest = root / contract["fullTrial"] / "manifest.json"
    shutil.copyfile(native_manifest, output / "actual-failed-manifest.json")
    manifest = json.loads(native_manifest.read_text(encoding="utf-8-sig"))
    for key in ("height", "baseHeight", "crestLength", "domainWidth", "unitWeightNPerM3"):
        assert manifest["config"][key] == contract[key]
    assert manifest["config"]["slope"] == contract["slopeDegrees"]
    assert manifest["config"]["drainedCohesionPa"] == contract["cohesionPa"]
    assert manifest["config"]["drainedFrictionDeg"] == contract["frictionDegrees"]
    spec = importlib.util.spec_from_file_location("frozen_urmi_static", frozen / "slope_stability.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    toe = contract["crestLength"] + contract["height"] / math.tan(math.radians(contract["slopeDegrees"]))
    assert abs(toe - manifest["config"]["toeX"]) <= 1e-12
    profile = [[0., 14.], [12., 14.], [toe, 4.], [60., 4.]]
    rows, summaries = [], []
    for slices in contract["sliceCounts"]:
        rejected, accepted = Counter(), []
        for entry in np.linspace(*contract["entryRangeM"], contract["entryCount"]):
            for exit in np.linspace(contract["exitStartM"], toe + contract["exitEndBeyondToeM"], contract["exitCount"]):
                for rho in np.linspace(*contract["rhoRange"], contract["rhoCount"]):
                    item = {"entry": float(entry), "exit": float(exit), "rho": float(rho), "slices": slices}
                    try:
                        data = module.make_slices(module.Circle(entry, exit, rho), profile, contract["baseY"], slices, contract["unitWeightNPerM3"])
                        result = module.solve_bishop(data, contract["cohesionPa"], math.tan(math.radians(contract["frictionDegrees"])))
                        item.update(status="FORMAL_ROOT", geometry=data.geometry, result=result)
                        accepted.append(item)
                    except module.RejectedCircle as error:
                        item.update(status="REJECTED", reason=str(error))
                        rejected[str(error)] += 1
                    rows.append(item)
        nonnegative = [r for r in accepted if r["result"]["normalForcesNonnegative"]]
        minimum = lambda candidates: min(candidates, key=lambda r: r["result"]["formalFactor"]) if candidates else None
        summaries.append({"slices": slices, "attempted": 9 * 17 * 13, "formalRoots": len(accepted), "rejections": dict(rejected),
                          "negativeNormalCandidates": sum(not r["result"]["normalForcesNonnegative"] for r in accepted),
                          "minimumAllFormal": minimum(accepted), "minimumNonnegativeNormalSubset": minimum(nonnegative),
                          "minimumRawNormalStressPa": min((r["result"]["minimumNormalStressPa"] for r in accepted), default=None)})
    write(output / "all-candidates.json", rows)
    after = [{"source": record(Path(r["source"]["path"])), "copy": record(Path(r["copy"]["path"]))} for r in bindings]
    assert after == bindings
    write(output / "source-after.json", after)
    write(output / "summary.json", {"scope": contract["scope"], "profile": profile, "sourceBinding": bindings,
          "actualManifest": record(output / "actual-failed-manifest.json"), "summaries": summaries,
          "mpmUpdates": 0, "materialCalls": 0, "physicalAdmissibility": False, "scientificallyValidated": False,
          "automaticNextRunAuthorized": False, "normalPolicy": contract["normalPolicy"], "decisionLimit": contract["decisionLimit"]})
    print(json.dumps({"attempts": len(rows), "summaries": summaries}))


if __name__ == "__main__":
    main()
