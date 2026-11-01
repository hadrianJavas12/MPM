---
title: Clay60 adaptive kinematics
type: synthesis
tags: [cl-mpm, numerics, clay]
sources: [docs/AI_HANDOVER.md, docs/benchmarks/CLAY_SINGLE_SLOPE60.md]
updated: 2026-11-01
---

# Clay60 adaptive kinematics

The previous corrected-domain trial stopped at5.304s with det(dF)<0 and severe accumulated F distortion. The new opt-in USF simulation selects dt from current mapped nodal speed, elastic bound and actual particle velocity gradients before stress/history updates. It bounds norm-infinity(dtL) by.1 and recomputes end-step gravity. Original physical model and guards retained. Tests: failed tensor arithmetic,13517MP native grid bound,one selection per step,4paired USF parity updates plus2highspeed USF steps passed. Manufactured compression halving convergence is not full-slope convergence. Fresh8s trial prepared; late distortion/runout remain unvalidated. See [[clay60-worker-domain]] and [[cl-mpm]].

1Nov17:23WIB: fresh adaptive trial launched source8fc1da88. Actual13517MP/frame0/316sourceDLL/newadaptiveASDFload proof PASS;full8s outcome pending.34hwall deadline3Nov03:23WIB+2hmedia,budgetnotETA. Quiet15min finite monitor and frozen3movie autoexport active.
