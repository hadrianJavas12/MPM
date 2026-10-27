"""Sparse stdout observations only; never reconstruct missing preparation CSV."""
from pathlib import Path
import json,re,hashlib
out=Path(__file__).resolve().parent
path=out.parent/'full-001.stdout.log'
raw=path.read_bytes()
rows=[]
for match in re.finditer(rb'\[urmi-damage40\] ([^\r\n]+?) updates=(\d+) native=([\d.]+) RF=(\S+) RK=(\S+)',raw):
    phase,step,time,rf,rk=match.groups()
    def number(value): return float(value.decode().lower().replace('d','e'))
    rows.append({'phase':phase.decode(),'updates':int(step),'nativeTimeS':number(time),'RF':number(rf),'RK':number(rk)})
assert len(rows)==193 and rows[-1]['updates']==19300
below=[r for r in rows if r['nativeTimeS']>=2 and r['RF']<1e-4]
both=[r for r in below if r['RK']<1e-8]
crossings=[{'previous':a,'current':b} for a,b in zip(rows,rows[1:]) if (a['RF']<1e-4)!=(b['RF']<1e-4)]
summary={'scope':'Sparse actual100-step stdout samples only; not reconstructed CSV, per-update convergence proof or final particle state',
 'source':{'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
 'samples':len(rows),'acceptedUpdatesFromTerminalManifest':19320,'lastLoggedUpdates':19300,'unprintedTailAcceptedUpdates':20,
 'first':rows[0],'last':rows[-1],'minimumRF':min(rows,key=lambda r:r['RF']),'maximumRF':max(rows,key=lambda r:r['RF']),
 'minimumRK':min(rows,key=lambda r:r['RK']),'maximumRK':max(rows,key=lambda r:r['RK']),
 'postRampLoggedSamplesRFStrictlyBelow1e4':len(below),'postRampLoggedSamplesBothCriteria':len(both),
 'RFThresholdCrossingsBetweenSparseSamples':crossings,'csvReconstructed':False,'nativeSolverRerun':False,
 'limitation':'Unsampled updates are unavailable; crossing intervals cannot establish50consecutive updates over1s or100undamped updates over1s.'}
(out/'stdout-sampled-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['samples','minimumRF','maximumRF','last','postRampLoggedSamplesRFStrictlyBelow1e4','postRampLoggedSamplesBothCriteria']}))
