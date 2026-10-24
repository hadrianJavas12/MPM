"""Saved-state boundary/stress diagnosis; inferred signatures are not failure attribution."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from native_saved_io import vtk,rows,sha
from review_failed_soil2 import numeric_csv

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/fast-010-001"
OUT=RUN.with_name(RUN.name+"-review")


def main():
    mh,material=numeric_csv(RUN/"wang2017-material-history.csv")
    ch,contacts=numeric_csv(RUN/"wang2017-contact-history.csv")
    force,energy=rows(RUN/"force-displacement.csv"),rows(RUN/"energy-history.csv")
    manifest=json.loads((RUN/"manifest.json").read_text())
    config=manifest["config"]
    E,nu=config["E"],config["nu"]
    twoG=E/(1+nu);lam=E*nu/((1+nu)*(1-2*nu))
    original,of=vtk(RUN/"vtk/gravity_initial.vtk")
    slope=np.tan(np.deg2rad(config["slope"]))
    surface=config["baseHeight"]+np.maximum(0,config["height"]-slope*np.maximum(original[:,0]-config["crestLength"],0))
    inclined=(original[:,0]>config["crestLength"])&(original[:,0]<config["crestLength"]+config["height"]/slope)
    surface_distance=(surface-original[:,1])/np.where(inclined,np.sqrt(1+slope*slope),1)
    strip_ids=np.unique(contacts[:,ch["particle_id"]])
    strip=np.isin(of["unique-id"],strip_ids)
    distance_to_strip=np.sqrt(np.sum((original[:,None,:]-original[strip][None,:,:])**2,axis=2)).min(axis=1)
    history=[];stress_history=[]
    max_inplane_consistency=max_plane_ep_identity=max_reconstructed_yield_error=0.0
    min_geometric_gap=float(contacts[:,ch["geometric_gap_m"]].min())
    max_geometric_gap=float(contacts[:,ch["geometric_gap_m"]].max())
    negative_gap_count=int((contacts[:,ch["geometric_gap_m"]]<0).sum())
    source_snapshots={}
    for frame,row in enumerate(force):
        cr=contacts[contacts[:,ch["frame"]]==frame]
        gap=cr[:,ch["geometric_gap_m"]]
        stiffness=cr[:,ch["spring_stiffness_N_per_m2"]]
        nominal_soil_y=-stiffness*gap
        history.append({"frame":frame,"timeS":row["time_s"],"commandedSettlementM":row["commanded_settlement_m"],
                        "negativeSavedGeometricGapCount":int((gap<0).sum()),
                        "minSavedGeometricGapM":float(gap.min()),"maxSavedGeometricGapM":float(gap.max()),
                        "nominalGeometricSoilForceYSumNPerM":float(nominal_soil_y.sum()),
                        "nominalGeometricUpwardSoilForceSumNPerM":float(nominal_soil_y[nominal_soil_y>0].sum()),
                        "nativeActualTotalSoilForceYNPerM":row["soil_force_y_N_per_m"],
                        "nativeActualReactionUpNPerM":row["reaction_upward_N_per_m"],
                        "geometricSpringEnergyJPerM":float((.5*stiffness*gap*gap).sum()),
                        "nativeSignedActuatorCommandWorkJPerM":energy[frame]["actuator_signed_command_work_J_per_m"]})
        points,fields=vtk(RUN/"vtk"/f"particles_{frame:04d}.vtk")
        mr=material[material[:,mh["frame"]]==frame]
        mr=mr[np.argsort(mr[:,mh["particle_id"]])]
        j=fields["wang-det-f"]
        lt_x=j*fields["sig_xx"]-twoG*fields["eps_xx"]
        lt_y=j*fields["sig_yy"]-twoG*fields["eps_yy"]
        lt=.5*(lt_x+lt_y)
        epszz=lt/lam-fields["eps_xx"]-fields["eps_yy"]
        tauzz=lt+twoG*epszz
        mean=(j*fields["sig_xx"]+j*fields["sig_yy"]+tauzz)/3
        max_inplane_consistency=max(max_inplane_consistency,float(np.abs(lt_x-lt_y).max()))
        max_plane_ep_identity=max(max_plane_ep_identity,float(np.abs(epszz+mr[:,mh["wang-Ep-zz"]]).max()))
        tau=np.zeros((len(points),3,3))
        tau[:,0,0]=j*fields["sig_xx"];tau[:,1,1]=j*fields["sig_yy"];tau[:,2,2]=tauzz
        tau[:,0,1]=j*fields["sig_xy"];tau[:,1,0]=tau[:,0,1]
        principal=np.linalg.eigvalsh(tau)
        phi=fields["mc-friction-rad"];c=fields["wang-cohesion-pa"]
        yield_res=(1+np.sin(phi))*principal[:,-1]-(1-np.sin(phi))*principal[:,0]-2*j*c*np.cos(phi)
        max_reconstructed_yield_error=max(max_reconstructed_yield_error,float(np.abs(yield_res-fields["mc-yield-residual-kirchhoff-pa"]).max()))
        positive=mean>1e-6
        stress_history.append({"frame":frame,"timeS":row["time_s"],"maxReconstructedMeanKirchhoffPa":float(mean.max()),
                               "positiveMeanCountAbove1eMinus6Pa":int(positive.sum()),
                               "positiveMeanDrivenContactCount":int((positive&strip).sum()),
                               "positiveMeanWithin1mOriginalFreeSurfaceCount":int((positive&(surface_distance<=1)).sum()),
                               "positiveMeanWithin1mDrivenCentreCount":int((positive&(distance_to_strip<=1)).sum())})
        if frame in (0,len(force)-1):
            source_snapshots[frame]=(points,fields,mr,mean)
    points,fields,mr,mean=source_snapshots[len(force)-1]
    cap=json.loads((RUN/"mc-integration-failure.json").read_text())
    ep=mr[:,[mh["wang-Ep-"+s] for s in ("xx","yy","zz","yz","zx","xy")]]
    old=np.asarray(cap["committedPlasticTensor"])
    difference=ep-old
    distance=np.sqrt(np.sum(difference[:,:3]**2,axis=1)+2*np.sum(difference[:,3:]**2,axis=1))
    nearest=[]
    for index in np.argsort(distance)[:10]:
        nearest.append({"nativeId":int(fields["unique-id"][index]),"lastSavedPositionM":points[index].tolist(),
                        "originalPositionM":original[index].tolist(),"plasticTensorFrobeniusDistance":float(distance[index]),
                        "lastSavedActualJMinusFailureTrialJ":float(fields["wang-det-f"][index]-cap["deformationJacobian"]),
                        "lastSavedReconstructedMeanKirchhoffPa":float(mean[index]),"drivenContact":bool(strip[index]),
                        "originalNormalDistanceToFreeSurfaceM":float(surface_distance[index]),
                        "originalDistanceToNearestDrivenCentreM":float(distance_to_strip[index])})
    positive=mean>1e-6
    output={"scope":"Saved-state diagnosis, not direct failure-particle identification or an admissible constitutive remedy. No replay/solver invoked.",
            "scientificValidation":False,"signedGapInterpretation":"geometric_gap=commanded_descent−actual_top_descent. Nominal geometric soil force=-epsilon*width*gap; positive force would pull soil upward. Native assembler uses predicted-corner increment, so these nominal individual forces are not the saved actual assembled per-contact tractions.",
            "savedContactRows":len(contacts),"negativeSavedGeometricGapCount":negative_gap_count,
            "savedGeometricGapRangeM":[min_geometric_gap,max_geometric_gap],"contactHistory":history,
            "unsavedContactTraction":"NOT_AVAILABLE: no statement that every unsaved substep/contact traction was compression-only",
            "boundaryConclusion":"No saved geometric spring is tensile and all saved total actual strip forces are downward/zero. A compression-only platen would change the declared boundary problem; saved evidence does not demonstrate persistent tensile strip force that it would simply remove. It cannot be claimed to cure the constitutive no-solution state.",
            "stressReconstruction":{"method":"For documented native isotropic Kirchhoff elasticity tau=lambda*tr(eps_el)*I+2G*eps_el and plane-shear symmetry: L=mean(tau_xx−2G eps_xx,tau_yy−2G eps_yy); eps_zz=L/lambda−eps_xx−eps_yy; tau_zz=L+2G eps_zz. Mean tau then uses all3 normal components.",
                "directExportLimitation":"VTK has sig_xx,sig_yy,sig_xy and eps_xx,eps_yy, not full sigma_zz/elastic_eps_zz. Reported3D mean is explicitly reconstructed; future direct stress/elastic-strain export would remove this inference.",
                "youngsModulusPa":E,"poissonRatio":nu,"lambdaPa":lam,"twoGPa":twoG,
                "maxInplaneElasticIdentityResidualPa":max_inplane_consistency,"maxInferredEpsZZPlusExportedEpZZ":max_plane_ep_identity,
                "maxReconstructedSixPlaneYieldResidualDifferencePa":max_reconstructed_yield_error,
                "positiveThresholdPa":1e-6,"thresholdScope":"Floating-point diagnostic cut, not a tensile material cap or scientific-validation criterion",
                "timeSeries":stress_history,"lastPositiveMeanParticleIds":fields["unique-id"][positive].astype(int).tolist(),
                "lastPositiveMeanOriginalBoundingBoxM":[original[positive].min(axis=0).tolist(),original[positive].max(axis=0).tolist()]},
            "failureSignatureInference":{"method":"Rank last-saved signed Ep by physical-tensor Frobenius distance to capsule committedEp; list actualJ differences separately. No weighted score or exact-ID attribution.",
                "reasonInferenceOnly":"212 updates separate last saved accepted update count19608 from failure-manifest19820; capsule carries no global particle ID or exact failure time. Other particles may evolve between frames.",
                "rankedCandidates":nearest},
            "nativeFailureReason":cap["reason"],"historyGuardFailure":"NOT_ESTABLISHED; capsule reason is no admissible signed-tensor solution",
            "commandWorkAndSpringEnergy":"These are different observations. Geometric saved spring energy is not exact assembled-contact work; neither proxy establishes closed energy balance or self-sustained sliding."}
    (OUT/"boundary-tension-review.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    fig,ax=plt.subplots(figsize=(11,6),constrained_layout=True)
    ax.scatter(points[:,0],points[:,1],color="lightgrey",s=12)
    dots=ax.scatter(points[positive,0],points[positive,1],c=mean[positive]/1000,cmap="magma",s=32,vmin=0)
    fig.colorbar(dots,ax=ax,label="Reconstructed positive mean Kirchhoff stress (kPa)")
    q=nearest[0]["lastSavedPositionM"]
    ax.scatter([q[0]],[q[1]],marker="x",c="cyan",s=90,label="Closest saved Ep signature; inferred ID")
    ax.plot([7,10],[15-force[-1]["commanded_settlement_m"]]*2,color="red",lw=3,label="Driven strip")
    ax.set(xlabel="x (m)",ylabel="y (m)",aspect="equal",xlim=(-.5,20.5),ylim=(-.5,15.5),
           title="Incomplete Soil2, last saved5.7s /57mm; actual coordinates, displacement scale1\nMean stress reconstructed from native isotropic elastic relation; failure ID/time not exported")
    ax.legend(loc="lower left",fontsize=8)
    fig.savefig(OUT/"boundary-tension-diagnosis.png",dpi=150)
    plt.close(fig)
    print(json.dumps({"negativeSavedGapCount":negative_gap_count,"lastContactObservation":history[-1],"lastStressObservation":stress_history[-1],
                      "reconstructionResidualPa":max_inplane_consistency,"yieldResidualDifferencePa":max_reconstructed_yield_error,
                      "closestInferredSavedSignature":nearest[0]},indent=2))


if __name__=="__main__":
    main()
