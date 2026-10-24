"""Actual interrupted100mm apex-model saved-data review; no solver/tests/replay."""
from pathlib import Path
from decimal import Decimal
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from native_saved_io import load,vtk,rows,sha

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/apex-100mm-001"
OUT=RUN.with_name(RUN.name+"-review")


def numeric_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        rd=csv.reader(stream);header=next(rd)
        data=np.asarray([[float(v.lower().replace("d","e")) for v in row] for row in rd])
    if data.ndim!=2 or data.shape[1]!=len(header) or not np.isfinite(data).all():
        raise ValueError("Malformed or nonfinite audit CSV")
    return {name:i for i,name in enumerate(header)},data


def reference(path):
    manifest=json.loads((path/"manifest.json").read_text())
    force=rows(path/"force-displacement.csv")
    with (path/"force-displacement.csv").open(encoding="utf-8-sig",newline="") as stream:
        commands=[Decimal(r["commanded_settlement_m"].lower().replace("d","e")) for r in csv.DictReader(stream)]
    return {"run":path,"manifest":manifest,"force":force,"commands":commands,
            "initial":vtk(path/"vtk/particles_0000.vtk"),"hashes":[]}


def compare(current,ref,free,mass):
    p0=current[3][0][0];ids=current[3][0][1]["unique-id"]
    output=[]
    for command in sorted(set(current[4])&set(ref["commands"])):
        ci,ri=current[4].index(command),ref["commands"].index(command)
        points,fields=current[3][ci]
        source=ref["run"]/"vtk"/f"particles_{int(ref['force'][ri]['frame']):04d}.vtk"
        rp,rf=vtk(source)
        assert np.array_equal(ids,rf["unique-id"])
        d=(points-p0)-(rp-ref["initial"][0])
        reaction=current[1][ci]["reaction_upward_N_per_m"]
        other=ref["force"][ri]["reaction_upward_N_per_m"]
        record={"commandedSettlementM":float(command),"currentFrame":ci,"referenceFrame":ri,
                "currentReactionNPerM":reaction,"referenceReactionNPerM":other,"reactionDifferenceNPerM":reaction-other,
                "reactionDifferenceOverAbsReferenceOrNull":(reaction-other)/abs(other) if other else None,
                "maxLoadingDisplacementFieldDifferenceM":float(np.linalg.norm(d,axis=1).max()),
                "rmsLoadingDisplacementFieldDifferenceM":float(np.sqrt(np.mean(np.sum(d*d,axis=1)))),
                "currentFreeCentroidMotionM":np.average((points-p0)[free],axis=0,weights=mass[free]).tolist(),
                "referenceFreeCentroidMotionM":np.average((rp-ref["initial"][0])[free],axis=0,weights=mass[free]).tolist()}
        if "wang-paper-kps" in rf:
            record["maxAbsPaperKpsDifference"]=float(np.abs(fields["wang-paper-kps"]-rf["wang-paper-kps"]).max())
            record["maxAbsCohesionDifferencePa"]=float(np.abs(fields["wang-cohesion-pa"]-rf["wang-cohesion-pa"]).max())
        else:
            record["historyComparison"]="Native Soil1 J2 and Soil2 paper tensor norm are different quantities; not subtracted"
        ref["hashes"].append({"path":str(source.relative_to(ROOT)),"sha256":sha(source)})
        output.append(record)
    return {"scope":"Exact recorded Decimal commanded settlements and native ID alignment, no interpolation or convergence PASS",
            "matchedSavedStates":len(output),"states":output,
            "initialMaxPositionDifferenceM":float(np.linalg.norm(p0-ref["initial"][0],axis=1).max()),
            "referenceNativeComplete":ref["manifest"]["complete"]}


def main():
    current=load(RUN)
    manifest,force,energy,states=current[:4]
    status_path=RUN.with_name(RUN.name+"-status.json")
    status=json.loads(status_path.read_text(encoding="utf-8-sig"))
    assert status["nativeExitCode"]==1 and manifest["complete"] is False
    assert len(states)==91 and force[-1]["time_s"]==9 and force[-1]["commanded_settlement_m"]==.09
    mh,material=numeric_csv(RUN/"wang2017-material-history.csv")
    ch,contacts=numeric_csv(RUN/"wang2017-contact-history.csv")
    p0,f0=states[0];ids=f0["unique-id"];count=len(ids)
    assert count==915 and len(material)==91*915 and len(contacts)==91*6
    original,original_fields=vtk(RUN/"vtk/gravity_initial.vtk")
    assert np.array_equal(original_fields["unique-id"],ids)
    strip_ids=np.unique(contacts[:,ch["particle_id"]]);assert len(strip_ids)==6
    strip=np.isin(ids,strip_ids);free=(original[:,1]>5)&~strip
    mass=f0["mass"]
    errors={key:0.0 for key in ("csvVtkPositionM","csvVtkCommonScalar","storedJMinusDetF","JMinusVolumeRatio","paperInvariant",
                               "cohesionLawPa","properRotation","epTraceMinusPlasticVolume","exportedEpTrace","contactSurfaceM","contactMaxGapM","springEnergyJPerM")}
    krange=[float("inf"),float("-inf")];jrange=krange.copy();crange=krange.copy();vrange=krange.copy()
    kframes=[];pvolframes=[];series=[];sampled_active_ids=set();flag_rows=0;decrease_flags=0;step_increment_max=0.0
    smallest_last_k_change=float("inf")
    for i,(points,fields) in enumerate(states):
        mr=material[material[:,mh["frame"]]==i];mr=mr[np.argsort(mr[:,mh["particle_id"]])]
        assert len(mr)==count and np.array_equal(mr[:,mh["particle_id"]],ids)
        assert np.max(np.abs(mr[:,mh["time_s"]]-force[i]["time_s"]))<1e-12
        xyz=mr[:,[mh[x] for x in ("x_m","y_m","z_m")]]
        errors["csvVtkPositionM"]=max(errors["csvVtkPositionM"],float(np.abs(xyz-points).max()))
        for name,index in mh.items():
            if name in fields:errors["csvVtkCommonScalar"]=max(errors["csvVtkCommonScalar"],float(np.abs(mr[:,index]-fields[name]).max()))
        F=mr[:,[mh[f"wang-F-{a}{b}"] for a in range(3) for b in range(3)]].reshape(-1,3,3)
        R=mr[:,[mh[f"wang-R-{a}{b}"] for a in range(3) for b in range(3)]].reshape(-1,3,3)
        J=np.linalg.det(F);assert (J>0).all()
        ep=mr[:,[mh["wang-Ep-"+s] for s in ("xx","yy","zz","yz","zx","xy")]]
        dev=ep.copy();dev[:,:3]-=dev[:,:3].mean(axis=1)[:,None]
        k=np.sqrt(.5*(np.sum(dev[:,:3]**2,axis=1)+2*np.sum(dev[:,3:]**2,axis=1)))
        cohesion=mr[:,mh["wang-cohesion-pa"]]
        volume_ratio=mr[:,mh["volume_m3_per_m"]]/mr[:,mh["reference_volume_m3_per_m"]]
        plastic_volume=mr[:,mh["wang-plastic-volume"]]
        trace=np.sum(ep[:,:3],axis=1)
        errors["storedJMinusDetF"]=max(errors["storedJMinusDetF"],float(np.abs(J-mr[:,mh["wang-det-f"]]).max()))
        errors["JMinusVolumeRatio"]=max(errors["JMinusVolumeRatio"],float(np.abs(J-volume_ratio).max()))
        errors["paperInvariant"]=max(errors["paperInvariant"],float(np.abs(k-mr[:,mh["wang-paper-kps"]]).max()))
        errors["cohesionLawPa"]=max(errors["cohesionLawPa"],float(np.abs(cohesion-np.where(k>=.02,15000,30000-750000*k)).max()))
        errors["properRotation"]=max(errors["properRotation"],float(np.abs(np.matmul(np.transpose(R,(0,2,1)),R)-np.eye(3)).max()),float(np.abs(np.linalg.det(R)-1).max()))
        errors["epTraceMinusPlasticVolume"]=max(errors["epTraceMinusPlasticVolume"],float(np.abs(trace-plastic_volume).max()))
        errors["exportedEpTrace"]=max(errors["exportedEpTrace"],float(np.abs(trace-mr[:,mh["wang-Ep-trace"]]).max()))
        active=mr[:,mh["wang-apex-active"]]
        assert np.isin(active,[0,1]).all()
        flag_rows+=int(active.sum());sampled_active_ids.update(ids[active==1].astype(int).tolist())
        decrease_flags+=int(mr[:,mh["wang-history-decrease-accepted"]].sum())
        smallest_last_k_change=min(smallest_last_k_change,float((mr[:,mh["wang-paper-kps"]]-mr[:,mh["wang-previous-paper-kps"]]).min()))
        step_increment_max=max(step_increment_max,float(np.abs(mr[:,mh["wang-plastic-volume-increment"]]).max()))
        for values,limits in ((k,krange),(J,jrange),(cohesion,crange),(plastic_volume,vrange)):
            limits[0]=min(limits[0],float(values.min()));limits[1]=max(limits[1],float(values.max()))
        kframes.append(k);pvolframes.append(plastic_volume)
        ct=contacts[contacts[:,ch["frame"]]==i];assert len(ct)==6 and len(np.unique(ct[:,ch["particle_id"]]))==6
        surface=(ct[:,ch["loading_origin_centre_y_m"]]-ct[:,ch["centre_y_m"]])+(ct[:,ch["loading_origin_half_height_m"]]-ct[:,ch["half_height_m"]])
        gap=ct[:,ch["commanded_settlement_m"]]-surface
        errors["contactSurfaceM"]=max(errors["contactSurfaceM"],float(np.abs(surface-ct[:,ch["top_surface_descent_m"]]).max()),abs(float(np.average(surface,weights=ct[:,ch["overlap_width_m"]]))-force[i]["measured_settlement_m"]))
        errors["contactMaxGapM"]=max(errors["contactMaxGapM"],abs(float(np.abs(gap).max())-force[i]["max_gap_m"]))
        errors["springEnergyJPerM"]=max(errors["springEnergyJPerM"],float(np.abs(.5*ct[:,ch["spring_stiffness_N_per_m2"]]*gap*gap-ct[:,ch["geometric_spring_energy_J_per_m"]]).max()))
        v=np.column_stack((fields["vel_x"],fields["vel_y"],np.zeros(count)))
        d=points-p0
        series.append({"frame":i,"timeS":force[i]["time_s"],"commandedSettlementM":force[i]["commanded_settlement_m"],
                       "reactionNPerM":force[i]["reaction_upward_N_per_m"],"freeCentroidMotionM":np.average(d[free],axis=0,weights=mass[free]).tolist(),
                       "freeMeanVelocityMPerS":np.average(v[free],axis=0,weights=mass[free]).tolist(),
                       "freeRmsSpeedMPerS":float(np.sqrt(np.average(np.sum(v[free]*v[free],axis=1),weights=mass[free]))),
                       "freeFront95thXM":float(np.quantile(points[free,0],.95)),"sampledApexActiveCount":int(active.sum()),
                       "maxAccumulatedPlasticVolumetricStrain":float(plastic_volume.max()),"geometricSpringEnergyJPerM":float((.5*ct[:,ch["spring_stiffness_N_per_m2"]]*gap*gap).sum())})
    assert errors["csvVtkPositionM"]<1e-12 and errors["csvVtkCommonScalar"]<1e-9
    assert errors["storedJMinusDetF"]<1e-12 and errors["paperInvariant"]<1e-12 and errors["cohesionLawPa"]<1e-8
    assert errors["properRotation"]<1e-10 and errors["epTraceMinusPlasticVolume"]<1e-12 and errors["exportedEpTrace"]<1e-12
    assert errors["contactSurfaceM"]<1e-12 and errors["contactMaxGapM"]<1e-12
    karray,pvarray=np.asarray(kframes),np.asarray(pvolframes)
    last,fields=states[-1];d=last-p0
    v=np.column_stack((fields["vel_x"],fields["vel_y"],np.zeros(count)));speed=np.linalg.norm(v,axis=1)
    motion={}
    for name,mask in {"all":np.ones(count,dtype=bool),"freeAboveBaseExcludingSixDriven":free,"sixDrivenContacts":strip,"baseOriginalYAtMost5m":original[:,1]<=5}.items():
        m=mass[mask];mean=np.average(d[mask],axis=0,weights=m);meanv=np.average(v[mask],axis=0,weights=m)
        rms=float(np.sqrt(np.average(np.sum(v[mask]**2,axis=1),weights=m)))
        motion[name]={"particleCount":int(mask.sum()),"massKgPerM":float(m.sum()),"centroidMotionM":mean.tolist(),"meanVelocityMPerS":meanv.tolist(),
                      "rmsSpeedMPerS":rms,"meanVelocityNormOverRmsSpeed":float(np.linalg.norm(meanv)/rms) if rms else None,
                      "maxMotionNormM":float(np.linalg.norm(d[mask],axis=1).max()),"maxAbsHorizontalMotionM":float(np.abs(d[mask,0]).max()),
                      "maxDownwardMotionM":float((-d[mask,1]).max()),"maxSpeedMPerS":float(speed[mask].max()),
                      "massFractionRightwardMotionGreater5mm":float(m[d[mask,0]>.005].sum()/m.sum()),
                      "massFractionRightwardMotionGreater10mm":float(m[d[mask,0]>.01].sum()/m.sum()),
                      "massFractionRightwardAndDownwardVelocity":float(m[(v[mask,0]>0)&(v[mask,1]<0)].sum()/m.sum())}
    fastest=int(speed.argmax());dk=karray[-1]-karray[0];top=np.argsort(dk)[-50:]
    toe=manifest["config"]["crestLength"]+manifest["config"]["height"]/np.tan(np.deg2rad(manifest["config"]["slope"]))
    strict=reference(ROOT/"output/wang2017-soil2-2026-10-24/apex-fast-010-001")
    soil1=reference(ROOT/"output/wang2017-reference-2026-10-24/fast-010-001")
    strict_comparison=compare(current,strict,free,mass);soil1_comparison=compare(current,soil1,free,mass)
    reactions=np.asarray([r["reaction_upward_N_per_m"] for r in force]);peak=int(reactions.argmax())
    substantial=(pvarray[-1]-pvarray[0])>1e-12
    final_volume_particles=[]
    for index in np.flatnonzero(substantial):
        final_volume_particles.append({"nativeId":int(ids[index]),"originalPositionM":original[index].tolist(),"lastPositionM":last[index].tolist(),
                                       "plasticVolumetricStrainAtLoadingOrigin":float(pvarray[0,index]),"lastPlasticVolumetricStrain":float(pvarray[-1,index]),
                                       "incrementOverSavedLoadingInterval":float(pvarray[-1,index]-pvarray[0,index]),"drivenContact":bool(strip[index])})
    active_frames=[r for r in series if r["sampledApexActiveCount"]]
    volume_frames=[r for r in series if r["maxAccumulatedPlasticVolumetricStrain"]>1e-12]
    summary={"scope":"INCOMPLETE declared volumetric-apex100mm target, native1; actual saved-state observations only. Media separately generated once from saved native states; no test, solver or replay.",
             "nativeComplete":False,"nativeExitCode":1,"sourceCommitAtLaunch":status["sourceCommitAtLaunch"],"scientificValidation":False,
             "lastSavedTimeS":9,"lastSavedCommandedSettlementM":.09,"lastSavedAcceptedUpdates":int(force[-1]["updates"]),"failureManifestLoadingUpdates":manifest["loadingUpdates"],"nativeSavedOutput":current[6],
             "audit":{"materialCsvRows":len(material),"contactCsvRows":len(contacts),"allReadFieldsFinite":True,"uniqueStableIds":True,
                      "actualJRange":jrange,"paperKpsRange":krange,"cohesionPaRange":crange,"plasticVolumetricStrainRange":vrange,
                      "identityResiduals":errors,"acceptedTinyHistoryDecreaseFlagRows":decrease_flags,"smallestLastStepKpsChange":smallest_last_k_change,
                      "smallestSavedKpsChange":float(np.diff(karray,axis=0).min())},
             "apexActivation":{"sampledLastAcceptedApexFlagRows":flag_rows,"sampledUniqueParticleIds":sorted(sampled_active_ids),
                               "firstSampledActiveTimeS":active_frames[0]["timeS"] if active_frames else None,
                               "firstSavedNonroundoffPlasticVolumeTimeS":volume_frames[0]["timeS"] if volume_frames else None,
                               "particlesWithLoadingPlasticVolumeIncreaseAbove1eMinus12":len(final_volume_particles),"particles":final_volume_particles,
                               "maximumAbsExportedTrialPlasticVolumeIncrement":step_increment_max,
                               "samplingCaveat":"Flags describe ONLY the last accepted return at a saved instant, not all20500+ substeps/events. Exported trial-volume increment is current minus committed and may be0 after each loadstep commit; use differences of accumulated totals across saved frames to observe interval volume change. Positive accumulated plastic volume is strain, not geometrical particle volume, porosity or exact multiplicative Fp determinant.",
                               "lastMassWeightedAverageAccumulatedPlasticVolumetricStrain":float(np.average(pvarray[-1],weights=mass))},
             "motionDefinition":"ID-aligned native particle-centre motion from this run's settled loading origin; original above-base selection excludes6 prescribed contacts",
             "motion":motion,"fastestFinalParticle":{"id":int(ids[fastest]),"positionM":last[fastest].tolist(),"velocityMPerS":v[fastest].tolist(),"speedMPerS":float(speed[fastest]),"drivenContact":bool(strip[fastest])},
             "runout":{"originalToeXM":float(toe),"freeMassFractionBeyondOriginalToe":float(mass[free&(last[:,0]>toe)].sum()/mass[free].sum()),
                       "freeFront95thAdvanceFromSettledM":series[-1]["freeFront95thXM"]-series[0]["freeFront95thXM"],"lastMaxFreeXM":float(last[free,0].max()),"rightBoundaryXM":20},
             "localization":{"paperKpsAtLoadingOriginMax":float(karray[0].max()),"lastPaperKpsMax":float(karray[-1].max()),
                             "incrementAbove1eMinus8Count":int((dk>1e-8).sum()),"incrementAbove1eMinus3Count":int((dk>.001).sum()),
                             "top50MassWeightedIncrementShare":float(np.sum(dk[top]*mass[top])/np.sum(dk*mass)),
                             "top50OriginalBoundingBoxM":[original[top].min(axis=0).tolist(),original[top].max(axis=0).tolist()],"top50DrivenContacts":int(strip[top].sum()),
                             "meaning":"Paper plastic tensor invariant and concentration, not damage or proof of a throughgoing slip surface"},
             "reaction":{"peakSavedReactionNPerM":float(reactions[peak]),"peakSavedTimeS":force[peak]["time_s"],"lastReactionNPerM":float(reactions[-1]),
                         "finalDropFromSavedPeakFraction":float((reactions[peak]-reactions[-1])/reactions[peak]),
                         "largestSingleSavedReactionDecreaseNPerM":float(np.minimum(np.diff(reactions),0).min()),
                         "interpretation":"Reaction is native total strip actuator response per unit thickness; completion/colour/apex activation alone does not imply peak failure or landslide"},
             "timeSeries":series,"comparisonCompleted60mmPrefix":strict_comparison,"comparisonSoil1":soil1_comparison,
             "lastEnergyObservations":energy[-1],"energyCaveat":"Current-volume Hencky/native-plastic proxies and geometric spring energy do not close energy balance or establish quasistatic response",
             "physicalVerdict":"NATIVE_FAILED_INCOMPLETE; COHERENT_LANDSLIDE_NOT_VERIFIED. Check free-mass motion and reaction/runout below; prescribed strip settlement and isolated high/upward velocities are insufficient.",
             "limits":["Original strict-history apex class retained; current stop is declared history-decrease scope rejection, not native completion or Wang validation","100x paper loading rate; no rate/mesh/dt convergence or laboratory calibration",
                       "10m relief assumed; boundary and endpoint uncertainty retained","Fixed bottom/side rollers and local-softening mesh dependence limit runout/mechanism interpretation","No post-driver hold/release was executed"]}
    (OUT/"interrupted-100mm-physical-review.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    sources={p.name:sha(p) for p in Path(__file__).parent.glob("*.py")}
    inputs={"analysisSources":sources,"currentNativeInputs":current[7],
            "currentExtraInputs":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in [RUN/"wang2017-material-history.csv",RUN/"wang2017-contact-history.csv",status_path]],
            "strictReferenceSnapshotHashes":strict["hashes"],"soil1ReferenceSnapshotHashes":soil1["hashes"]}
    (OUT/"review-input-hashes.json").write_text(json.dumps(inputs,indent=2)+"\n",encoding="utf-8")
    fig,axes=plt.subplots(1,3,figsize=(15,4.5),constrained_layout=True)
    command=np.array([r["commandedSettlementM"] for r in series])*1000;times=np.array([r["timeS"] for r in series])
    axes[0].plot(command,reactions/1000,label="Declared apex")
    axes[0].plot([r["commandedSettlementM"]*1000 for r in soil1_comparison["states"]],[r["referenceReactionNPerM"]/1000 for r in soil1_comparison["states"]],"--",label="Soil1")
    axes[0].plot([r["commandedSettlementM"]*1000 for r in strict_comparison["states"]],[r["referenceReactionNPerM"]/1000 for r in strict_comparison["states"]],":",label="Completed60mm reference")
    axes[0].set(xlabel="Actual commanded descent (mm)",ylabel="Reaction (kN/m)",title="Native reaction; observed peak/drop")
    axes[0].legend(fontsize=8)
    axes[1].plot(times,[r["freeCentroidMotionM"][0]*1000 for r in series],label="Free centroid rightward")
    axes[1].plot(times,[-r["freeCentroidMotionM"][1]*1000 for r in series],label="Free centroid downward")
    axes[1].set(xlabel="Actual native time (s)",ylabel="Motion from settled origin (mm)",title="509 above-base MPs;6 driven excluded")
    axes[1].legend(fontsize=8)
    axes[2].plot(times,[r["maxAccumulatedPlasticVolumetricStrain"] for r in series],color="purple",label="Maximum accumulated plastic volume strain")
    axes[2].set(xlabel="Actual native time (s)",ylabel="Plastic volumetric strain (1)",title="Actual added apex mode; sampled outputs")
    other=axes[2].twinx();other.step(times,[r["sampledApexActiveCount"] for r in series],where="mid",color="orange",label="Sampled apex-active MPs")
    other.set_ylabel("Last-return flag count at save")
    for axis in axes:axis.grid(alpha=.25)
    fig.suptitle("INCOMPLETE9s/90mm of10s/100mm target | actual saved data | no scientific landslide PASS",fontsize=12)
    fig.savefig(OUT/"physical-diagnostics.png",dpi=150);plt.close(fig)
    print(json.dumps({"frames":len(states),"audit":summary["audit"],"apexActivation":summary["apexActivation"],"freeMotion":motion["freeAboveBaseExcludingSixDriven"],
                      "reaction":summary["reaction"],"runout":summary["runout"],"fastestFinal":summary["fastestFinalParticle"],
                      "strictLastComparison":strict_comparison["states"][-1],"soil1LastComparison":soil1_comparison["states"][-1]},indent=2))


if __name__=="__main__":main()
