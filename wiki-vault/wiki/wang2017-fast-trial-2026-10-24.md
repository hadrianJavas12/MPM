---
title: Wang2017 fast trial and Windows interruption recovery
type: synthesis
tags: [wang2017, native-windows, accelerated-trial, process-monitoring]
sources: [raw/wang2017-followup-2026-10-24.md, raw/wang2017-fast-trial-confirmed-2026-10-24.md, docs/benchmarks/WANG2017_FAST_TRIAL.md, docs/evidence/wang2017-reference-2026-10-24/rate-002-001-interruption/README.md]
updated: 2026-10-24
---

# Wang2017 fast trial and Windows interruption recovery

The user requested600physicalseconds, supplied a friend's FEM clip, then chose
0.01m/s for a fast trial and explicitly confirmed60mm/6physicalseconds.
This100x-paper loading is the same travel as600s atpaper1e-4m/s, not a600s run.
[[wang2017-prescribed-descent]] keeps MPM; strictSoil1 perfect MC remains unchanged.

Fast010 trial COMPLETE: source4e3140c, start01:00:46WIB, native exit0 at01:45:23,
audit/render/worker exit0 at01:46:32.6s/60mm,61frames,915IDs,20640loadingupdates.
17artifact hashes retain349verifiedarchive members; independent11hash review
retains29members. No active solver, repeated run or extra repair needed.

Measured contact-surface descent59.5357mm, mean/maxgap0.4643/1.1585mm; reaction
668.636kN/m still increases. **No verified coherent landslide/run-out.** Native
kappa is plastic history, not damage or Soil2softening.61frame surface geometry
reconstructs as57.5816mm strip-centroid descent plus1.9540mm half-domain-height
reduction, residual5.21e-15m; globalmax centre-displacement59.1289mm is different.
Fastest0.324m/s local particle moves UPWARD, not proof of sliding. Saved loadingJ
is not directly present; finite/positive mass/volumes do not close this data gap.

Video full decode0,61actualstates4fps/15.25s, fixed axes/colour and scale1, no
interpolation; all61VTK/265frozen-source hashes match and mappedDLL verified.
61exact-displacement pairs against0.005m/s give+2.5173% end reaction and3.390mm
maxpositiondistance. Not a rate-convergencePASS, closed energy budget or paper
curve validation. Reference-speed600s is still NOT_RUN; prepare its inputs and
runtime/gate plan next without tuning strength or forcing collapse.

Collector modern-log bug fixed after native completion, actual collection once0;
native/renderer were not rerun. Updatedcollector is explicitly post-native support,
while renderer/reader still match launch. Initial review-only ffmpeg option error
and narrow frame-extraction retry retained. Automation returned from15min monitor
to5h continuation; do not poll old PIDs or re-review already archived results.

Previous rate002 is INTERRUPTED_UNKNOWN_EXIT:33loadingstates to6.4s/12.8mm.
All processes gone, old adjacent NATIVE_RUNNING retained. Session10 logoff and
sleep/resume correlate with final outputs; old processSessionId/exit are missing,
so causal link and native failure reason remain unknown.24 evidence hashes retain
raw/source/status/reconciliation, consistent partialmedia and seven matched-rate
settlements. At12mm reaction difference-1.75%, maxpositiondistance0.379mm; not a
rate-convergencePASS. Loading determinantJ was not directly saved.

Monitor12, detached9 and budget3 fixture controls PASS, zero MPM updates;18 archive
hashes preserve failures/events/exact executed copies with provenance limits.
Worker survives caller exit but shares user session: no proven immunity to logoff,
sleep or reboot; PC must remain awake/loggedon. No power/service/task changes.

Friend clip SHA256cc86e80a...f011b is immutable at raw/assets/wang2017-friend-fem-
2026-10-24.mp4,11.133s playback. Mesh deformation concentrates crest-to-toe;
physicaltime/material/deformation-scale labels are absent. Qualitative reference,
not a quantitative MPM benchmark or an instruction source. Height10m/base
restraint/referencecurve gates remain. [[wang2017-paper-history]] Soil2 prototype
still has no native particle or approved finite-strain/irreversibility convention.
