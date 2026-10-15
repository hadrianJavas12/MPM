"""Diagnostics for complete native runs with differing saved clocks; never declares equivalence."""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np
s=importlib.util.spec_from_file_location('comparison',Path('D:/MPM/scripts/compare-framework-runs.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
_,ca,sa=m.recorded_states(args.baseline);_,cb,sb=m.recorded_states(args.candidate)
result={'purpose':'Diagnostics only, does not override strict pointwise pass/fail; no interpolated states or referencevideo timeline','scientificValidation':False,'runs':{},'sharedSavedClocks':[]}
for label,run,states in [('baseline',args.baseline,sa),('candidate',args.candidate,sb)]:
    meta=json.loads((run/'reference-metadata.json').read_text(encoding='utf-8-sig'));assert meta['complete'] is True and meta['termination']=='simulation-time'
    records=[]
    for state in states:
        points,fields=m._reader.read_particle_vtk(state['path']);records.append({'time':state['time'],'phase':state['row'].get('phase'),'file':str(state['path']),'sha256':m.sha256(state['path']),**m.state_summary(points,fields)})
    def first(key):return next((r for r in records if r.get(key) is not None and r[key]>.05),None)
    result['runs'][label]={'source':str(run),'metadata':meta,'savedStates':len(states),'states':records,'firstLowerDamageAbove005':first('lower_reference_y_le_4m'),'firstUpperDamageAbove005':first('upper_reference_y_ge_9m'),'final':records[-1]}
lookup={round(v['time'],10):v for v in sb};shared_a=[];shared_b=[]
for state in sa:
    cand=lookup.get(round(state['time'],10))
    if cand is None:continue
    assert abs(state['time']-cand['time'])<=1e-10
    pa,fa=m._reader.read_particle_vtk(state['path']);pb,fb=m._reader.read_particle_vtk(cand['path']);ia,ib,basis=m.identity(pa,fa,pb,fb,1e-7)
    result['sharedSavedClocks'].append({'time':state['time'],'identity':basis,'position':m.metric(pa[ia],pb[ib],1e-8,1e-7),'fields':{k:m.metric(fa[k][ia],fb[k][ib],1e-8,1e-7) for k in sorted(fa)}});shared_a.append(state);shared_b.append(cand)
result['sharedClockCurves']=m.curve_compare(ca,shared_a,cb,shared_b,1e-8,1e-7)
a,b=sa[-1],sb[-1];assert a['time']==b['time']
pa,fa=m._reader.read_particle_vtk(a['path']);pb,fb=m._reader.read_particle_vtk(b['path']);ia,ib,basis=m.identity(pa,fa,pb,fb,1e-7)
result['finalSameClockComparison']={'time':a['time'],'identity':basis,'position':m.metric(pa[ia],pb[ib],1e-8,1e-7),'fields':{k:m.metric(fa[k][ia],fb[k][ib],1e-8,1e-7) for k in sorted(fa)}}
spacing=.025;xs=np.arange(.5*spacing,31,spacing);ys=np.arange(.5*spacing,17.333333333,spacing);window=ys[:,None]>1.05
aa=m._reader.particle_occupancy(pa,fa,xs,ys,'rectangle')&window;bb=m._reader.particle_occupancy(pb,fb,xs,ys,'rectangle')&window
result['finalDomainOccupancy']={'meaning':'Numerical domain shape agreement, not physicalaccuracy','spacingM':spacing,'viewportXM':[0,31],'viewportYM':[0,17.333333333],'excludeFoundationYAtOrBelowM':1.05,'footprint':'actual VTK particle rectangle domains','intersectionOverUnion':float(np.count_nonzero(aa&bb)/np.count_nonzero(aa|bb))}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf8')
print(json.dumps({'baselineStates':len(sa),'candidateStates':len(sb),'sharedClocks':len(shared_a),'finalPosition':result['finalSameClockComparison']['position'],'finalShape':result['finalDomainOccupancy']},indent=2))
