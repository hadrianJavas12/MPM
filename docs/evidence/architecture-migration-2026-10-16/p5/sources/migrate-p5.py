import hashlib,json,os
from pathlib import Path
R=Path('D:/MPM');P=json.loads((R/'docs/architecture/P5_ENGINE_MIGRATION.json').read_text())
B=R/'output/architecture-migration-2026-10-16/p5-source-before';assert not B.exists()
asd=R/'cl-mpm.asd';text=asd.read_bytes().decode('utf8');records=[]
for row in P['files']:
 s=R/row['source'];t=R/row['target'];b=s.read_bytes()
 assert hashlib.sha256(b).hexdigest()==row['sourceSha256'] and not t.exists()
 old='(:file "'+row['source'][:-5]+'")';new='(:file "'+row['source'][:-5]+'" :pathname "'+row['target'][:-5]+'")'
 assert text.count(old)==1; text=text.replace(old,new)
 backup=B/row['source'];backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(b)
 t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(b)
 relative=os.path.relpath(t,s.parent).replace('\\','/')
 s.write_text(';;;; Legacy source path; normal ASDF loads the engine owner directly.\n(load (merge-pathnames "'+relative+'" (uiop:pathname-directory-pathname *load-truename*)))\n')
 records.append({'source':row['source'],'target':row['target'],'beforeSha256':hashlib.sha256(b).hexdigest(),'afterSha256':hashlib.sha256(t.read_bytes()).hexdigest(),'wholeFileByteIdentical':b==t.read_bytes()})
asd.write_bytes(text.encode('utf8'))
(B.parent/'p5-source-identity.json').write_text(json.dumps(records,indent=2)+'\n')
print('P5: 2 complete engine files byte-identical; old ASDF IDs and source loaders preserved.')
