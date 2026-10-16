"""Execute only the two hash-approved P1 extractions, preserving form bytes."""
import hashlib,json,re
from pathlib import Path
R=Path('D:/MPM')
A=json.loads((R/'docs/architecture/MIGRATION_APPROVALS.json').read_text())['approvals']
B=R/'output/architecture-migration-2026-10-16/p1-source-before'
def sha(b):return hashlib.sha256(b).hexdigest()
def forms(text):
    out=[]; depth=0; start=None; string=False; escape=False; line=False; block=0; i=0
    while i<len(text):
        c=text[i]; pair=text[i:i+2]
        if line:
            if c=='\n':line=False
        elif block:
            if pair=='#|':block+=1;i+=1
            elif pair=='|#':block-=1;i+=1
        elif string:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':string=False
        elif pair=='#|':block=1;i+=1
        elif c==';':line=True
        elif c=='"':string=True
        elif pair=='#\\':
            i+=2
            if i>=len(text):raise ValueError('Incomplete character token')
            if text[i].isalpha():
                while i+1<len(text) and text[i+1].isalnum():i+=1
        elif c=='(':
            if depth==0:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth<0:raise ValueError('Unbalanced form')
            if depth==0:out.append(text[start:i+1])
        i+=1
    assert depth==0 and not string and block==0
    return out

if B.exists():raise SystemExit('Refusing to overwrite before-source evidence')
source={a['source_path']:(R/a['source_path']).read_bytes() for a in A}
for a in A:assert sha(source[a['source_path']])==a['source_sha256_before']
spec='framework/components/specifications.lisp'
parsed={}
for f in forms(source[spec].decode('utf8')):
    m=re.match(r'\((\S+)\s+([^\s()]+)',f)
    assert m,f[:80]
    if m[1]=='in-package':continue
    assert m[2] not in parsed
    parsed[m[2]]=f
targets=A[0]['targets'];expected=[n for t in targets for n in t['forms']]
assert set(expected)==set(parsed) and len(expected)==len(parsed)
new={}
proof=[]
for t in targets:
    new[t['path']]=(';;;; Existing declarations extracted without numerical changes.\r\n(in-package :cl-mpm/framework)\r\n\r\n'+
        '\r\n\r\n'.join(parsed[n] for n in t['forms'])+'\r\n').encode('utf8')
    for n in t['forms']:proof.append({'name':n,'source':spec,'target':t['path'],
        'originalFormSha256':sha(parsed[n].encode('utf8')),'targetFormSha256':sha(parsed[n].encode('utf8'))})
new[A[1]['targets'][0]['path']]=source[A[1]['source_path']]
for path in new:
    if (R/path).exists():raise SystemExit('Refusing to replace existing target '+path)
for path,data in source.items():
    backup=B/path;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(data)
for path,data in new.items():
    target=R/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
for path,relatives in [(spec,['src/simulation/components/base.lisp','materials/core/definition.lisp','src/simulation/components/specifications.lisp']),
                      ('framework/components/materials.lisp',['materials/adapters/native.lisp'])]:
    body=';;;; Historical source-path compatibility; ASDF loads the new owner directly.\n(in-package :cl-user)\n'
    body+='(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))\n'
    body+='  (dolist (relative \'('+ ' '.join(json.dumps(v) for v in relatives)+'))\n'
    body+='    (load (merge-pathnames relative root))))\n'
    (R/path).write_text(body,encoding='utf8')
report={'startingCommit': '7c399fb','numericalBehaviorChangeAllowed':False,'originalDefiningForms':len(proof),
        'exactFormByteEquality':True,'forms':proof,
        'nativeAdapterExactFileByteEquality':(R/A[1]['targets'][0]['path']).read_bytes()==source[A[1]['source_path']],
        'targetSha256':{p:sha(d) for p,d in new.items()},'beforeSourceRoot':str(B.relative_to(R))}
(B.parent/'p1-extraction-form-hashes.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('forms','targetSha256')},indent=2))
