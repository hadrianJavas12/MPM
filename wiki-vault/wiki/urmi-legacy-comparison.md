---
title: Urmi legacy collapse scope comparison
type: synthesis
tags: [mpm, urmi, landslide, evidence-scope]
sources: [docs/benchmarks/URMI_LEGACY_COMPARISON.md, docs/Prediction of retrogressive landslide in sensitive clays.pdf]
updated: 2026-10-26
---

# Urmi legacy collapse scope comparison

The retained legacy H/HS cases have a72degree face,2.5x2.5m notch,4m soil
foundation and elastic-only initialization followed by plastic activation and
state resets. They differ from [[unnotched-mc-gravity]] and do not establish
unnotched failure. Filtered summary metrics omit extreme particle trajectories;
raw data/media remain intact and whole-run integrity is not established.

The actual Urmi paper uses stable drained elastoplastic MC initialization,
then undrained parameters/softening. Mainly elastic response does not authorize
disabling plasticity. This is a separate future hypothesis requiring parameter,
equilibrium and state-transfer contracts, not a hidden current model change.

The source/data/paper audit is in
[repository comparison](../../docs/benchmarks/URMI_LEGACY_COMPARISON.md).
No legacy simulation, audit or rendering was repeated for that comparison.
