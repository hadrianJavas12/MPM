"""Read real saved Soil2 states/transactions; no solver, replay, interpolation or physics edits."""
from pathlib import Path
import csv
import json
import numpy as np
from native_saved_io import load, vtk, sha

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/fast-010-001"
CONTROL=ROOT/"output/wang2017-reference-2026-10-24/fast-010-001"
OUT=RUN.with_name(RUN.name+"-review")


def numeric_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.reader(stream)
        header=next(reader)
        values=np.array([[float(v.lower().replace("d","e")) for v in row] for row in reader])
    if values.ndim!=2 or values.shape[1]!=len(header) or not np.isfinite(values).all():
        raise ValueError("Nonfinite or malformed audit CSV")
    return {name:i for i,name in enumerate(header)},values


def main():
    current,control=load(RUN),load(CONTROL)
    manifest,force,energy,states=current[:4]
    status_path=RUN.with_name(RUN.name+"-status.json")
    status=json.loads(status_path.read_text(encoding="utf-8-sig"))
    assert status["nativeExitCode"]==1 and manifest["complete"] is False and manifest["status"]=="failed"
    count=len(states[0][0])
    mh,material=numeric_csv(RUN/"wang2017-material-history.csv")
    ch,contacts=numeric_csv(RUN/"wang2017-contact-history.csv")
    assert len(material)==len(states)*count and len(contacts)==len(states)*6
    ids=states[0][1]["unique-id"]
    material_frames=[]
    max_position_csv_vtk=max_field_csv_vtk=max_k_residual=max_j_residual=max_law_residual=0.0
    max_rotation_error=max_volume_j_error=max_surface_error=max_gap_error=max_spring_error=0.0
    min_j,min_volume_ratio,min_cohesion=float("inf"),float("inf"),float("inf")
    max_j,max_volume_ratio,max_cohesion=float("-inf"),float("-inf"),float("-inf")
    history_flags,smallest_last_step_k_change=0,float("inf")
    all_ep=[]
    all_k=[]
    for i,(points,fields) in enumerate(states):
        rows=material[material[:,mh["frame"]]==i]
        rows=rows[np.argsort(rows[:,mh["particle_id"]])]
        assert len(rows)==count and np.array_equal(rows[:,mh["particle_id"]],ids)
        assert np.max(np.abs(rows[:,mh["time_s"]]-force[i]["time_s"]))<1e-12
        xyz=rows[:,[mh[n] for n in ("x_m","y_m","z_m")]]
        max_position_csv_vtk=max(max_position_csv_vtk,float(np.abs(xyz-points).max()))
        for name,column in mh.items():
            if name in fields:
                max_field_csv_vtk=max(max_field_csv_vtk,float(np.abs(rows[:,column]-fields[name]).max()))
        F=rows[:,[mh[f"wang-F-{a}{b}"] for a in range(3) for b in range(3)]].reshape(-1,3,3)
        R=rows[:,[mh[f"wang-R-{a}{b}"] for a in range(3) for b in range(3)]].reshape(-1,3,3)
        j=np.linalg.det(F)
        vratio=rows[:,mh["volume_m3_per_m"]]/rows[:,mh["reference_volume_m3_per_m"]]
        assert (j>0).all() and (vratio>0).all()
        max_j_residual=max(max_j_residual,float(np.abs(j-rows[:,mh["wang-det-f"]]).max()))
        max_volume_j_error=max(max_volume_j_error,float(np.abs(j-vratio).max()))
        ep=rows[:,[mh[f"wang-Ep-{name}"] for name in ("xx","yy","zz","yz","zx","xy")]]
        dev=ep.copy();dev[:,:3]-=dev[:,:3].mean(axis=1)[:,None]
        k=np.sqrt(.5*(np.sum(dev[:,:3]**2,axis=1)+2*np.sum(dev[:,3:]**2,axis=1)))
        assert (k>=0).all()
        max_k_residual=max(max_k_residual,float(np.abs(k-rows[:,mh["wang-paper-kps"]]).max()))
        expected_c=np.where(k>=.02,15000,30000-750000*k)
        max_law_residual=max(max_law_residual,float(np.abs(expected_c-rows[:,mh["wang-cohesion-pa"]]).max()))
        max_rotation_error=max(max_rotation_error,float(np.abs(np.matmul(np.transpose(R,(0,2,1)),R)-np.eye(3)).max()),float(np.abs(np.linalg.det(R)-1).max()))
        min_j,max_j=min(min_j,float(j.min())),max(max_j,float(j.max()))
        min_volume_ratio,max_volume_ratio=min(min_volume_ratio,float(vratio.min())),max(max_volume_ratio,float(vratio.max()))
        c=rows[:,mh["wang-cohesion-pa"]]
        min_cohesion,max_cohesion=min(min_cohesion,float(c.min())),max(max_cohesion,float(c.max()))
        flags=rows[:,mh["wang-history-decrease-accepted"]]
        assert np.isin(flags,[0,1]).all()
        history_flags+=int(flags.sum())
        smallest_last_step_k_change=min(smallest_last_step_k_change,float((rows[:,mh["wang-paper-kps"]]-rows[:,mh["wang-previous-paper-kps"]]).min()))
        all_ep.append(ep);all_k.append(k);material_frames.append(rows)
        cr=contacts[contacts[:,ch["frame"]]==i]
        assert len(cr)==6 and len(np.unique(cr[:,ch["particle_id"]]))==6
        centre=cr[:,ch["loading_origin_centre_y_m"]]-cr[:,ch["centre_y_m"]]
        half=cr[:,ch["loading_origin_half_height_m"]]-cr[:,ch["half_height_m"]]
        surface=centre+half
        max_surface_error=max(max_surface_error,float(np.abs(surface-cr[:,ch["top_surface_descent_m"]]).max()),abs(float(np.average(surface,weights=cr[:,ch["overlap_width_m"]]))-force[i]["measured_settlement_m"]))
        gap=cr[:,ch["commanded_settlement_m"]]-surface
        max_gap_error=max(max_gap_error,float(np.abs(gap-cr[:,ch["geometric_gap_m"]]).max()),abs(float(np.abs(gap).max())-force[i]["max_gap_m"]))
        spring=.5*cr[:,ch["spring_stiffness_N_per_m2"]]*gap*gap
        max_spring_error=max(max_spring_error,float(np.abs(spring-cr[:,ch["geometric_spring_energy_J_per_m"]]).max()))
    assert max_position_csv_vtk<1e-12 and max_field_csv_vtk<1e-9
    assert max_j_residual<1e-12 and max_k_residual<1e-12 and max_law_residual<1e-8
    assert max_rotation_error<1e-10 and max_surface_error<1e-12 and max_gap_error<1e-12
    original,original_fields=vtk(RUN/"vtk/gravity_initial.vtk")
    p0,f0=states[0];last,fields=states[-1]
    strip_ids=np.unique(contacts[:,ch["particle_id"]])
    strip=np.isin(ids,strip_ids)
    free=(original[:,1]>manifest["config"]["baseHeight"])&~strip
    assert len(strip_ids)==6
    delta=last-p0
    velocity=np.column_stack((fields["vel_x"],fields["vel_y"],np.zeros(count)))
    speed=np.linalg.norm(velocity,axis=1);mass=fields["mass"]
    motion={}
    for name,mask in {"all":np.ones(count,dtype=bool),"aboveBaseExcludingSixDrivenContacts":free,"drivenContacts":strip,"baseOriginalYAtMost5m":original[:,1]<=5}.items():
        d,m,v=delta[mask],mass[mask],velocity[mask]
        mean=np.average(d,axis=0,weights=m);mean_v=np.average(v,axis=0,weights=m)
        rms=float(np.sqrt(np.average(np.sum(v*v,axis=1),weights=m)))
        motion[name]={"particleCount":int(mask.sum()),"massKgPerM":float(m.sum()),"centroidMotionM":mean.tolist(),
                      "maxMotionNormM":float(np.linalg.norm(d,axis=1).max()),"maxAbsHorizontalMotionM":float(np.abs(d[:,0]).max()),
                      "maxDownwardMotionM":float((-d[:,1]).max()),"meanVelocityMPerS":mean_v.tolist(),"rmsSpeedMPerS":rms,
                      "meanVelocityNormOverRmsSpeed":float(np.linalg.norm(mean_v)/rms) if rms else None,
                      "massFractionRightwardMotionGreater5mm":float(m[d[:,0]>.005].sum()/m.sum()),
                      "massFractionRightwardMotionGreater10mm":float(m[d[:,0]>.01].sum()/m.sum()),
                      "massFractionRightwardAndDownwardVelocity":float(m[(v[:,0]>0)&(v[:,1]<0)].sum()/m.sum())}
    fastest=int(speed.argmax());farthest=int(np.linalg.norm(delta,axis=1).argmax())
    karray=np.array(all_k);dk=karray[-1]-karray[0];top=np.argsort(dk)[-50:]
    toe=manifest["config"]["crestLength"]+manifest["config"]["height"]/np.tan(np.deg2rad(manifest["config"]["slope"]))
    series=[]
    for row,(points,values) in zip(force,states):
        mv=points-p0;vel=np.column_stack((values["vel_x"],values["vel_y"]))
        series.append({"timeS":row["time_s"],"commandedSettlementM":row["commanded_settlement_m"],"freeCentroidMotionM":np.average(mv[free],axis=0,weights=mass[free]).tolist(),
                       "freeRmsSpeedMPerS":float(np.sqrt(np.average(np.sum(vel[free]*vel[free],axis=1),weights=mass[free]))),
                       "freeFront95thXM":float(np.quantile(points[free,0],.95)),"reactionNPerM":row["reaction_upward_N_per_m"]})
    comparisons=[]
    for value in sorted(set(current[4])&set(control[4])):
        ci,oi=current[4].index(value),control[4].index(value)
        cp,cf=states[ci];op,of=control[3][oi]
        assert np.array_equal(cf["unique-id"],of["unique-id"])
        displacement_difference=(cp-p0)-(op-control[3][0][0])
        raw_difference=cp-op
        reaction_difference=force[ci]["reaction_upward_N_per_m"]-control[1][oi]["reaction_upward_N_per_m"]
        comparisons.append({"commandedSettlementM":float(value),"soil2Frame":ci,"soil1Frame":oi,
                            "soil2ReactionNPerM":force[ci]["reaction_upward_N_per_m"],"soil1ReactionNPerM":control[1][oi]["reaction_upward_N_per_m"],
                            "reactionDifferenceNPerM":reaction_difference,"reactionDifferenceOverAbsSoil1OrNull":reaction_difference/abs(control[1][oi]["reaction_upward_N_per_m"]) if control[1][oi]["reaction_upward_N_per_m"] else None,
                            "maxAbsolutePositionDistanceM":float(np.linalg.norm(raw_difference,axis=1).max()),
                            "maxLoadingDisplacementFieldDifferenceM":float(np.linalg.norm(displacement_difference,axis=1).max()),
                            "rmsLoadingDisplacementFieldDifferenceM":float(np.sqrt(np.mean(np.sum(displacement_difference**2,axis=1)))),
                            "soil2KineticJPerM":force[ci]["kinetic_energy_J_per_m"],"soil1KineticJPerM":control[1][oi]["kinetic_energy_J_per_m"],
                            "paperKpsMinusJ2History":"NOT_COMPARED: distinct invariants on different material models"})
    summary={
        "scope":"INCOMPLETE actual native Soil2 run, native exit1; saved-state consistency/observations only, not scientific validation or a completed landslide. No solver or capsule replay invoked.",
        "scientificValidation":False,"nativeExitCode":1,"nativeComplete":False,"sourceCommitAtLaunch":status["sourceCommitAtLaunch"],
        "lastSavedTimeS":force[-1]["time_s"],"lastSavedCommandedSettlementM":force[-1]["commanded_settlement_m"],
        "lastSavedLoadingUpdates":int(force[-1]["updates"]),"failureManifestLoadingUpdates":manifest["loadingUpdates"],
        "failureTime":"Later than last saved state; exact global failure time/displacement and particle ID are not present in the material capsule. Do not label5.7s/57mm as exact rejection time.",
        "nativeSavedOutput":current[6],
        "fullAuditIdentities":{"materialRows":len(material),"contactRows":len(contacts),"idsStable":True,"allAuditDataFinite":True,
           "actualJDetFRange":[min_j,max_j],"volumeOverReferenceVolumeRange":[min_volume_ratio,max_volume_ratio],
           "cohesionPaRange":[min_cohesion,max_cohesion],"maxStoredJMinusDetF":max_j_residual,
           "maxActualJMinusVolumeRatio":max_volume_j_error,"maxPaperInvariantResidual":max_k_residual,"maxSoil2CohesionLawResidualPa":max_law_residual,
           "maxProperRotationResidual":max_rotation_error,"maxMaterialCsvVtkPositionDifferenceM":max_position_csv_vtk,"maxMaterialCsvVtkCommonFieldDifference":max_field_csv_vtk,
           "maxSurfaceDescentIdentityResidualM":max_surface_error,"maxIndividualGapIdentityResidualM":max_gap_error,"maxGeometricSpringEnergyIdentityResidualJPerM":max_spring_error,
           "acceptedHistoryDecreaseFlagCount":history_flags,"smallestLastAcceptedStepKpsChange":smallest_last_step_k_change,
           "smallestSavedFrameKpsChange":float(np.diff(karray,axis=0).min()),
           "transportScope":"Last accepted-step polar rotations are proper at saved instants; sparse frames do not reconstruct every unsaved Ep transport/update. Independent material controls own path/objectivity verification."},
        "motionDefinition":"ID-aligned native centres relative to this run's settled loading-frame0; original above-base mask excludes all six driven contact IDs",
        "motion":motion,
        "fastestLastParticle":{"id":int(ids[fastest]),"positionM":last[fastest].tolist(),"velocityMPerS":velocity[fastest].tolist(),"speedMPerS":float(speed[fastest]),"drivenContact":bool(strip[fastest])},
        "largestLastCentreMotionParticle":{"id":int(ids[farthest]),"motionM":delta[farthest].tolist(),"normM":float(np.linalg.norm(delta[farthest])),"drivenContact":bool(strip[farthest])},
        "localization":{"paperKpsLastRange":[float(karray[-1].min()),float(karray[-1].max())],"paperKpsAtLoadingOriginRange":[float(karray[0].min()),float(karray[0].max())],
           "incrementGreater1eMinus8Count":int((dk>1e-8).sum()),"incrementGreater1eMinus3Count":int((dk>.001).sum()),
           "top50IncrementMassWeightedShare":float(np.sum(dk[top]*mass[top])/np.sum(dk*mass)),
           "top50IncrementOriginalBoundingBoxM":[original[top].min(axis=0).tolist(),original[top].max(axis=0).tolist()],
           "top50IncrementDrivenContacts":int(strip[top].sum()),"definition":"Signed paper tensor invariant, not damage; concentration alone is not a throughgoing shear-band or landslide proof"},
        "runout":{"originalToeXM":float(toe),"freeMassFractionBeyondOriginalToe":float(mass[free&(last[:,0]>toe)].sum()/mass[free].sum()),
                  "freeFront95thAdvanceFromSettledM":series[-1]["freeFront95thXM"]-series[0]["freeFront95thXM"],
                  "maxFreeXAtLoadingOriginM":float(p0[free,0].max()),"maxFreeXLastM":float(last[free,0].max()),"rightBoundaryXM":manifest["config"]["width"],
                  "definition":"Only particles originally above base and outside driven strip; stationary base particles do not count as run-out"},
        "motionReactionTimeSeries":series,
        "soil1Comparison":{"sameSavedCommandPairs":len(comparisons),"alignment":"Exact saved Decimal commanded settlement, native unique ID; no interpolation",
           "soil2SettleUpdates":manifest["settleUpdates"],"soil1SettleUpdates":control[0]["settleUpdates"],
           "initialMaxPositionDifferenceM":float(np.linalg.norm(p0-control[3][0][0],axis=1).max()),
           "initialGravityDifference":"Constitutive models evolve differently during the same initialization protocol; loading-displacement comparison subtracts each run's own settled origin",
           "states":comparisons,"curveAgreement":"No rate/mesh/dt convergence PASS or digitized paper curve agreement inferred"},
        "lastEnergyObservations":energy[-1],
        "energyCaveat":"Elastic/native-plastic proxies are not a closed budget. Geometric contact spring energy uses saved actual gap; the assembler uses predicted-corner gap, so this is not exact assembled contact work.",
        "landslide":"NOT_VERIFIED: driven settlement, plastic colour and isolated speed maxima are insufficient. No hold/post-driver observation was executed.",
        "scientificLimitations":["100x paper loading rate; not reference speed","Assumed10m relief; paper boundary/endpoint uncertainties retained","Fixed bottom and side rollers constrain possible failure/run-out","Local strain softening has no demonstrated mesh-objective failure width","Native run stopped on no-admissible-solution error; history-guard rejection is not established by saved outputs"],
    }
    (OUT/"failed-soil2-saved-review.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    extra=[RUN/n for n in ("wang2017-material-history.csv","wang2017-contact-history.csv","mc-integration-failure.json")]+[status_path]
    hashes={"analysisSources":{p.name:sha(p) for p in Path(__file__).parent.glob("*.py")},"soil2Inputs":current[7],"soil1Inputs":control[7],
            "extraInputs":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in extra]}
    (OUT/"review-input-hashes.json").write_text(json.dumps(hashes,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"frames":len(states),"materialRows":len(material),"contactRows":len(contacts),"lastComparison":comparisons[-1],
                      "identities":summary["fullAuditIdentities"],"motion":motion,"fastest":summary["fastestLastParticle"],
                      "localization":summary["localization"],"runout":summary["runout"]},indent=2))


if __name__=="__main__":
    main()
