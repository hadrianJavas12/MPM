import importlib.util,json,pathlib,numpy as np
s=importlib.util.spec_from_file_location('comparison', 'scripts/compare-framework-runs.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
vtk=pathlib.Path('output/reference-reproduction-2026-10-15/dp-physical-pilot/vtk/sim_00002.vtk')
p,f=m._reader.read_particle_vtk(vtk)
order=np.random.default_rng(20261015).permutation(len(p))
pp=p[order].copy();ff={k:v[order].copy() for k,v in f.items()}
a,b,basis=m.identity(p,f,pp,ff,1e-7)
reorder=bool(np.array_equal(p[a],pp[b]) and all(np.array_equal(v[a],ff[k][b]) for k,v in f.items()))
key='sig_yy';ff[key][b[0]]+=1000.0
stress_detected=not m.metric(f[key][a],ff[key][b],1e-8,1e-7)['pass']
ff={k:v[order].copy() for k,v in f.items()};ff['damage'][b[0]]=0.5
Damage_detected=not m.metric(f['damage'][a],ff['damage'][b],1e-8,1e-7)['pass']
ff={k:v[order].copy() for k,v in f.items()};ff['disp_x'][0]+=0.125
try:
    m.identity(p,f,pp,ff,1e-7)
    broken_identity_rejected=False
except ValueError:
    broken_identity_rejected=True
checks={'reordered_particles_preserve_all_arrays':reorder,'detect_1kPa_stress_perturbation':stress_detected,'detect_damage_perturbation':Damage_detected,'reject_changed_reference_identity':broken_identity_rejected}
result={'fixture':str(vtk),'fixtureSha256':m.sha256(vtk),'particles':len(p),'identity':basis,'checks':checks,'passed':all(checks.values())}
path=pathlib.Path('output/framework-refactor-2026-10-15/comparator-guard-checks.json');path.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
assert result['passed']
