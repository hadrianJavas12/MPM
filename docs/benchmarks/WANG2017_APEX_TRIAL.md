# Soil2 with explicit apex flow: completed 60 mm trial

[The scoped residual-history repair](WANG2017_RESIDUAL_HISTORY_SCOPE.md) now
records the actual 100 mm failure, one replay, unchanged-tolerance prefix FAIL
and the separate opt-in continuation policy with its native verification.

**100mm follow-up:** native/worker exit1 at24October15:55:34WIB on3caa6be,
before wallbudget. Last saved9s/90mm/30960accepted loading updates; failure
manifest31092 includes later unsaved work. The actual composite-apex capsule
rejects signed-history decrease.03187108863369348→.03187108746386819; both are
past residual.02. One new frozen replay and saved-output/partial-media review
are underway; no tolerance or material change has been applied. Exact failed
solver time/particleID are absent from the capsule. This is not a completed10s
or a verified landslide. The completed60mm evidence below remains unchanged.

On24October2026 the Windows-native run
`output/wang2017-soil2-2026-10-24/apex-fast-010-001` completed at13:33:43WIB
on source55bc85d9d4567b6677439846035127751fbc4c7f. Audit/render and detached
worker exited0 at13:34:44. Native complete=true,6s physical time,60mm commanded
descent,61 saved states,915 particles,20640 loading updates. Gravity converged
after3400 updates. No duplicate solver or render was needed.

This is the [explicit volumetric apex-flow experiment](WANG2017_APEX_FLOW.md),
not the strict law or an exact paper reproduction. It keeps0.01m/s,100times
paper speed, and all numerical strength/geometry/grid/BC/damping inputs of the
strict trial. The apex convention changes the material response and is labeled
in native metadata and media. Strict failure evidence remains unchanged.

The final manifest reports reaction642.296777kN/m, measured contact-surface
descent59.553961mm, zero mass error and finite final fields. Root inspected
`descent-overview.png` and `energy-diagnostics.png`: actual geometry stays close
to its initial shape at displacement scale1, while reaction keeps increasing.
Neither native completion nor the rising kinetic proxy proves a landslide.

Independent saved-state review confirms61 states/915 stable IDs,55815 material
and366 contact rows, finite fields, constant mass and positive J. The actual J
range is0.987073696–1.002542895. F/J/volume, tensor-history/cohesion, proper
rotation and contact identities agree to recorded floating-point residuals.

| Actual saved-data observation | Result |
| --- | ---: |
| Maximum paper kps |0.017506169 |
| Minimum cohesion |16.870373kPa, above15kPa residual |
| Sampled apex-active particles |1: ID627 at5.8,5.9,6.0s |
| Maximum accumulated plastic volume strain |0.000728068207 |
| Ep-trace / plastic-volume residual |8.32e-15 |
| Free above-base particles, excluding6 driven |509 |
| Their centroid movement |+2.106mmX /−18.521mmY |
| Their mean final velocity |(+0.0005949,−0.0021849)m/s |
| Free upper-slope mass beyond original toe |0 |
|95th-percentile front advance |5.805mm |

The fastest particle797 moves upward, vy+0.3134m/s. Reaction increases on every
saved interval; there is no post-peak drop or verified coherent failure/run-out.
The physical objective remains unfulfilled. Native completion and local
softening/apex activation do not establish a scientific/landslide PASS.

Volume diagnostics need their stated sampling convention: exported trial
volume increment is current-minus-committed and is zero after each saved loadstep
commit. Accumulated volume changes prove evolution; zero exported trial increment
does not prove zero apex flow. Flags sample only the last return at saved times,
not every internal integration event. Volume strain is not porosity or det(Fp).

All58 exact shared strict snapshots through5.7s have zero reaction/displacement/
kps/cohesion deltas before sampled apex activation. Against completed Soil1's
61 states, final reaction is3.9392% lower and maximum displacement-field
difference3.28313mm. This is a material comparison, not convergence evidence.

The [completed packet](../evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-completed/README.md)
retains24 artifact hashes/361 verified archive members,275 frozen source files,
actual copiedDLL proof, all raw CSV/VTK, adjacent logs and media. The separate
[physical review](../evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-review/README.md)
retains exact analysis inputs/scripts/results and the next-study rationale.
[Video](../evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-completed/slope-descent.mp4):
61 actual states,4fps,15.25s playback, H264/yuv420p, scale1/no interpolation;
full ffmpeg decode exits0 with an empty error log. Root inspected the actual
overview, energy figure and original paper-page renders.

The next loading study follows the still-rising reaction and uncompleted
softening: continue the same material/rate to100mm/10s before considering a
hold. The retained printed-page180 image verifies Figure3's0–0.10m axis and
an approximate600kN plateau from about0.05m for Soil1. It does not establish
the Soil2 endpoint or a large-runout time history.100mm remains a declared
comparison target for this Soil2 extension, not a verified failure datum.
The new declarative case is `cases/benchmarks/wang2017-soil2-apex-100mm.lisp`.
Native input-only3 groups pass with zero physical updates: only target travel,
derived duration and frame count change; material, geometry, BC, rate, timestep,
damping, penalty and45000update cap remain identical.101 frames retain nominal
0.1s cadence, but floating-point frame-time rounding requires an actual common
prefix comparison; bit identity is not assumed. No old suites were repeated.

The previous native run took85m11s. A simple10/6 projection is about142min;
the new wall cap is3h, not a completion promise. A fresh full run is necessary:
saved VTKs do not contain a verified full-state restart. If100mm remains
pre-peak, resolve geometry and rate/mesh sensitivity rather than endlessly
extending travel or reducing strength to force a collapse.
A stationary strip hold is also extra loading history and can release penalty
spring energy; it does not by itself establish natural creep or zero energy input.
Relief10m is a declared case assumption, not a recovered paper value. Reference
curve, bottom tangential restraint, rate/mesh sensitivity and finite-strain
interpretation remain limitations.

## 100mm endpoint launch and Windows command

Checkpoint3caa6be is committed/pushed. The fresh100mm case started
**24October13:52:42WIB** in `output/wang2017-soil2-2026-10-24/apex-100mm-001`;
initial native RUNNING, full physical outcome pending.3h cap until16:52:42WIB.
Use a fresh directory for any separately justified run; do not duplicate it:

```powershell
Set-Location D:\MPM
pwsh -NoProfile -File .\scripts\start-wang2017-detached.ps1 `
  -Case cases/benchmarks/wang2017-soil2-apex-100mm.lisp `
  -OutputDirectory output/wang2017-soil2-2026-10-24/apex-100mm-001 `
  -MaxWallHours 3
```

Worker31296/wrapper38252/cmd25892/SBCL27304 run in user Session11. This does not
prove logoff/sleep/reboot survival. The same monitor checks15min, quiet while
healthy; automatic native audit/render/video follow completion. No further
strength, rate or constitutive change is part of this endpoint experiment.

Launch-only `apex-100mm-launch/` retains6 verified artifact hashes/292 decoded
ZIP members,275 frozen sources matching manifest/workspace, actual copiedDLL,
3 postprocessor hashes and one process-chain identity observation. Runtime
proof was initially unavailable; the later authorized capture preserves this
history and only establishes launch provenance, not completion or a landslide.
