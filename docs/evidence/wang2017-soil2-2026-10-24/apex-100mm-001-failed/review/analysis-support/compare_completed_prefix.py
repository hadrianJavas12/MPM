"""Exact saved-settlement comparison, using unchanged canonical pointwise metric.

Saved data only. Numerical prefix consistency is not scientific validation.
"""
from pathlib import Path
from decimal import Decimal
import csv
import json
import numpy as np
from native_saved_io import vtk, sha
from canonical_prefix_metric import metric

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "output/wang2017-soil2-2026-10-24/apex-100mm-001"
BASE = RUN.with_name("apex-fast-010-001")
OUT = RUN.with_name(RUN.name + "-review")
ATOL, RTOL, TIME_ATOL = 1e-8, 1e-7, 1e-10


def table(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        key = Decimal(row["commanded_settlement_m"].lower().replace("d", "e"))
        assert key not in result
        result[key] = {name: float(value.lower().replace("d", "e")) for name, value in row.items()}
    return result


def main():
    current, baseline = table(RUN / "force-displacement.csv"), table(BASE / "force-displacement.csv")
    common = sorted(set(current) & set(baseline))
    assert len(common) == 61 and common[0] == 0 and common[-1] == Decimal(".06")
    arrays = {}; hashes = []
    for command in common:
        c, b = current[command], baseline[command]
        cp = RUN / "vtk" / f"particles_{int(c['frame']):04d}.vtk"
        bp = BASE / "vtk" / f"particles_{int(b['frame']):04d}.vtk"
        cx, cf = vtk(cp); bx, bf = vtk(bp)
        assert np.array_equal(cf["unique-id"], bf["unique-id"])
        assert set(cf) == set(bf)
        for name, ca, ba in [("positions_m", cx, bx)] + [("vtk:" + name, cf[name], bf[name]) for name in sorted(cf)]:
            pair = arrays.setdefault(name, [[], []]); pair[0].append(ba); pair[1].append(ca)
        for name in sorted(c):
            pair = arrays.setdefault("force_csv:" + name, [[], []]); pair[0].append([b[name]]); pair[1].append([c[name]])
        hashes.extend([{"path":str(p.relative_to(ROOT)), "sha256":sha(p)} for p in (bp, cp)])
    metrics = {name:metric(np.asarray(pair[0]), np.asarray(pair[1]), ATOL, RTOL) for name, pair in arrays.items()}
    time_difference = max(abs(current[k]["time_s"] - baseline[k]["time_s"]) for k in common)
    time_pass = time_difference <= TIME_ATOL
    failed = {name:value for name,value in metrics.items() if not value["pass"]}
    # Exported boolean history/branch flags can differ on roundoff-scale transactions;
    # they remain included in strict comparison rather than silently excluded.
    result = {"scope":"Saved prefix numerical consistency only; not completed100mm, convergence or scientific validation",
              "baseline":str(BASE.relative_to(ROOT)), "current":str(RUN.relative_to(ROOT)),
              "alignment":"Exact Decimal saved commanded settlement; stable native unique IDs; no interpolation",
              "matchedStates":len(common), "commandRangeM":[float(common[0]),float(common[-1])],
              "tolerances":{"atol":ATOL,"rtol":RTOL,"timeAtol":TIME_ATOL,
                            "source":"scripts/compare-framework-runs.py unchanged defaults; baseline a in atol+rtol*abs(a)"},
              "maximumSavedTimeDifferenceS":time_difference,"savedTimePass":time_pass,
              "allCanonicalPointwiseMetricsPass":not failed and time_pass,
              "failedMetricNames":list(failed),"metrics":metrics,
              "scientificValidation":False,
              "sourceProof":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in
                             (ROOT/"scripts/compare-framework-runs.py",Path(__file__),Path(__file__).with_name("canonical_prefix_metric.py"))]}
    (OUT/"completed-prefix-comparison.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    hashes.extend({"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in (RUN/"force-displacement.csv",BASE/"force-displacement.csv"))
    (OUT/"completed-prefix-input-hashes.json").write_text(json.dumps(hashes,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"matchedStates":len(common),"allPass":not failed and time_pass,"failedMetrics":failed,
                      "positionMetric":metrics["positions_m"],"reactionMetric":metrics["force_csv:reaction_upward_N_per_m"]},indent=2))


if __name__ == "__main__":
    main()
