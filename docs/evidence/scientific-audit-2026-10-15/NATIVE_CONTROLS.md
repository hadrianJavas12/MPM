# Bounded Windows native controls, 2026-10-15

HEAD: `8549c32bb53b69e6cbbb93246b412084eab9a2c1`. Runtime: native Windows SBCL 2.6.9 through `windows\cl-mpm.cmd`, configured Quicklisp/local libraries, one engine worker. No production definition was replaced, and no accepted/full simulation was rerun.

Run from `D:\MPM`:

```powershell
& .\windows\cl-mpm.cmd output\scientific-audit-2026-10-15\native-invariant-controls.lisp
```

The final run exited 0 and printed `AUDIT NATIVE CONTROLS COMPLETE`; assertions passed. The final log has one harmless existing unused-`dt` style warning from inlining native strain assembly. The script, final log and JSON outcomes are alongside this note. A setup-only failure log is preserved: the initial harness initialized lparallel without the engine's separate workers, so it failed with `no workers` before either diagnostic. The harness now uses `cl-mpm/utils::set-workers 1`. The pre-distance-label-fix log preserves an intermediate successful run whose reported distance was the engine's squared norm; the final output reports 9 m and separately records squared norm 81 m².

## A. Disconnected aggregate support: reproduced

Explicit native occupancy flags describe a partial cell `[1,2] × [1,2]` and a full cell `[10,11] × [1,2]` on a 1 m mesh, with an 8 m empty gap. Four nodes of each occupied cell are active. This is an algebraic occupancy diagnostic; no MPs were dynamically evolved or mapped to set those flags.

The genuine `get-closest-cell` found zero eligible candidates in its local patch and returned cell `(10 1 0)`, whose centroid is 9 m from the fragment centroid. Genuine `locate-aggregate-nodes` then assigned all four fragment nodes to that remote support. Both genuine `assemble-e` and production `assemble-sparse-e` agreed within 1e-12. The resulting 8 × 4 extension matrix includes fragment rows `[10,0,-9,0]`, `[0,10,0,-9]`, `[9,0,-8,0]`, `[0,9,0,-8]`; its maximum absolute coefficient is 10.

All row sums are exactly 1, so the matrix reproduces a global unit translation. However, imposing that unit translation on the remote support necessarily extends the same displacement into the disconnected fragment; there are no independent fragment degrees of freedom in this matrix. Thus partition of unity does not rule out cross-gap coupling. This demonstrates a native support-search/coupling failure mode for disconnected occupancy, not its incidence or contribution in the accepted collapse.

Relevant source: `src/aggregate.lisp:180` (`get-closest-cell`), `:223` (fallback traversal), `:308` (`locate-aggregate-nodes`), `:364` (support assignment), `:527` (dense E), `:564` (sparse E). Neither local nor fallback eligibility tests enforce an occupied connected component; the fallback also has no maximum distance.

## B. Fbar volume/stored-F/domain Jacobians: reproduced

A 6 × 6 m native 2D GIMP mesh at h = 1 m contains one MP at `(2.9,2.7)`, initial domain `0.8 × 0.8`, V₀ = 0.64, F₀ = I. All nodes are active with prescribed nonuniform displacements `uₓ = 0.02xy`, `uᵧ = −0.01xy`. Native cached GIMP iteration uses 9 nodes. The script invokes genuine `calculate-strain-rate-disp`, `update-strain-kirchoff` and `update-domain-det`. It does not invoke a constitutive model or advance a dynamic solver.

| Control | V/V₀ | det(stored F) | domain area/domain area₀ |
| --- | ---: | ---: | ---: |
| Fbar ON | 1.025 | 1.02375 | 1.02375 |
| Fbar OFF | 1.025 | 1.025 | 1.025 |

The ON mismatch is −0.00125 in Jacobian units (about −0.122% relative to the volume ratio); the OFF mismatch is zero. Domain area agrees with the stored-F determinant to floating-point tolerance in both cases. The actual normal and Fbar gradients, F matrices and ratios are preserved in JSON.

Relevant source: `src/core/stress-update.lisp:40` (native displacement assembly), `:115` (`calculate-df`), `:181`–`:206` (Fbar strain increment scaling), `:272` (stored F uses strain increment), `:276` (volume uses unmodified increment), `:298` (Kirchhoff-to-Cauchy conversion uses stored detF); `src/core/domain-update.lisp:495` (`update-domain-det`).

Using separate physical and constitutive Fbar Jacobians can be a deliberate numerical convention. This control demonstrates that the current stored F/domain do not describe the same area change as stored physical V under this nonuniform displacement. Its consequences for Cauchy stress, particle-domain integration and energy require an explicit numerical contract and validation. It does not by itself prove an incorrect accepted result, quantify the accepted-run mismatch, or validate any damage/fracture/collapse physics.
