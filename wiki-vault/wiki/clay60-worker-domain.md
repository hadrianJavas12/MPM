---
title: Clay60 worker domain correction
type: synthesis
tags: [cl-mpm, numerics, clay]
sources: [docs/AI_HANDOVER.md, docs/benchmarks/CLAY_SINGLE_SLOPE60.md]
updated: 2026-10-31
---

# Clay60 worker domain correction

Caller thread dynamic volume-domain binding did not reach the actual worker. The new scenario particle method selects guarded volume domains explicitly; prior declaration alone did not prove runtime activation. Five tensor controls and two native USF steps passed. Motion movies now use accumulated equivalent J2 plastic strain with a fixed scale across all saved states. A fresh8s run is being prepared; completion and physical validation remain unproven. See [[clay60-monitor-recovery]] and [[cl-mpm]].

31Oct01:57WIB: corrected run launched,source d428e1a2. Actual startup13517MP/frame0/315sources/DLL PASS; target8s17states pending. Wall deadline1Nov11:57WIB plus2h export, budgetnotETA. Frozen automatic media watcher and15min heartbeat active; terminal verification/delivery/archive pending.

## Terminal31Oct12:25WIB
Native failed5.3041s/5634updates;eleven states0..5s and3actualmovies delivered. Corrected domain advanced beyond old3s failure, but actual ID7699 detDF=-14.71218 triggered unchanged guard. Saved F singularmax656 at5s and11536 at failure near rightboundary. Savedintegrity/source/DLL PASS is not validatedrunout: distorted physical patches extend beyond grid; KE unsettled. No native rerun. Terminal archive includes actualsource/runtime/raw/adjacent/detached/preparation/media and saved-only audit. See [[clay60-monitor-recovery]] and repositoryhandover.
