"""Frozen-source dry Bishop family diagnostic. No MPM/ASDF/material execution."""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import shutil
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a fresh output directory")
    args.output.mkdir(parents=True)
    support = args.output / "analysis-support"
    support.mkdir()
    records = []
    for source in (Path(__file__), ROOT / "scripts/analysis/slope_stability.py", args.contract):
        payload = source.read_bytes()
        destination = support / source.name
        shutil.copyfile(source, destination)
        if destination.read_bytes() != payload:
            raise RuntimeError("Pre-execution source copy mismatch")
        records.append({"path": str(destination), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)})
    write_json(args.output / "analysis-pre-execution.json", {"sources": records, "numericalSearchStarted": False})
    # Execute the copied backend, never a later mutable workspace version.
    spec = importlib.util.spec_from_file_location("frozen_slope_stability", support / "slope_stability.py")
    backend = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = backend
    spec.loader.exec_module(backend)
    Circle, RejectedCircle = backend.Circle, backend.RejectedCircle
    make_slices, solve_bishop = backend.make_slices, backend.solve_bishop
    contract = json.loads((support / args.contract.name).read_text(encoding="utf-8-sig"))
    if contract["schema"] != "cl-mpm.static-diagnostic.v1":
        raise ValueError("Unsupported static contract")
    family, material, numerics = contract["circleFamily"], contract["material"], contract["numerics"]
    if family["rhoSpacing"] != "geometric" or family["entryExitSpacing"] != "linear":
        raise ValueError("This preregistered family requires geometric rho and linear endpoint spacing")
    rows, summaries = [], []
    for search in contract["searches"]:
        grids = [np.linspace(*family["entryXM"], search["entryCount"]),
                 np.linspace(*family["exitXM"], search["exitCount"]),
                 np.geomspace(*family["rho"], search["rhoCount"])]
        group = []
        for entry, exit, rho in itertools.product(*grids):
            seed = {"search": search["name"], "slices": search["slices"], "entry": float(entry), "exit": float(exit), "rho": float(rho)}
            try:
                slices = make_slices(Circle(entry, exit, rho), contract["surfaceXYM"], contract["baseYM"],
                                     search["slices"], material["unitWeightNPerM3"], numerics["geometryRoundoffM"])
                geometry_error = None
            except RejectedCircle as error:
                geometry_error = str(error)
            for srf in contract["strengthReductionFactors"]:
                row = {**seed, "strengthReductionFactor": srf, "status": "REJECTED", "reason": geometry_error}
                if geometry_error is None:
                    try:
                        result = solve_bishop(slices, material["cohesionPa"] / srf,
                                              math.tan(math.radians(material["frictionDeg"])) / srf,
                                              numerics["factorAbsoluteTolerance"], numerics["maximumBisections"])
                        row.update(slices.geometry, **result, status="FORMAL_ROOT", reason="")
                    except RejectedCircle as error:
                        row["reason"] = str(error)
                rows.append(row)
                group.append(row)
        for srf in contract["strengthReductionFactors"]:
            selected = [r for r in group if r["strengthReductionFactor"] == srf]
            roots = [r for r in selected if r["status"] == "FORMAL_ROOT"]
            minimum = min(roots, key=lambda r: r["formalFactor"]) if roots else None
            boundary = {k: bool(minimum and minimum[k] in family[bound]) for k, bound in
                        (("entry", "entryXM"), ("exit", "exitXM"), ("rho", "rho"))}
            summaries.append({"search": search, "strengthReductionFactor": srf, "candidateCount": len(selected),
                              "formalRoots": len(roots), "rejectionReasons": dict(Counter(r["reason"] for r in selected if r["status"] != "FORMAL_ROOT")),
                              "restrictedFamilyMinimum": minimum, "minimumOnSearchBoundary": boundary})
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with (args.output / "candidates.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    write_json(args.output / "result.json", {"schema": "cl-mpm.static-diagnostic.result.v1", "status": "FORMAL_DIAGNOSTIC_COMPLETED",
               "summaries": summaries, "globalFactorOfSafetyCertified": False, "physicalAdmissibility": False,
               "mpmValidation": False, "scientificallyValidated": False, "mpmStepsExecuted": 0,
               "negativeNormals": "Retained without clamping or tension-crack assumption; see all candidate counts/minimum stresses",
               "limits": "Restricted circular family and midpoint slice quadrature; simplified Bishop does not enforce all force equilibrium; no dynamic landslide/runout validation"})
    for row in records:
        if hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise RuntimeError("Frozen analysis source changed")
    print(json.dumps({"output": str(args.output), "candidates": len(rows), "globalFactorOfSafetyCertified": False}))


if __name__ == "__main__":
    main()
