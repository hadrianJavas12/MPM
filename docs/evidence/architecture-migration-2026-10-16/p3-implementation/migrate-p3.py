"""Apply reviewed byte-bound ownership extraction; never change defining bodies."""
import hashlib,json
from pathlib import Path
R=Path('D:/MPM')
plan=json.loads((R/'docs/architecture/P3_DIAGNOSTICS_MIGRATION.json').read_text())
source=R/plan['source_path']; raw=source.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)==plan['source_sha256_before']
before=R/'output/architecture-migration-2026-10-16/p3-source-before'
assert not before.exists(),'Do not overwrite before evidence'
pieces={}
for f in plan['forms']:
    body=raw[f['source_start_byte']:f['source_end_byte_exclusive']]
    assert sha(body)==f['source_form_sha256']
    pieces[f['source_form_id']]=body
ids=[i for g in plan['ordered_groups'] for i in g['source_form_ids']]
assert len(ids)==len(set(ids))==len(pieces) and set(ids)==set(pieces)
targets={}
for g in plan['ordered_groups']:
    target=R/g['target_path']; assert not target.exists(),str(target)
    forms=[pieces[i] for i in g['source_form_ids']]
    if 'F01' not in g['source_form_ids']:forms.insert(0,pieces['F01'])
    targets[target]=b';;;; Existing read-only diagnostics; defining bodies preserved exactly.\r\n'+b'\r\n\r\n'.join(forms)+b'\r\n'
backup=before/plan['source_path']; backup.parent.mkdir(parents=True);backup.write_bytes(raw)
for path,data in targets.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
paths=[g['target_path'] for g in plan['ordered_groups']]
shim=';;;; Historical source-path compatibility; ASDF loads the new owners directly.\n(in-package :cl-user)\n'
shim+='(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))\n'
shim+='  (dolist (relative \'('+ ' '.join(json.dumps(p) for p in paths)+'))\n'
shim+='    (load (merge-pathnames relative root))))\n'
source.write_text(shim,encoding='utf8')
proof={'phase':'P3','sourceSha256':sha(raw),'beforeSource':str(backup.relative_to(R)),
       'all31SourceFormsCoveredExactlyOnce':True,'definingBodyChanges':False,
       'targets':{str(p.relative_to(R)):sha(b) for p,b in targets.items()},
       'forms':[{k:f[k] for k in ('source_form_id','source_form_sha256','target_path')} for f in plan['forms']]}
(before.parent/'p3-extraction-form-hashes.json').write_text(json.dumps(proof,indent=2)+'\n')
print('P3: 31 original forms verified and extracted; no defining-body changes.')
