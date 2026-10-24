"""Add residual-strength/contact/prefix context and correct generic loader J label.

Run after review_interrupted_100mm.py and compare_completed_prefix.py. Does not
recompute the solver or change saved bytes or comparison thresholds.
"""
from pathlib import Path
import json
import numpy as np
from native_saved_io import vtk,rows,sha

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/apex-100mm-001"
BASE=RUN.with_name("apex-fast-010-001")
OUT=RUN.with_name(RUN.name+"-review")
review_path=OUT/"interrupted-100mm-physical-review.json"
review=json.loads(review_path.read_text())
prefix=json.loads((OUT/"completed-prefix-comparison.json").read_text())
force=rows(RUN/"force-displacement.csv")
contacts=rows(RUN/"wang2017-contact-history.csv")
contact_ids=np.unique([r["particle_id"] for r in contacts])
original,original_fields=vtk(RUN/"vtk/gravity_initial.vtk")
ids=original_fields["unique-id"]
free=(original[:,1]>5)&~np.isin(ids,contact_ids)
strength=[];flag_cases=[];stress_failures=[];latest=None
for frame in range(91):
    points,fields=vtk(RUN/"vtk"/f"particles_{frame:04d}.vtk")
    assert np.array_equal(ids,fields["unique-id"])
    residual=fields["wang-paper-kps"]>=.02
    assert np.all(fields["wang-cohesion-pa"][residual]==15000)
    strength.append({"frame":frame,"timeS":force[frame]["time_s"],"residualStrengthParticles":int(residual.sum()),
                     "residualStrengthFreeParticles":int((residual&free).sum()),
                     "maxPaperKps":float(fields["wang-paper-kps"].max()),
                     "minCohesionPa":float(fields["wang-cohesion-pa"].min())})
    if frame<=60:
        bp,bf=vtk(BASE/"vtk"/f"particles_{frame:04d}.vtk")
        mismatch=fields["wang-history-decrease-accepted"]!=bf["wang-history-decrease-accepted"]
        for j in np.flatnonzero(mismatch):
            flag_cases.append({"frame":frame,"nativeId":int(ids[j]),
                               "currentAcceptedHistoryDecrease":float(fields["wang-history-decrease-accepted"][j]),
                               "baselineAcceptedHistoryDecrease":float(bf["wang-history-decrease-accepted"][j]),
                               "currentLastStepPaperKpsChange":float(fields["wang-paper-kps"][j]-fields["wang-previous-paper-kps"][j]),
                               "baselineLastStepPaperKpsChange":float(bf["wang-paper-kps"][j]-bf["wang-previous-paper-kps"][j])})
        for name in ("mc-yield-residual-kirchhoff-pa","sig_xy"):
            delta=np.abs(fields[name]-bf[name]);tol=1e-8+1e-7*np.abs(bf[name])
            for j in np.flatnonzero(delta>tol):
                stress_failures.append({"field":name,"frame":frame,"nativeId":int(ids[j]),
                                        "baselineValuePa":float(bf[name][j]),"currentValuePa":float(fields[name][j]),
                                        "differencePa":float(delta[j]),"unchangedTolerancePa":float(tol[j])})
    latest=(points,fields,residual)
points,fields,residual=latest
gap=np.array([r["geometric_gap_m"] for r in contacts])
last_contacts=[r for r in contacts if r["frame"]==90]
spring_by_frame=[sum(r["geometric_spring_energy_J_per_m"] for r in contacts if r["frame"]==i) for i in range(91)]
energy=rows(RUN/"energy-history.csv")
supplement={"scope":"Additional saved-data observations only; no completion or scientific PASS",
            "residualStrength":{"law":"paper kps>=.02 gives cohesion15000Pa, without changing friction35deg",
                                "firstSavedResidualTimeS":next(r["timeS"] for r in strength if r["residualStrengthParticles"]),
                                "finalCount":int(residual.sum()),"finalFreeCount":int((residual&free).sum()),
                                "finalIds":ids[residual].astype(int).tolist(),
                                "finalOriginalPositionsM":original[residual].tolist(),"series":strength},
            "contact":{"savedRows":len(contacts),"geometricGapRangeM":[float(gap.min()),float(gap.max())],
                       "negativeGeometricGapRows":int((gap<0).sum()),
                       "lastGeometricGapRangeM":[min(r["geometric_gap_m"] for r in last_contacts),max(r["geometric_gap_m"] for r in last_contacts)],
                       "maxSavedGeometricSpringEnergyJPerM":max(spring_by_frame),
                       "lastGeometricSpringEnergyJPerM":spring_by_frame[-1],
                       "lastActuatorSignedCommandWorkJPerM":energy[-1]["actuator_signed_command_work_J_per_m"],
                       "caveat":"Gap uses saved particle top surface; native force uses predicted corner geometry. Spring and work proxies do not close energy. Individual actual corner tractions are not saved."},
            "prefixFailedMetricContext":{"canonicalPointwiseComparisonPass":prefix["allCanonicalPointwiseMetricsPass"],
                                          "failedMetricNames":prefix["failedMetricNames"],
                                          "stressFailureRows":stress_failures,
                                          "differingHistoryFlagRows":len(flag_cases),
                                          "maxAbsLastStepPaperKpsChangeAtDifferingFlags":max(abs(r[k]) for r in flag_cases for k in
                                             ("currentLastStepPaperKpsChange","baselineLastStepPaperKpsChange")),
                                          "differingHistoryFlags":flag_cases,
                                          "interpretation":"History flags differ at roundoff-scale last accepted increments. This does not remove the strict pointwise mismatch or validate the later unsaved transaction."}}
(OUT/"residual-contact-prefix-context.json").write_text(json.dumps(supplement,indent=2)+"\n",encoding="utf-8")
# The generic reused loader only sees volume and gravity F. This review ALSO
# independently read the complete loading F9 material CSV and checked det(F).
review["nativeSavedOutput"]["loadingDeterminantJ"]="DIRECTLY_RECONSTRUCTED_FROM_SAVED_MATERIAL_F9; see audit.actualJRange and storedJMinusDetF, independently checked against volume ratio"
review["apexActivation"]["samplingCaveat"]=review["apexActivation"]["samplingCaveat"].replace("all20500+ substeps/events","all30960 saved-endpoint accepted loading updates or later unsaved events")
review["canonicalCompleted60mmPrefix"]={"file":"completed-prefix-comparison.json","matchedStates":prefix["matchedStates"],
                                       "allCanonicalPointwiseMetricsPass":prefix["allCanonicalPointwiseMetricsPass"],
                                       "failedMetricNames":prefix["failedMetricNames"],"scientificValidation":False}
review["supplementFile"]="residual-contact-prefix-context.json"
review["finalization"]={"script":str(Path(__file__).relative_to(ROOT)),"sha256":sha(Path(__file__)),
                        "correction":"Generic volume-only loader J note replaced with this review's independently checked saved loading F9 evidence. No saved source/output changed."}
review_path.write_text(json.dumps(review,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"residualFirstS":supplement["residualStrength"]["firstSavedResidualTimeS"],
                  "residualCount":int(residual.sum()),"residualIds":ids[residual].astype(int).tolist(),
                  "contact":supplement["contact"],"maxFlagKpsIncrement":supplement["prefixFailedMetricContext"]["maxAbsLastStepPaperKpsChangeAtDifferingFlags"]},indent=2))
