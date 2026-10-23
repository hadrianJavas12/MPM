import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
run=ROOT/'output/wang2017-reference-2026-10-23/diagnostic-fast-005-002'
dest=ROOT/'docs/evidence/wang2017-reference-2026-10-23/diagnostic-fast-005-002-video'
audit=json.loads((run/'output-audit.json').read_text())
assert audit['passedConsistencyChecks'] and not audit['nativeComplete'] and audit['frames']==78
expected={r['path'].replace('\\','/'):r['sha256'] for r in audit['sources']}
verified=0
with tarfile.open(ROOT/'docs/evidence/wang2017-reference-2026-10-23/diagnostic-fast-005-002-failure/raw-native-output.tar.gz') as archived:
 for member in archived:
  if member.name in expected:
   assert hashlib.sha256(archived.extractfile(member).read()).hexdigest()==expected[member.name]
   verified+=1
assert verified==78
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,r_frame_rate,duration','-show_entries','format=duration,size','-of','json',str(run/'slope-descent.mp4')]))
assert probe['streams'][0]['nb_frames']=='78' and probe['streams'][0]['codec_name']=='h264'
subprocess.run(['ffmpeg','-v','error','-i',str(run/'slope-descent.mp4'),'-f','null','-'],check=True)
dest.mkdir(parents=True,exist_ok=False);(dest/'.gitattributes').write_text('* -text -whitespace\n')
for name in ('slope-descent.mp4','descent-overview.png','energy-diagnostics.png','output-audit.json'):
 shutil.copyfile(run/name,dest/name)
for name in ('frame_00000.png','frame_00039.png','frame_00077.png'):
 shutil.copyfile(run/'rendered-frames'/name,dest/name)
(dest/'support').mkdir()
shutil.copyfile(ROOT/'scripts/plot-wang2017-descent.py',dest/'support/plot-wang2017-descent.py')
shutil.copyfile(ROOT/'scripts/plot_m5_cliff_comparison.py',dest/'support/plot_m5_cliff_comparison.py')
shutil.copyfile(__file__,dest/'support'/Path(__file__).name)
shutil.copyfile(Path(str(run)+'-video-fixed-scale.log'),dest/'render.log')
(dest/'media-verification.json').write_text(json.dumps({'fullDecodePassed':True,'archivedNativeVTKHashesMatched':verified,'probe':probe,'physicalTimeS':15.4,'playbackDurationS':19.5,'nativeComplete':False,'scientificValidation':False,'fixedColourAndSpatialBounds':True,'displacementScale':1,'interpolatedStates':False},indent=2)+'\n')
(dest/'README.md').write_text('# Partial actual Wang Soil1 video\n\n78 native saved frames0–15.4s; last saved state precedes the failed substep. Loading0.005m/s=50x paper. Playback4fps/19.5s, no displacement amplification or interpolated states. Native mc-kappa is accumulated equivalent plastic strain, not damage or Wang Soil2 history. Fixed spatial/colour bounds. INCOMPLETE title retained; native failed/full physical target not reached.\n\nAll78 input VTK hashes match the immutable raw failure archive. H264/yuv420p1680x756;78 decoded frames and full decode PASS. Saved-output consistency passes only available checks; no scientific/paper-curve validation. Exact rendering scripts and sample frames retained.\n',encoding='utf-8')
entries=[dict(path=p.relative_to(dest).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'evidence-manifest.json').write_text(json.dumps({'entries':entries},indent=2)+'\n')
assert all(hashlib.sha256((dest/e['path']).read_bytes()).hexdigest()==e['sha256'] for e in entries)
print(json.dumps({'verifiedArtifacts':len(entries),'videoBytes':(dest/'slope-descent.mp4').stat().st_size}))
