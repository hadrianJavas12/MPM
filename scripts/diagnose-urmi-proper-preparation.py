"""Saved-only diagnosis of a terminal proper trial before any material switch.
Never runs native MPM and never substitutes a successful equilibrium review.
"""
import argparse,csv,hashlib,importlib.util,json,math,shutil
from pathlib import Path
import numpy as np

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def record(p):
    return {"path":str(p.resolve()),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    a=argparse.ArgumentParser();a.add_argument("--run-dir",type=Path,required=True);a.add_argument("--output-dir",type=Path,required=True);args=a.parse_args()
    run=args.run_dir.resolve();out=args.output_dir.resolve();out.mkdir(exist_ok=False)
    shutil.copyfile(__file__,out/Path(__file__).name)
    frozen=run/"filled-review-001/analysis-source"
    for name in ("review-urmi-proper.py","review-urmi-damage40.py","plot_m5_cliff_comparison.py"):
        shutil.copyfile(frozen/name,out/name)
    observer=load_module(out/"review-urmi-proper.py","terminal_observer")
    helper=load_module(out/"review-urmi-damage40.py","terminal_helper")
    reader=load_module(out/"plot_m5_cliff_comparison.py","terminal_vtk")
    manifest=json.loads((run/"manifest.json").read_text(encoding="utf-8-sig"));cfg=manifest["config"]
    assert manifest["status"]=="failed" and manifest["savedFrames"]==0 and not manifest["equilibriumVerified"]
    assert manifest["phase"]=="drained-undamped-hold" and "undamped hold" in manifest["error"]
    shutil.copyfile(run/"preparation-history.csv",out/"preparation-history.csv")
    assert record(run/"preparation-history.csv")["sha256"]==record(out/"preparation-history.csv")["sha256"]
    with (out/"preparation-history.csv").open(newline="",encoding="utf-8-sig") as f:
        rows=[{k:float(v.lower().replace("d","e")) for k,v in r.items()} for r in csv.DictReader(f)]
    hold=[];fail=[];damped=[];prior=0.;passing=[]
    for i,r in enumerate(rows,1):
        assert all(math.isfinite(x) for x in r.values()) and r["updates"]==i and r["native_time_s"]>prior
        assert r["free_force_denominator2"]>0 and r["free_force_numerator2"]>=0 and r["free_nodal_mass"]>0
        rf=math.sqrt(r["free_force_numerator2"]/r["free_force_denominator2"])
        rk=r["free_KE"]/(r["free_nodal_mass"]*abs(cfg["gravity"])*cfg["height"])
        assert math.isclose(rf,r["RF"],rel_tol=1e-10,abs_tol=1e-14) and math.isclose(rk,r["RK"],rel_tol=1e-10,abs_tol=1e-14)
        ok=rf<cfg["forceTolerance"] and rk<cfg["kineticTolerance"] and r["native_time_s"]>=cfg["gravityRampDuration"]
        if r["damping"]>0:
            assert not hold and r["damping"]==.75
            passing=passing+[r] if ok else []
            damped=passing.copy()
        else:
            if not hold:hold_start=prior
            hold.append(r)
            if not ok:fail.append(r)
        prior=r["native_time_s"]
    assert len(rows)==manifest["preparationUpdates"] and len(fail)==1 and fail[0] is rows[-1]
    assert len(damped)>=cfg["consecutiveChecks"] and damped[-1]["native_time_s"]-damped[0]["native_time_s"]>=cfg["consecutiveDurationS"]
    assert hold[-1]["native_time_s"]-hold_start<cfg["undampedHoldDurationS"]
    assert fail[0]["RF"]>=cfg["forceTolerance"] and fail[0]["RK"]<cfg["kineticTolerance"]
    source=observer.source_proof(run);native=observer.constants(run);nodes,_=helper.reference_table(manifest["model"])
    data=run/"filled-review-001/saved-inputs"
    initial=next(helper.csv_frames(data/"preparation-material-state.csv"))[1]
    history=helper.history_rows(data/"preparation-states.csv")
    _,audit,_,_=observer.audit_frame(initial,history[0],data/"vtk/initial.vtk",None,None,0,manifest,native,nodes,helper,reader.read_cliff_vtk)
    report={"scope":"TERMINAL_FAILED_PREPARATION_ONLY_NO_DYNAMICS", "nativeError":manifest["error"],
        "nativeComplete":False,"equilibriumVerified":False,"dynamicFrames":0,"materialSwitchOccurred":False,
        "savedNormIdentityAudit":"PASS","initialStateIntegrity":"PASS","initialStateAudit":audit,"sourceProof":source,
        "preparationUpdates":len(rows),"nativeTimeS":prior,"dampedPassingChecks":len(damped),
        "dampedPassingDurationS":damped[-1]["native_time_s"]-damped[0]["native_time_s"],
        "undampedChecks":len(hold),"undampedDurationS":prior-hold_start,
        "forceLimit":cfg["forceTolerance"],"kineticLimit":cfg["kineticTolerance"],"actualFailure":fail[0],
        "forceExcessPercent":100*(fail[0]["RF"]/cfg["forceTolerance"]-1),
        "nativeSolverReruns":0,"dynamicMoviesAvailable":False,
        "limits":"Only initial particle field survived; final full particle tuple was not saved. RF crossing proves this protocol failed, not material/root failure, physical instability, or whether sliding would occur.",
        "bindings":[record(run/"manifest.json"),record(out/"preparation-history.csv")]+[record(x) for x in out.glob("*.py")]}
    (out/"diagnosis.json").write_text(json.dumps(report,indent=2)+"\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t=np.array([r["native_time_s"] for r in rows]);rf=np.array([r["RF"] for r in rows]);rk=np.array([r["RK"] for r in rows])
    fig,axes=plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
    axes[0].semilogy(t,rf,label="saved RF");axes[0].semilogy(t,np.maximum(rk,1e-18),label="saved RK")
    axes[0].axhline(cfg["forceTolerance"],ls="--",color="red",label="RF limit 1e-4")
    axes[0].axhline(cfg["kineticTolerance"],ls=":",color="gray",label="RK limit 1e-8");axes[0].legend(fontsize=8)
    axes[1].plot(t,rf);axes[1].axhline(cfg["forceTolerance"],ls="--",color="red");axes[1].set_xlim(hold_start-.1,prior+.01);axes[1].set_ylim(7.5e-5,1.025e-4)
    for ax in axes:ax.axvline(hold_start,color="orange",label="damping removed");ax.set_xlabel("native time (s)");ax.grid(alpha=.2)
    axes[0].set_title("Saved preparation norms; no dynamic stage")
    axes[1].set_title("Undamped hold stopped at first RF crossing")
    fig.savefig(out/"preparation-failure.png",dpi=140);plt.close(fig)
    print(json.dumps({k:report[k] for k in ("scope","preparationUpdates","nativeTimeS","undampedChecks","undampedDurationS","forceExcessPercent","dynamicFrames")}))
if __name__=="__main__":main()
