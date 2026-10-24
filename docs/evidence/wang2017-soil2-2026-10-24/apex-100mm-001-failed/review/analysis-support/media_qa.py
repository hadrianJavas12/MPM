"""Inspect and fully decode the one actual partial video; no native computation."""
from pathlib import Path
import json
import shutil
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/apex-100mm-001"
OUT=RUN.with_name(RUN.name+"-review")
video=RUN/"slope-descent.mp4"
probe=subprocess.run([shutil.which("ffprobe"),"-v","error","-count_frames","-select_streams","v:0",
                      "-show_entries","stream=codec_name,width,height,pix_fmt,r_frame_rate,duration,nb_read_frames",
                      "-of","json",str(video)],capture_output=True,text=True,check=True)
(OUT/"video-probe.json").write_text(probe.stdout,encoding="utf-8")
times=subprocess.run([shutil.which("ffprobe"),"-v","error","-select_streams","v:0","-show_frames",
                      "-show_entries","frame=best_effort_timestamp_time","-of","json",str(video)],capture_output=True,text=True,check=True)
(OUT/"video-frame-timestamps.json").write_text(times.stdout,encoding="utf-8")
with (OUT/"video-decode.log").open("w",encoding="utf-8") as stream:
    decode=subprocess.run([shutil.which("ffmpeg"),"-v","error","-i",str(video),"-f","null","-"],stdout=stream,stderr=subprocess.STDOUT)
(OUT/"video-decode-status.json").write_text(json.dumps({"scope":"Full video decode only, not native completion or scientific validation","decodeExit":decode.returncode},indent=2)+"\n",encoding="utf-8")
stream=json.loads(probe.stdout)["streams"][0]
pts=[float(r["best_effort_timestamp_time"]) for r in json.loads(times.stdout)["frames"]]
assert len(pts)==int(stream["nb_read_frames"])==91 and decode.returncode==0
assert np.allclose(np.diff(pts),.25,rtol=0,atol=1e-12)
audit=json.loads((RUN/"output-audit.json").read_text())
assert audit["visualization"]["displacementScale"]==1 and not audit["visualization"]["interpolatedStates"]
result={"scope":"Actual incomplete saved native states; no scientific-validation claim",
        "nativeStates":91,"nativeTimeRangeS":[0,9],"nativeCommandRangeM":[0,.09],"savedPhysicalIntervalS":.1,
        "videoFrames":91,"videoFps":4,"durationS":float(stream["duration"]),"firstPtsS":pts[0],"lastPtsS":pts[-1],
        "nativeToVideoIntervalFactor":2.5,"lastFrameHoldS":.25,"spatialDisplacementScale":1,"interpolation":False,
        "fixedAxesAndColour":audit["visualization"],"codec":stream["codec_name"],"pixelFormat":stream["pix_fmt"],
        "width":stream["width"],"height":stream["height"],"fullDecodeExitCode":decode.returncode,"rendererExitCode":2,
        "interpretation":"Each actual .1s native interval is shown for .25s; actual native time labels, no real-time playback claim"}
(OUT/"media-qa.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
