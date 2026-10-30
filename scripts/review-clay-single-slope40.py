"""Saved-only peak-initial residual-clay quarter-strength observer; no solver execution."""
import argparse,csv,hashlib,importlib.util,json,math,shutil,subprocess,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
SCOPE="SINGLE_CONSTANT40_CLAY_THREE_CHANNEL_TRIAL_NOT_CALIBRATED_VALIDATION"
MOVIE_FPS=5
F=[f"F_{i}{j}" for i in range(3) for j in range(3)]
def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def record(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def now():
    return datetime.now(timezone.utc).isoformat()


def observer_cohort(initial, cfg):
    """Immutable old physical cohort; added foundation/left MPs never join it."""
    return ((initial[:, 0] > cfg["observerInitialXGreater"])
            & (initial[:, 1] > cfg["observerInitialYGreater"]))


def imported(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def relative(run, text):
    require(isinstance(text, str), "Native output relative path missing")
    part = Path(text)
    require(not part.is_absolute() and ".." not in part.parts, "Absolute/parent native output path refused")
    result = (run / part).resolve()
    require(result.is_relative_to(run), "Native output path escapes run")
    return result


def source_proof(run):
    source = (run / "source").resolve()
    manifest = load(source / "source-manifest.json")
    files = {}
    for row in manifest["files"]:
        path = relative(run, row["path"])
        require(path.is_relative_to(source), "Frozen source escapes source directory")
        key, actual = path.relative_to(source).as_posix(), record(path)
        require(key not in files and actual["sha256"] == row["sha256"] and actual["bytes"] == row["bytes"],
                f"Frozen source hash/size mismatch: {key}")
        files[key] = actual
    require("case.lisp" in files, "Executed case source not in actual source manifest")
    provenance = load(run / "source-provenance.json")
    require(provenance.get("sourceSnapshotExactLoadedBytes") is True
            and provenance.get("copiedByteEqualityBeforeLoad") is True, "Actual frozen runtime source proof missing")
    dll = provenance["nativeBackend"]
    native = source / "libs/kirchoff.dll"
    require(Path(dll["modulePath"]).resolve() == native and dll["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and dll["sha256"] == record(native)["sha256"], "Actual mapped frozen DLL mismatch")
    loaded = {Path(row["source"]).resolve() for row in provenance["verifiedAsdfActions"]
              if row.get("firstParty") is True and row.get("operation") == "load-op" and row.get("event") == "performing"}
    for key in ("scenarios/residual-clay-slope/package.lisp",
                "scenarios/residual-clay-slope/output.lisp", "scenarios/residual-clay-slope/runner.lisp",
                "scenarios/residual-clay-slope/toe-profile.lisp"):
        require(key in files and (source / key).resolve() in loaded, f"Required actual owned source not loaded: {key}")
    if load(run/'manifest.json')['config'].get('explicitHsApex'):
        key='materials/models/plastic/mc-hs-apex.lisp'
        require(key in files and (source/key).resolve() in loaded,'Explicit HS apex implementation not frozen and loaded')
    return {"status": "PASS", "sourceFilesVerified": len(files), "actualMappedDll": dll,
            "case": files["case.lisp"], "manifest": record(source / "source-manifest.json"),
            "runtimeProvenance": record(run / "source-provenance.json")}


def constants(run):
    import re
    text = (run / "source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp").read_text(encoding="utf-8-sig")
    result = {}
    for name in ("stress-atol", "stress-rtol", "kappa-tol"):
        found = re.search(r"\(defconstant\s+\+" + name + r"\+\s+([\d.eEdD+-]+)\)", text)
        require(found, f"Actual frozen native tolerance missing: {name}")
        result[name] = float(found[1].lower().replace("d", "e"))
    return result


def patch_vertices(values, cfg):
    """Actual F maps each original square material patch; not the GIMP kernel.
    No field interpolation, particle deletion or fabricated crack surface.
    """
    f = np.column_stack([values[k] for k in F]).reshape(-1,3,3)
    half = cfg["meshSize"] / cfg["mpsPerCell"] / 2
    corners = np.array([[-half,-half],[half,-half],[half,half],[-half,half]])
    xy = np.column_stack([values["x_m"], values["y_m"]])
    vertices = np.einsum("nij,kj->nki", f[:,:2,:2], corners) + xy[:,None,:]
    # Translation-free shoelace avoids cancellation when world coordinates grow.
    local = vertices - vertices[:,:1,:]
    area = .5*np.sum(local[:,:,0]*np.roll(local[:,:,1],-1,axis=1)-local[:,:,1]*np.roll(local[:,:,0],-1,axis=1),axis=1)
    require(np.isfinite(vertices).all() and np.all(area>0) and
            np.allclose(area, values["J"]*values["reference_volume_m3_per_m"],rtol=2e-9,atol=1e-12),
            "Actual deformed patch area disagrees with positive J*originalV0")
    return vertices


def render(report, output, read_vtk, video):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize, LinearSegmentedColormap
    from matplotlib.collections import PolyCollection
    helper = imported(output / "analysis-source" / "review-urmi-damage40.py", "proper_render_csv")
    cfg = report["actualConfig"]
    states = report["states"]
    displayed = states or report["preparationSnapshots"]
    csv_name = "material-state.csv" if states else "preparation-material-state.csv"
    values = [v for _,v in helper.csv_frames(output / "saved-inputs" / csv_name)]
    require(len(values)==len(displayed), "Render actual saved state count differs")
    origin = np.array([cfg["displayOriginX"], cfg["displayOriginY"]])
    patches = [patch_vertices(v,cfg)-origin for v in values]
    all_points = np.concatenate(patches).reshape(-1,2)
    lo=np.minimum(all_points.min(axis=0),-origin)
    hi=np.maximum(all_points.max(axis=0),[cfg["domainWidth"]-origin[0],cfg["domainHeight"]-origin[1]])
    margin=max(1,.02*max(hi-lo)); bounds=[lo[0]-margin,hi[0]+margin,lo[1]-margin,hi[1]+margin]
    directories={kind:output/f"actual-{kind}-frames" for kind in ("motion","damage","plastic-strain")}
    for directory in directories.values(): directory.mkdir()
    soil=LinearSegmentedColormap.from_list("soil",["#67432f","#b87943","#ecd6a3"])
    for index,(state,v,verts) in enumerate(zip(displayed,values,patches)):
        for kind,directory in directories.items():
            fig=plt.figure(figsize=(14,6)); ax=fig.add_axes([.07,.15,.81,.67])
            colours=v["initial_y_m"] if kind=="motion" else (v["mc_kappa"] if kind=="plastic-strain" else v["strength_damage"])
            collection=PolyCollection(verts,edgecolors="none",linewidths=0,antialiaseds=False,
                cmap=soil if kind=="motion" else "inferno",
                norm=Normalize(0,cfg["baseHeight"]+cfg["height"]) if kind=="motion" else Normalize(0,.2 if kind=="plastic-strain" else 1))
            collection.set_array(colours); ax.add_collection(collection)
            ax.set(xlim=bounds[:2],ylim=bounds[2:],xlabel="world x (m)",ylabel="world y (m)")
            ax.set_aspect("equal",adjustable="box"); ax.grid(alpha=.12)
            event={0:"initial soil",1:"measured drained equilibrium",2:"instantaneous material switch",3:"gravity-driven MC motion"}[state["phaseCode"]]
            if cfg.get('explicitHsApex'): event += ' | explicit volumetric apex flow'
            status="COMPLETE 8 s PROFILE TRIAL" if report["nativeComplete"] else "PARTIAL TRIAL"
            channel={"motion":"Soil motion (original depth colours)","damage":"MC frictional strength loss", "plastic-strain":"Accumulated equivalent plastic shear strain (NOT damage)"}[kind]
            fig.suptitle(f"{channel} | {status}\nONE constant40deg face; no notch; native t={state['nativeTimeS']:.2f} s\nExplicit volumetric apex flow; gravity from zero stress",fontsize=11)
            fig.text(.07,.035,f"All {report['particleCount']} material patches from actual F; equal metres; overlaps/gaps retained; no calibrated validation",fontsize=9)
            if kind!="motion": fig.colorbar(collection,cax=fig.add_axes([.915,.24,.018,.43]),label="kappa (colour capped at0.2; values retained)" if kind=="plastic-strain" else "D_phi = 1 - tan(phi) / tan(phi_peak)")
            fig.savefig(directory/f"frame_{index:04d}.png",dpi=100)
            if index==len(displayed)-1: fig.savefig(output/f"proper-{kind}-result.png",dpi=140)
            plt.close(fig)
    media={"status":"PASS","scope":SCOPE,"actualMovieStates":len(displayed),"allParticlesShown":True,
           "coordinateScale":1,"colourRanges":{"damage":[0,1],"plastic-strain":[0,.2]},"interpolation":False,"plotBoundsWorldM":bounds,
           "renderGeometry":"Actual F convects each original square patch; numerical quadrature domains distinct; overlaps/gaps retained",
           "sameActualStateSequenceAndTimingForAllMovies":True,"movies":{}}
    if video:
        executable=shutil.which("ffmpeg")
        if executable is None:
            import imageio_ffmpeg
            executable=imageio_ffmpeg.get_ffmpeg_exe()
        for kind,directory in directories.items():
            destination=output/({"motion":"soil-motion.mp4","damage":"strength-damage.mp4","plastic-strain":"plastic-shear-strain.mp4"}[kind])
            command=[executable,"-v","error","-y","-framerate",str(MOVIE_FPS),"-i",str(directory/"frame_%04d.png"),
                     "-frames:v",str(len(displayed)),"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(destination)]
            write(output/f"{kind}-video-command.json",command)
            encoded=subprocess.run(command,capture_output=True,text=True)
            (output/f"{kind}-video.stderr.log").write_text(encoded.stderr)
            require(encoded.returncode==0,f"{kind} encoding failed; saved data retained")
            decoded=subprocess.run([executable,"-v","error","-nostats","-progress","pipe:1","-i",str(destination),"-f","null","-"],capture_output=True,text=True)
            (output/f"{kind}-decode.stdout.log").write_text(decoded.stdout)
            (output/f"{kind}-decode.stderr.log").write_text(decoded.stderr)
            counts=[int(line.split("=",1)[1]) for line in decoded.stdout.splitlines() if line.startswith("frame=")]
            require(decoded.returncode==0 and not decoded.stderr.strip() and counts and counts[-1]==len(displayed),f"{kind} decode/count failed")
            media["movies"][kind]={"video":record(destination),"decodedFrames":counts[-1],"framesPerSecond":MOVIE_FPS}
    return media


def inspect(run,output,manifest,data,helper,reader):
    require(manifest['scenario']=='clay-single-slope' and manifest['particleCount']==14010,'Wrong residual-clay native case')
    cfg=manifest['config'];proof=source_proof(run);native=constants(run)
    require(cfg.get('singleSlope') is True and cfg['slope']==40 and 'upperSlopeDeg' not in cfg and cfg['duration']==8 and cfg['frames']==17,'Undeclared geometry/duration')
    require(cfg['meshSize']==.5 and cfg['mpsPerCell']==2 and cfg['youngsModulusPa']==20e6 and cfg['poissonRatio']==.2 and cfg['density']==2000,'Actual material/resolution differs')
    table=np.array(cfg['frictionTable']);peak=math.tan(math.radians(cfg['peakFrictionDeg']))
    require(table[0,1]==33.99 and math.isclose(math.tan(math.radians(table[-1,1]))/peak,.25,abs_tol=1e-12),'Peak initial/quarter positive residual differs')
    history=helper.history_rows(data/'history.csv');states=[];baseline=None;previous=None;velocities=[];candidates=[]
    for frame,v in helper.csv_frames(data/'material-state.csv'):
        require(frame==len(states),'Nonconsecutive saved frames')
        n=14010;h=history[frame]
        require(np.array_equal(v['particle_id'],np.arange(n)) and h['particle_count']==n,'Actual logical IDs/count/order differ')
        points,fields=reader.read_cliff_vtk(data/(manifest['dynamicVtkPattern']%frame))
        require(helper.close(points[:,0],v['x_m']) and helper.close(points[:,1],v['y_m']),'CSV/VTK coordinates differ')
        f=np.column_stack([v[k] for k in F]).reshape(n,3,3);j=v['J'];mass=v['mass_kg_per_m'];v0=v['reference_volume_m3_per_m']
        require((j>0).all() and (mass>0).all() and (v0>0).all() and helper.close(np.linalg.det(f),j) and helper.close(v['volume_m3_per_m'],j*v0),'F/J/positive mass/originalV0 identity failed')
        initial=np.column_stack([v['initial_x_m'],v['initial_y_m']]);ids=helper.integers(fields['unique-id'],'VTK IDs')
        if baseline is None:
            require(helper.close(initial,points[:,:2]) and (v['mc_kappa']==0).all(),'Initial state/kappa preload differs')
            xs=np.arange(.125,72,.25); ys=np.arange(.125,18,.25)
            surface=8+np.maximum(0,10-np.maximum(0,xs-24)*math.tan(math.radians(40)))
            expected=np.array([[x,y] for x,z in zip(xs,surface) for y in ys if y<=z])
            order=np.lexsort((initial[:,1],initial[:,0]))
            require(expected.shape==initial.shape and helper.close(initial[order],expected),'Actual no-notch constant40degree geometry differs from independent full-grid clip')
            baseline={'mass':mass.copy(),'v0':v0.copy(),'ids':ids.copy(),'initial':initial.copy()}
            cohort=observer_cohort(initial,cfg);graph=helper.graph_for(initial,cohort,.2525)
        require(np.array_equal(mass,baseline['mass']) and np.array_equal(v0,baseline['v0']) and np.array_equal(ids,baseline['ids']) and np.array_equal(initial,baseline['initial']),'Actual immutable reference changed')
        require(np.array_equal(v['free_upper_reference_subset'],cohort.astype(float)),'Physical observer cohort changed')
        phi=np.radians(np.interp(v['mc_kappa'],table[:,0],table[:,1]));d=1-np.tan(phi)/peak
        require(helper.close(v['friction_rad'],phi) and helper.close(v['strength_damage'],d) and (d>=-1e-12).all() and (d<=.75+1e-12).all(),'Actual friction law/quarter floor differs')
        require((v['cohesion_pa']==0).all() and (v['dilation_rad']==0).all() and (v['E_pa']==20e6).all() and (v['nu']==.2).all() and (v['damage_active']==1).all(),'Unapproved material switch or strength inputs')
        for field,key in {'mc-kappa':'mc_kappa','mc-strength-damage':'strength_damage','mc-cohesion-pa':'cohesion_pa','mc-friction-rad':'friction_rad'}.items():require(helper.close(fields[field],v[key]),'CSV/VTK material differs:'+field)
        residual=helper.six_plane_residual(v);tol=native['stress-atol']+native['stress-rtol']*np.maximum(1,v['native_projection_trial_scale_pa'])
        require(helper.close(tol,v['native_yield_tolerance_pa']) and (residual<=tol).all() and (np.abs(residual-v['yield_residual_kirchhoff_pa'])<=tol).all(),'Actual native yield admissibility failed')
        require((v['mc_kappa']>=0).all() and (v['plastic_work_pa']>=0).all(),'Negative accumulated history')
        if previous is not None:
            require((v['mc_kappa']>=previous['mc_kappa']-native['kappa-tol']).all() and (v['plastic_work_pa']>=previous['plastic_work_pa']-helper.ATOL-helper.RTOL*np.abs(previous['plastic_work_pa'])).all(),'History decreased')
        velocity=np.column_stack([v['vx_m_per_s'],v['vy_m_per_s']]);ke=float(np.sum(.5*mass*np.sum(velocity**2,axis=1)))
        require(helper.close(ke,h['kinetic_energy_j_per_m']) and helper.close(mass.sum(),h['mass_kg_per_m']) and helper.close(v['time_s'],frame*.5,time=True) and helper.close(v['native_time_s'],v['time_s'],time=True),'Actual saved time/KE/mass differs')
        displacement=points[:,:2]-initial;downhill=displacement@np.array([math.cos(math.radians(40)),-math.sin(math.radians(40))])
        selected=helper.largest_component(cohort&(displacement[:,0]>=.25)&(downhill>=.5),graph,mass)
        fraction=float(mass[selected].sum()/mass[cohort].sum()) if len(selected) else 0
        velocities.append(velocity[:,0].copy());interval={'status':'NOT_DETECTED'}
        if len(selected) and fraction>=.1:
            mean=np.array([np.average(vx[selected],weights=mass[selected]) for vx in velocities])
            interval=helper.sustained_interval(np.array([s['timeS'] for s in states]+[frame*.5]),mean,{'minimumSustainedVxMPerS':.001,'minimumSustainedDurationS':1})
            if interval['status']=='PASS':candidates.append({'frame':frame,'timeS':frame*.5,'fractionOfUpperCohortMass':fraction,'interval':interval})
        eligible=cohort&(initial[:,0]<=cfg['toeX']+.5);crossed=eligible&(points[:,0]>cfg['toeX']+.5)
        state={'frame':frame,'timeS':frame*.5,'nativeTimeS':float(v['native_time_s'][0]),'phaseCode':3,'vtk':record(data/(manifest['dynamicVtkPattern']%frame)),
               'minJ':float(j.min()),'maximumStrengthLoss':float(d.max()),'minimumFrictionDeg':float(np.degrees(phi).min()),'kineticJPerM':ke,
               'maximumDisplacementM':float(np.linalg.norm(displacement,axis=1).max()),'connectedMovingFractionOfUpperCohortMass':fraction,
               'upperCohortCentroidDisplacementM':np.average(displacement[cohort],weights=mass[cohort],axis=0).tolist(),
               'newlyPastToeCohortMassFraction':float(mass[crossed].sum()/mass[cohort].sum()),'actualParticles':n}
        active=v['strength_damage']>1e-6; plastic=v['mc_kappa']>1e-8
        near=(np.abs(initial[:,0]-cfg['toeX'])<3)&(np.abs(initial[:,1]-cfg['baseHeight'])<3)
        kp=int(np.argmax(v['mc_kappa']));dp=int(np.argmax(v['strength_damage']))
        state['onsetObservation']={'plastifiedMPs':int(plastic.sum()),'damagedMPs':int(active.sum()),'toePlastifiedMPs':int((near&plastic).sum()),'toeDamagedMPs':int((near&active).sum()),'maximumKappa':float(v['mc_kappa'][kp]),'maximumKappaInitialXY':initial[kp].tolist(),'maximumDamageInitialXY':initial[dp].tolist()}
        states.append(state);previous={k:v[k].copy() for k in ('mc_kappa','plastic_work_pa')}
    require(len(states)==manifest['savedFrames'],'Saved frame count differs')
    if manifest['complete']:require(len(states)==17 and states[-1]['timeS']==8,'Native complete lacks8s/17states')
    return {'scope':SCOPE,'savedIntegrity':'PASS','nativeComplete':manifest['complete'],'nativeStatus':manifest['status'],'actualConfig':cfg,'sourceProof':proof,
            'apexConvention':manifest.get('apexConvention','Strict MC; no additional volumetric apex flow'),
            'particleCount':14010,'states':states,'preparationSnapshots':[],'actualDynamicSavedFrames':len(states),'actualLastDynamicTimeS':states[-1]['timeS'] if states else 0,
            'qualitativeMotionCandidates':candidates,'landslideVerified':False,'scientificallyValidated':False,
            'initialization':'Human-approved peak initial strength, zero initial stress/kappa,2s gravity ramp, NO geostatic equilibrium claim; no model switch',
            'damageMeaning':'D_phi strength loss, plateau to kappa.037, floor strength25%; separate kappa video is accumulated J2 plastic strain, NOT exact Urmi deviatoric-strain convention', 'firstDamagedSavedState':next((x['onsetObservation']|{'timeS':x['timeS']} for x in states if x['onsetObservation']['damagedMPs']>0),None), 'toeInitiationGuaranteed':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--video',action='store_true');p.add_argument('--allow-partial',action='store_true');p.add_argument('--stopped-wrapper',action='store_true');a=p.parse_args()
    run=a.run_dir.resolve();out=a.output_dir.resolve();m=load(run/'manifest.json');require(m['savedFrames']>0,'No complete actual saved frame available')
    stopped=a.stopped_wrapper and load(Path(str(run)+'-status.json'))['status']=='STOPPED_WALL_BUDGET'
    require(m['complete'] is True or (a.allow_partial and m['status']=='failed') or stopped,'No authoritative terminal proof')
    require(not out.exists(),'Choose fresh review output; preserve original failures');out.mkdir(parents=True);frozen=out/'analysis-source';frozen.mkdir();data=out/'saved-inputs';data.mkdir()
    bindings=[]
    for name in (Path(__file__).name,'review-urmi-damage40.py','plot_m5_cliff_comparison.py','preview-urmi-damage40.py'):
        src=Path(__file__).with_name(name);shutil.copyfile(src,frozen/name);bindings.append(record(frozen/name))
    write(out/'analysis-freeze.json',{'scope':'Observer frozen before saved-data inspection, after native launch; original launch/frozen-source retained','records':bindings})
    shutil.copyfile(run/'manifest.json',out/'observed-native-manifest.json')
    helper=imported(frozen/'review-urmi-damage40.py','quarter_helper');reader=imported(frozen/'plot_m5_cliff_comparison.py','quarter_reader');copy=imported(frozen/'preview-urmi-damage40.py','quarter_copy')
    stage='saved-input-copy'
    try:
        copied=[]
        for name,rows in [('history.csv',None),('material-state.csv',14010)]:copied.append(copy.copy_csv_prefix(run/name,data/name,m['savedFrames'],rows))
        for frame in range(m['savedFrames']):
            name=m['dynamicVtkPattern']%frame;copied.append(copy.copy_closed(run/name,data/name))
        write(out/'input-copy-binding.json',copied);stage='saved-state-audit';report=inspect(run,out,m,data,helper,reader);write(out/'integrity.json',report)
        stage='filled-media';report['media']=render(report,out,reader.read_cliff_vtk,a.video);write(out/'review.json',report)
        print(json.dumps({'savedIntegrity':report['savedIntegrity'],'nativeComplete':report['nativeComplete'],'frames':len(report['states']),'scope':SCOPE}))
        return 0 if m['complete'] else 2
    except Exception as e:
        write(out/'stage-failure.json',{'stage':stage,'error':str(e),'traceback':traceback.format_exc(),'nativeSolverRerun':False});raise
if __name__=='__main__':raise SystemExit(main())
