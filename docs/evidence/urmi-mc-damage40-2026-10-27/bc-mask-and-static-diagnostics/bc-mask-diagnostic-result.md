# Boundary-mask finding,27October2026

FIRST executed nodal diagnostic `bc-mask-002` exited0 at15:37:51WIB:
four groups,0MPM updates,0material calls,ONE initial P2G. The actual unchanged
6714MP geometry has324fixed BC objects on320boundary nodes. All305frozen
source/input/runtime records hash-match, and all305before/after hashes match.
The actual mapped DLL is57c4c9a6cedb1ade1202914074dab942afc2f15abb114637619ca3cb5d9f074f.
Six named geometry/BC/core/scheduler source hashes match failed full001.

Original `bc-mask-001` exited1 before the diagnostic body because this new
harness used an unexported NODE-POSITION symbol with a single colon. Its
source/runtime/reader error/command/exit remain retained. Only two package
qualifications changed before fresh002; no physics or production fix.

## What the native test proves

At an actual bottom corner, side BC then bottom BC leaves cached node-bcs
`(0,1,1)` while the independent union is`(0,0,1)`. Applying bottom then side
leaves the correct union. In BOTH orders the actual constrained x/y velocities
are zero. Native reset-node retains the incorrect cached mask. Thus physical
constraint enforcement and cached diagnostic classification are distinct.

Exactly16predeclared cold-mask passes per worker count were executed once:

| Workers | Passes | Wrong positive-mass masks | Added free mass | Physical constraint violations |
|---|---:|---:|---:|---:|
|1|16|0|0|0|
|4|16|14passes|108.344847629kg/m on each affected pass|0|

The affected actual positive-mass node was the bottom-right corner(60,0).
Two top-corner cached-mask mismatches occurred in every serial pass too, but
their initial P2G mass is0and they were inactive. Both bottom corners have
initial mapped mass108.344847629kg/m. This is consistent with the independently
retained worker benchmark free-mass discrepancy108.34484879kg/m after its
short deformation history; it is not a claim that their deformed nodal states
were saved or exactly reconstructed.

Source mechanism: `bc-fixed` initializes node-bcs only whenNIL, outside its
velocity/force mutex, and later BCs do not merge constrained directions.
The exact recipe uses make-outside-bc-var, retaining overlapping corner BCs;
apply-essential-bcs schedules that vector in parallel. Native reset-node does
not clear the mask. P2G mass increments themselves use node mutexes; owned
RF/KE reductions are serial and consume the cached mask after stage barriers.

## Quantitative synthetic classification witness

Explicit prescribed raw pre-essential forces give RF0.559016994375 with the
wrong mask versus0.25 with the union. KE stays6J/m, but free mass changes
111.344847629→3kg/m and RK0.000549490830349→0.0203943242596. These are a
two-node analytical fixture using actual initial corner mass, NOT measured
full001 forces/velocities or the physical equilibrium error of that run.

## Limits and next action

This establishes the mask defect and explains a credible mechanism for the
parallel benchmark observer difference. It does NOT establish the cause of
serial full001's RF0.00013149719037753823 at the declared20s preparation cap.
Serial active masks were correct in the initial geometry fixture; terminal
full001 nodal masks/forces were not retained. The old1vs4comparison remains
FAILED at its unchanged1e-11limits, including its separate stress differences.

A narrow new owned observer can cache the union derived from actual BC
directions, rejecting unsupported BC types, without changing global engine
defaults or actual physical constraints. This would require its own review
and targeted controls. No production patch, full restart, tolerance change,
strength adjustment or longer preparation was performed by this diagnostic.

Raw evidence: `output/urmi-mc-damage40-2026-10-27/bc-mask-001` and002,
their adjacent invocation/stdout/stderr/exit records,002result.json and
root-source-verification.json. Keep both attempts and their exact sources.
