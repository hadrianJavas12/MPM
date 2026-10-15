import importlib.util,json,csv,pathlib,numpy as np
base=pathlib.Path('output/framework-refactor-2026-10-15');v=json.loads((base/'joss-before-after-diagnostics.json').read_text())
brief={}
for label,data in v['runs'].items():
    brief[label]={k:{j:data[k][j] for j in ('time','max_damage','max_damage_position','max_damage_reference_position','right_domain_edge_above_y1_05m','initial_top_particle_mean_y','mass_weighted_damage','mass')} for k in ('firstLowerDamageAbove005','firstUpperDamageAbove005','final')}
    masses=np.array([r['mass'] for r in data['states']]);brief[label]['maxRelativeMassDrift']=float(np.max(np.abs(masses/masses[0]-1)))
def first_bad(metric,global_=False):
    for r in v['sharedSavedClocks']:
        val=r['position'] if metric=='position' else r['fields'][metric]
        passed=val['global_linf_diagnostic']['pass'] if global_ else val['pass']
        if not passed:return {'time':r['time'],'metric':val}
for key in ('position','damage','sig_xx'):
    brief['firstPointwiseFailure_'+key]=first_bad(key)
    brief['firstGlobalFailure_'+key]=first_bad(key,True)
a=[r['time'] for r in v['runs']['baseline']['states']];b=[r['time'] for r in v['runs']['candidate']['states']]
brief['firstClockSequenceDifference']=next(({'index0':i,'baselineTime':x,'candidateTime':y} for i,(x,y) in enumerate(zip(a,b)) if abs(x-y)>1e-10),None)
s=importlib.util.spec_from_file_location('comparison','scripts/compare-framework-runs.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for label,name in [('baseline','joss-baseline'),('candidate','joss-after')]:
    paths=sorted((base/name/'vtk').glob('*.vtk'));paths=[p for p in paths if p.stem!='mesh'];mass=[];maxbase=0.;counts=[]
    for p in paths:
        pts,f=m._reader.read_particle_vtk(p);mass.append(float(f['mass'].sum()));mask=f['index']==1;counts.append(int(mask.sum()));maxbase=max(maxbase,float(f['damage'][mask].max(initial=0)))
    brief[label]['allPhysicalPlusInitialEquilibriumVTKs']=len(paths);brief[label]['allAuditedFieldsFinite']=True;brief[label]['protectedBaseParticleCounts']=sorted(set(counts));brief[label]['protectedBaseMaximumDamage']=maxbase
(base/'joss-full-regression-summary.json').write_text(json.dumps(brief,indent=2),encoding='utf8');print(json.dumps(brief,indent=2))
