"""One saved-only terminal observer: initial VTK, no missing CSV/state reconstruction."""
from pathlib import Path
import importlib.util,json,math,sys,traceback
from datetime import datetime,timezone
import numpy as np

OUT=Path(__file__).resolve().parent
BASE=OUT.parent
RUN=BASE/'full-001'
PREP=BASE/'full-001-launch-preparation'
def load(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
try:
    review=module('prepared_review',OUT/'analysis-source/review-urmi-damage40.py')
    reader=module('prepared_reader',OUT/'analysis-source/plot_m5_cliff_comparison.py')
    rec=review.record
    manifest,status,worker=load(RUN/'manifest.json'),load(Path(str(RUN)+'-status.json')),load(BASE/'full-001-detached/worker-exit.json')
    assert status['status']=='FAILED_NATIVE' and status['nativeExitCode']==1 and worker['exitCode']==1
    assert manifest['complete'] is False and manifest['phase']=='drained-ramp-and-relaxation'
    assert manifest['dynamicUpdates']==0 and manifest['savedFrames']==0 and manifest['nativeTimeS']==20
    assert manifest['error']=='Owned drained equilibrium update cap reached; no parameter tuning/restart applied.'
    prepared=load(PREP/'preparation.json')
    runtime_sources=review.verified_sources(RUN)
    expected={row['path'].replace('\\','/'):row for row in prepared['expectedNativeFiles']}
    actual={row['path'].replace('\\','/'):row for row in load(RUN/'source/source-manifest.json')['files']}
    assert set(expected)==set(actual)
    for name,row in expected.items():
        assert (row['bytes'],row['sha256'])==(actual[name]['bytes'],actual[name]['sha256'])
        copied=rec(PREP/'native-expected'/name)
        assert (copied['bytes'],copied['sha256'])==(row['bytes'],row['sha256'])
    for support in prepared['support']:
        assert rec(Path(support['copy']['path']))['sha256']==support['copy']['sha256']==support['original']['sha256']
    for filename,relative in [('review-urmi-damage40.py','analysis/review-urmi-damage40.py'),
                              ('plot_m5_cliff_comparison.py','analysis/plot_m5_cliff_comparison.py'),('contract.json','protocol/contract.json')]:
        assert rec(OUT/'analysis-source'/filename)['sha256']==rec(PREP/relative)['sha256']
    vtk_paths=sorted(p.name for p in (RUN/'vtk').glob('*.vtk'))
    assert vtk_paths==['initial.vtk','mesh.vtk']
    points,fields=reader.read_cliff_vtk(RUN/'vtk/initial.vtk')
    n=len(points)
    assert n==manifest['particleCount']==6714
    for key in ['mass','volume','size_x','size_y','unique-id','mc-logical-id','mc-kappa','mc-cohesion-pa',
                'mc-friction-rad','mc-dilation-rad','mc-plastic-work-j-m3','mc-strength-damage','mc-damage-active','mc-kappa-origin']:
        assert key in fields,key
    assert np.array_equal(fields['mc-logical-id'],np.arange(n))
    assert len(np.unique(fields['unique-id']))==n
    for key in ['mc-kappa','mc-plastic-work-j-m3','mc-strength-damage','mc-damage-active','mc-kappa-origin','mc-dilation-rad']:
        assert np.equal(fields[key],0).all(),key
    assert np.equal(fields['mc-cohesion-pa'],3700).all()
    assert np.allclose(fields['mc-friction-rad'],math.radians(30.6),atol=1e-11,rtol=1e-11)
    for key,array in fields.items():
        if key.startswith('sig_') or key.startswith('vel_'): assert np.equal(array,0).all(),key
    assert (fields['volume']>0).all() and (fields['size_x']>0).all() and (fields['size_y']>0).all()
    cfg=manifest['config']
    assert np.allclose(fields['mass'],fields['volume']*cfg['density'],atol=1e-11,rtol=1e-11)
    x,y=points[:,0],points[:,1]
    assert (points[:,2]==0).all()
    surface=4+np.maximum(0,10-math.tan(math.radians(40))*np.maximum(0,x-12))
    assert (y<=surface+1e-12).all() and (x>=0).all() and (x<=60).all() and (y>=0).all() and (y<=20).all()
    foundation=int(np.sum(y<4));assert foundation==3840
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import Normalize
    vertices=np.stack([np.column_stack([x-fields['size_x']/2,y-fields['size_y']/2]),
                       np.column_stack([x+fields['size_x']/2,y-fields['size_y']/2]),
                       np.column_stack([x+fields['size_x']/2,y+fields['size_y']/2]),
                       np.column_stack([x-fields['size_x']/2,y+fields['size_y']/2])],axis=1)
    fig,ax=plt.subplots(figsize=(15,6),constrained_layout=True)
    domains=PolyCollection(vertices,array=fields['mc-strength-damage'],cmap='inferno',norm=Normalize(0,1),edgecolors='none')
    ax.add_collection(domains);ax.set(xlim=(-.5,60.5),ylim=(-.5,20.5),xlabel='x (m)',ylabel='y (m)')
    ax.set_aspect('equal',adjustable='box')
    ax.set_title('ONLY surviving initial particle state | 40 degree soil slope, no notch | 6,714 actual MPs\n'
                 'Strength damage inactive: D_s = 0 | coordinate scale 1, fixed D_s scale 0-1 | no dynamic evolution saved')
    fig.colorbar(domains,ax=ax,label='Constitutive strength loss D_s (inactive during drained preparation)',shrink=.8)
    fig.savefig(OUT/'initial-only-scale1.png',dpi=150);plt.close(fig)
    report={
      'status':'PASS_SCOPED_INITIAL_VTK_ONLY','observedUtc':datetime.now(timezone.utc).isoformat(),
      'preparedFullReviewExecuted':False,'preflight':load(OUT/'prepared-review-preflight.json'),
      'terminal':{'sourceCommit':status['sourceCommit'],'nativeExitCode':status['nativeExitCode'],'workerExitCode':worker['exitCode'],
                  'startedUtc':status['startedUtc'],'endedUtc':status['endedUtc'],'workerFinishedUtc':worker['finishedUtc'],
                  'phase':manifest['phase'],'nativeTimeS':manifest['nativeTimeS'],'updates':manifest['updates'],
                  'dynamicTimeS':manifest['timeS'],'dynamicUpdates':manifest['dynamicUpdates'],'dynamicSavedFrames':manifest['savedFrames'],
                  'error':manifest['error'],'lastManifestRF':manifest['freeForceRatio'],'requiredRFStrictlyBelow':cfg['forceTolerance'],
                  'lastManifestRK':manifest['freeKineticRatio'],'materialIntegrationFailure':False},
      'sources':runtime_sources,'prelaunchNativePayloadsMatched':len(expected),'prelaunchSupportCopiesVerified':len(prepared['support']),
      'sourceArchiveReference':rec(Path('D:/MPM/docs/evidence/urmi-mc-damage40-2026-10-27/full-001-launch/executed-source-and-cache.zip')),
      'savedState':{'file':rec(RUN/'vtk/initial.vtk'),'kind':'initial only','particles':n,'scalarFields':len(fields),
                    'scalarFieldNames':sorted(fields),'allSavedFieldsFinite':True,'positiveMassVolumeDomain':True,
                    'massKgPerM':float(fields['mass'].sum()),'foundationParticles':foundation,
                    'maxStrengthDamage':float(fields['mc-strength-damage'].max()),'damageActive':False,
                    'maxKappa':float(fields['mc-kappa'].max()),'cohesionPa':3700,
                    'boundsMinM':points.min(axis=0).tolist(),'boundsMaxM':points.max(axis=0).tolist()},
      'media':{'png':rec(OUT/'initial-only-scale1.png'),'coordinateScale':1,'colourRange':[0,1],'interpolation':False,
               'video':'NOT_PRODUCED_SINGLE_INITIAL_STATE'},
      'limitations':['All preparation CSV absent; no full preparation-history audit or CSV/VTK pairing is possible.',
                     'No drained-equilibrium, transfer, or dynamic particle snapshot survived; native20s is not a saved state.',
                     'F9/J/global V=J*V0 cannot be independently audited from surviving fields without CSV; not asserted.',
                     'No time evolution, damage onset, coherent sliding, runout, or scientific validation is established.'],
      'nativeSolverRerun':False,'csvReconstructed':False,'landslideVerified':False}
    write('observation.json',report)
    print(json.dumps({'status':report['status'],'particles':n,'sources':len(expected),'dynamicStates':0,'maxStrengthDamage':0}))
except Exception as error:
    write('observer-failure.json',{'error':str(error),'traceback':traceback.format_exc(),'nativeSolverRerun':False,'savedInputsPreserved':True})
    raise
