# Native unnotched MC gravity study

Updated 25 October 2026: the first full SRF1.40 attempt failed during the gravity
ramp. Its retained data does not establish a landslide. One original-source
replay identifies a negative-multiplier acceptance defect; a scoped numerical
check is implemented; existing34 material tests, eight focused new groups and
four bounded MPM/output groups pass. A fresh full continuation has not started
at this checkpoint. See the
[journal-method decision](UNNOTCHED_LANDSLIDE_METHOD_SELECTION.md) and
[frozen study contract](../../research/references/unnotched-mc-ssr/contract.json).

## Experiment and limits

Two independent cases use the existing perfect-plastic, Cauchy-strength MC
material at SRF1 and1.40. Only cohesion and tan(friction) are reduced. SRF1.40
is a critical-bracket trial, not a guaranteed unstable control.

The initial polygon is `(0,0),(32,0),(12,10),(0,10)`m, with empty grid to80m
horizontally and15m vertically. This is a GL D1-inspired adaptation; full Xie
Figure7 geometry has not been visually verified. There is no notch, excavation,
weak seed, driver or hidden wall release. Zero initial stress/velocity and
active plasticity are retained throughout a smoothstep gravity ramp0–2s, then
constant gravity to6s. Actual `sim-gravity` changes; no reporting reset erases
ramp motion. Numerics:1m cells,2MPs/axis,USF/FLIP,dt-scale0.2,one worker,
mass-scale1,no damping/F-bar/splitting/removal. This is a coarse explicit
mechanism study, not the implicit B-spline/F-bar/36PPC paper calculation.

Left/right x rollers, fixed x/y grid bottom and free top are explicit. A fixed
bottom is not Coulomb bed contact. Floor penetration, boundary proximity,
ramp inertia, grid/PPC/dt sensitivity and locking limit quantitative runout
or factor-of-safety claims. Gravity work varies during the ramp; a naive
constant-gravity energy sum is not a closed energy budget.

## Ownership and execution

At the initial additive checkpoint the existing material and solver were
unchanged; the later scoped numerical acceptance repair is documented below.
Six short files under
`scenarios/gravity-slope/` own configuration, geometry, measurements, advancement
and compatibility. The cases contain component assignments. The scenario
inherits only an existing read-only free-force residual diagnostic; it does
not build the Wang actuator or run its procedure.

First run the focused native gate in a fresh directory:

```powershell
cd D:\MPM
.\windows\cl-mpm.cmd tests\benchmarks\gravity-slope-controls.lisp output\unnotched-gravity-2026-10-24\native-controls-001
```

This freezes the driver, both actual cases, contract, project sources and mapped
DLL before project loading. It checks reduction, polygon/BC/ramp and exactly
two genuine MPM updates with independent saved VTK/CSV readback. It does not
establish slope failure. Preserve failed attempts; saved-output checks can be
repaired without repeating solver updates.

Only after gates and a measured runtime pilot, launch a fresh trial:

```powershell
.\scripts\start-gravity-slope.ps1 -Case cases/benchmarks/gravity-slope-mc-srf-1.lisp -OutputDirectory output/unnotched-gravity-2026-10-24/srf1-001 -MaxWallHours 3
.\scripts\start-gravity-slope.ps1 -Case cases/benchmarks/gravity-slope-mc-srf-1p4.lisp -OutputDirectory output/unnotched-gravity-2026-10-24/srf1p4-001 -MaxWallHours 3
```

Run the pair sequentially for comparable single-worker cost; these commands
are documentation, not automatic launches. The thin alias reuses the existing
CIM launcher while preserving its old Wang default. A separate native monitor
records actual exit, deadline and process identities; completion is labelled
`NATIVE_COMPLETE_REVIEW_PENDING`. WMI remains in a user session; logoff/sleep/
reboot survival is unproven. Snapshots are evidence, not full restart state.
Historical output paths above already retain evidence; choose a new unused
suffix for another run. The launcher rejects reuse rather than overwriting it.

Native output: `manifest.json`, `history.csv`, `particles.csv` and actual
`vtk/particles_####.vtk`. Per-ID CSV includes initial positions, F9/J, physical
stress6, mass/volume, velocity, history/strength and boundary observations. IDs
are captured vector indices, with particle identity/order/count/mass checks.

## Verification chronology

At the implementation checkpoint, native input/output gates, runtime pilot and
paired physical results are **NOT_RUN**. Separate process-monitor fixtures
exercise supervision with zero MPM updates. Static syntax is not native proof.
Later dated findings must retain that distinction and all negative evidence.

Physical review uses the predeclared fixed cohort, connected moving mass and
sustained motion convention, inspecting scale1 geometry/plastic localisation.
Report initial-to-final and post-ramp response separately, and toe crossing as
a separate runout gate. Solver completion, plastic colour or one fast particle
does not prove a landslide. No automatic scientific PASS is produced.

### Native gate closure, 24 October 2026

Source2308a1e attempt001 passes inputs/invalid-inputs/geometry/boundary/ramp,
then exits1 because its main-thread-only dynamic counter is invisible to the
constitutive worker. Two genuine updates and three saved states remain valid;
this is a harness failure, not disabled material physics. Attempt002 fixes only
the shared, mutex-protected test counters and skips those five passed groups.
Runner/CSV/VTK/read-only all pass:1760attempted=accepted material calls, two
updates,880MPs,2640material rows and three VTKs. Both285-file source snapshots
match before/after; actual mapped DLL is verified. All three VTKs and both CSVs
from001 and002 are byte-identical. No production numerical source changed.

Independent Python readback of002 passes finite/mass/IDs/F/J/volume/law/yield,
CSV/VTK identities, initial complete polygon and saved gravity schedule. Its
selected frozen projection matches the source manifest hash/length. Root
visually inspected its scale1 PNG. The original001 review is retained with its
honestly labelled workspace-constant fallback; its earlier analysis source
version was not separately saved.002 retains its exact executed script. A later
metadata-only addition records the imported VTK reader hash for future reviews;
it does not alter numerical audit/thresholds or require repeating solver gates.
These tiny elastic states do not test slope instability or plastic-flow cost.

The native runner took0.568538s for construction/two updates/three rich saved
states. Initial stable dt is0.0007784618025300353s; a constant-initial-dt6s
extrapolation gives7708updates. The rough wall extrapolation is not an ETA:
plastic cost and evolving timestep remain unknown. A bounded3h wall budget is
declared for the first6s SRF1.40 trial; baseline SRF1 follows sequentially.
See [runtime rationale](../../research/references/unnotched-mc-ssr/runtime-plan.json).

Thirteen new synthetic monitor assertions pass with zero MPM updates. New alias
detachment/paths/exit/proof controls pass9assertions plus2default-selection
checks in002. Fixture001 expired its60s release timer before delayed verifier
invocation (exit8); preserve it rather than claiming it passed or was a native
failure. No logoff/sleep/reboot guarantee follows from these tests.

### First full trial and original-source replay, 24–25 October 2026

The first SRF1.40 attempt, `srf1p4-001` on source `a4de3e6`, exits native1 at
22:42:34WIB on24October, during the gravity ramp. Ten actual saved states cover
0–0.9s,880 fixed particle IDs and8800 material CSV rows. The manifest records
1265 accepted updates including work after the last saved state, and attempted
time0.980934788134821s. Saved0.9s is not the exact failed time. The6s duration,
post2s hold and predeclared1s persistence windows were not reached.

The saved-state review passes finite/mass/IDs/F/J/volume/material-law/yield and
CSV–VTK consistency. Maximum saved displacement is3.29489mm, maximum speed
0.00719495m/s and zero mass crosses the toe. These early small displacements
do not prove coherent failure; unavailable persistence/hold windows are
`NOT_EVALUATED`. The incomplete scale1 video contains10 actual states at4fps,
without interpolation or amplified motion, and full decode exits0.

[The retained failure packet](../evidence/unnotched-gravity-2026-10-24/srf1p4-001-failed/README.md)
contains51 indexed artifacts and909 verified ZIP members, including original
raw/source/runtime/media, exact analysis support, both replay attempts and the
read-only analytical note. A late launch-proof capture is explicitly
`INCOMPLETE_CAPTURE`; it did not reconstruct a live PID after native exit.

Replay001 fails in a helper-name/package-lock fixture before any projection
call. Its source and log remain retained. Replay002 performs **one** unchanged
production principal return, zero MPM updates, and reproduces the original
ambiguity. All283 frozen sources match before/after; six MC modules and the
mapped DLL match the failed-run bytes. Observation wrappers restore every
original return and are removed afterward. Whole-MPM/particle rollback is
`NOT_EXECUTED` from this pure-input capsule.

The ordinary face candidate has nonnegative multipliers and satisfies all six
yield inequalities. A second accepted edge candidate has a negative multiplier
`-7.313031007122379e-13`, admitted by the absolute1e-12 allowance. Its stress
effect5.625408467e-5Pa is32.42 times the existing1.734967080e-6Pa stress
tolerance; its plane-residual effect is larger still. Face/edge stress distance
exceeds the existing deduplication radius, so the ambiguity guard rejects the
step. Positive total work does not make that negative multiplier admissible.
This is a numerical complementarity defect, not evidence that two physically
valid perfect-MC returns exist. The analytical Schur-complement calculation
and retained native candidate records establish the distinction for this state.

### Scoped acceptance repair and current gates, 25 October 2026

Only the base MC-evolution `project-principal` adds a conservative backward
stress-error check after the original shared admissibility predicate:

```text
sum over lambda_j < 0:
  abs(lambda_j) * max(norm_inf(D*g_j), max_i(abs(n_i dot D*g_j)))
  <= existing stress tolerance
```

`D` uses the actual shear/bulk moduli, `g_j` the declared plastic-flow vectors
and `n_i` all six MC yield normals. The sum prevents cancellation from hiding
negative-flow effects. Nonnegative multipliers return zero without allocating
new plane arrays. No multiplier, stress, strength, history or trajectory is
clamped or altered. This extra condition only tightens allowed candidates;
all existing absolute/stress/history/dedup constants, the shared three-argument
predicate and all-roots ambiguity rejection remain unchanged. Wang point,
native and composite-apex acceptance retain their separate behavior and are
not claimed covered by this base-projector repair.

The existing material-point suite completes native exit0 with34PASS and no
failures at `output/unnotched-gravity-2026-10-25/mc-regression-001/`. Its exact
test bytes are unchanged and all283 copied source hashes verify afterward.
This is a material-point regression, not a full slope continuation.

The new frozen `complementarity-controls-001` suite completes exit0 with eight
groups: source contract, actual fixed-code case, permutations, transitions,
backward error, scaling, genuine ambiguity rejection and native rollback. It
executes61 explicit new fixed-code point calls (one actual identity, five
permutations,54 transition/scaling calls and one genuine ambiguity fixture),
one native constitutive call, zero MPM updates and zero old-baseline replays.
All284 copied files match before/after and the mapped DLL is verified.

For the captured input the new code returns the nonnegative face in original
axis order `[-73488.98698107201,-32901.247161468484,-32901.247084164526]`Pa,
kappa2.8214309790841185e-5. The false edge's conservative stress/plane error
1.125081693403443e-4Pa exceeds the unchanged tolerance1.734967079821152e-6Pa;
it is rejected. A separate genuine three-root positive-multiplier fixture still
raises ambiguity. This fixed-code regression is distinct from the one retained
original-source failure replay. The native rollback control does not establish
whole-MPM rollback for the historical capsule.

Narrow `native-output-fixed-001` completes four missing output groups, exit0:
1760 attempted=accepted native material calls, two real USF updates,880MPs,
three actual VTK states and2640 material CSV rows. All285 copied source hashes
match before/after and the mapped DLL is verified. Three particle VTKs and both
CSV files are byte-identical to the pre-fix002 elastic control. The first
comparison harness accidentally included mesh.vtk in its particle-file glob
and asserted before producing a result; that failure is retained. Only file
selection was corrected, using the saved output without another solver run.
This confirms bounded output compatibility; it does not test slope failure.

The [numerical fix/control evidence packet](../evidence/unnotched-gravity-2026-10-25/complementarity-fix-controls/README.md)
retains43 indexed artifacts/886 archive members/852 executed source entries;
root verified all hashes and44 staged Git blobs. A fresh full continuation has
not started at this checkpoint. No landslide or calibrated runout follows from
these gates. Keep the original failed run and replay as negative evidence;
any fresh full run starts from the declared initial state with unchanged study
inputs, preserving all previous attempts.

### Fresh same-input continuation, 25 October 2026

Repair/evidence checkpoint `3ed36a3` is pushed. Fresh `srf1p4-002` starts at
03:57:28WIB from the exact same SRF1.40 initial input, target6s/61states and
3h wall budget to06:57:28WIB. This rerun is justified by the diagnosed and
tested complementarity repair, without changes to strength, psi, geometry,
gravity schedule, damping or timestep. Original failed output remains intact.

Actual worker/wrapper/cmd/SBCL PID, session, creation-clock and parent-chain
proof is retained. The first two proof-harness attempts handled typed dates
and CIM/Process clock precision incorrectly; their reasons are retained. The
correct proof uses each record's original clock and exact equality, without
relaxed identity checks or a solver restart. This affects no native physics.
The single automation checks every15min while active and stays quiet during
healthy progress. Saved VTK/CSV and full sources will be archived/reviewed at
terminal before the sequential SRF1 comparison. No landslide is claimed yet.

[Launch-only evidence](../evidence/unnotched-gravity-2026-10-25/srf1p4-002-launch/README.md)
retains21 indexed artifacts; root verifies all282 actual source files and22
staged Git blobs. Only projection differs from001; all281 other frozen source
files, the exact executable case and full configuration match. Full raw/source
archives and physical/media review remain due at terminal.

### Completed SRF1.40 and baseline control, 25 October 2026

SRF1.40 attempt002 completes native/worker exit0 at04:12:52WIB:6s,
61actual states/880IDs/53680 material rows/7740 updates. The independent
saved-data review/render executes once, exit0, from analysis/reader/contract
bytes copied before execution. Integrity passes;282 actual frozen sources and
mapped DLL match. Root also inspects its actual scale1 PNG. The retained video
contains61 saved states at4fps (15.25s playback), without interpolation or
amplified motion, and full decode exits0.

**No landslide is detected.** Maximum displacement over the run is12.083373mm,
maximum plastic history0.002384817. The fixed cohort moves+2.619932mmX and
-6.475881mmY over0–6s; post-ramp2–6s adds only+0.196086mmX/-0.099476mmY.
Kinetic energy peaks7.099245J/m at1.8s and falls to0.05890283J/m at6s. Both
predeclared sustained-motion windows are NOT_DETECTED and no mass crosses the
toe. MinimumJ0.998403902246/max independent yield residual1.055e-10Pa support
integrity, not instability validation. No center exits or floor penetration
occur; the minimum particle half-domain margin is-3.5951micrometres, retained
as a contact/support limitation.

The ten common0–0.9s particle VTK files and first8800particle/10history CSV
rows are exactly byte/string-identical to the original failed001 prefix;
all numeric differences are zero. The comparison script is saved before
execution. [Completed evidence](../evidence/unnotched-gravity-2026-10-25/srf1p4-002-completed/README.md)
retains45 indexed artifacts/445 archive members, including all282 native
sources, raw output, exact analysis/media/runtime and saved comparison. Root
verifies every indexed hash/archived source and46 staged Git blobs.

The predeclared sequential SRF1 control starts04:18:27WIB on source8d8b544,
target6s/61states,3h wall budget to07:18:27WIB. Current c10kPa/phi20/psi0
differs from the reduced case only in declared SRF/cohesion/friction. Exact
case/source/configuration and live process proofs are retained in
[baseline launch evidence](../evidence/unnotched-gravity-2026-10-25/srf1-001-launch/README.md):
20 indexed artifacts/282 frozen sources/21 verified staged Git blobs. The
original inline matrix-analysis source was not separately saved; that gap is
explicit. No input gates were repeated. Compare the pair before choosing a
new geometry, mesh or ramp sensitivity study; do not increase SRF or extend
duration simply to obtain collapse. Baseline results remain pending.

The [conditional post-pair study review](../../research/notes/unnotched-landslide-2026-10-24/post-pair-study-review.md)
recommends verifying source geometry and independent static stability before
an expensive refinement. All proposed diagnostics/runs remain NOT_RUN. A later
cross-mesh comparison must preregister identical physical observation regions
and thresholds; the original h-scaled observer changes when h changes and
must not silently turn a resolution change into a different success detector.

### Pair closed and static diagnostic preregistered

Baseline completes native/worker0 at25Oct04:33:41WIB,6s/61states/7740updates.
One saved review/render passes integrity/source282/DLL. Maxu7.588638mm,final
KE.00420176J/m; no coherent motion or toe runout. The53680-row same-time/ID
comparison confirms identical initial geometry/mass/cohort and onlySRF/c/phi
differences. Both trials settle. Exact analysis, data, plots and videos remain
in [baseline+paired evidence](../evidence/unnotched-gravity-2026-10-25/srf1-001-completed/README.md):
46 indexed artifacts/444 ZIP members/282sources; root verifies47 Git blobs.
No old solver/audit/render repeated; actual landslide remains unmet.

[Static reference audit](../../research/notes/unnotched-landslide-2026-10-24/static-reference-audit.md)
and [preregistered contract](../../research/references/unnotched-mc-ssr/statics-contract.json)
define an independent restricted-circle Bishop diagnostic before an expensive
refinement. Negative normals/boundary optima must be retained; no clamping,
tension-crack assumption, global-FoS or dynamic validation follows. Static
implementation/controls/search are NOT_RUN at this checkpoint.

### Static gate closes; same-strength resolution study

The [independent diagnostic](UNNOTCHED_STATIC_DIAGNOSTIC.md) now completes five
new mathematical controls and one36,006-candidate search, without MPM steps.
Formal fine minima1.383870236/SRF1 and0.988478740/SRF1.4 suggest near-critical
conditions; negative normals/restricted search prohibit validation claims.
The preregistered h0.5 study keeps all physical inputs unchanged and freezes
a common physical observer. New native resolution gates precede the full run.

### Native refinement gate, 25 October 2026

`refnative-controls-001` passes4groups/exit0: mesh-only case/config delta,
3520MP/same220m2-mass-polygon-BC,2realUSFupdates/7040accepted material calls,
3VTKs/10560CSV rows with finite/ID/F/J/volume/stress readback. All285 frozen
files before/after and mapped DLL match. [Gate evidence](../evidence/unnotched-gravity-2026-10-25/refinement-controls/README.md)
retains25 indexed artifacts/300ZIPmembers/26 independently verified Git blobs.
These tiny states establish integration, not full plastic-failure validation.

The full refined command, after this checkpoint is pushed, is:

```powershell
.\scripts\start-gravity-slope.ps1 -Case cases/benchmarks/gravity-slope-mc-srf-1p4-h05.lisp -OutputDirectory output/unnotched-gravity-2026-10-25/srf1p4-h05-001 -MaxWallHours 3
```

Native fine integrity uses `refinement-audit-contract.json`; its original
h-scaled diagnostics are separate from the common physical-metre comparison.
Full refined results remain NOT_RUN at this checkpoint. Do not rerun gates.

### Refined full run launched

Source1a9f29a starts `srf1p4-h05-001` at25Oct14:53:10WIB with3h wall budget
until17:53:10WIB. Exact live PID/session/creation/parent-chain proof is retained.
All physical inputs are unchanged; the gate above precedes this6s/61state run.
One quiet15min monitor is active. Terminal native-h-scaled integrity and the
separate common-metre comparison remain pending; no landslide claim follows.

[Refined launch evidence](../evidence/unnotched-gravity-2026-10-25/srf1p4-h05-001-launch/README.md)
retains30 indexed artifacts/282 frozen files and31 independently verified Git
blobs. All281 non-case sources match coarse1.4; only actual mesh differs.
Frozen protocols are included; observer execution was not claimed at launch.

### Terminal refinement review and observer controls

The first frozen synthetic invocation passes nine tests with exit 0. Seven
copied sources/support files match before and after execution. Controls cover
the fixed physical cohort, graph radius, displacement, persistence and toe
thresholds; equivalent coarse/fine mass; post-2s reference; contract drift and
input non-mutation. They exercise observer helpers only. No native simulation,
actual saved-run analysis, full orchestration or plotting was performed.
See [observer evidence](../evidence/unnotched-gravity-2026-10-25/refinement-observer-controls/README.md).

After the native run terminates, use a fresh output directory and run ONCE:

```powershell
.\toolchain\analysis-venv\Scripts\python.exe scripts/review-gravity-refinement.py --run-dir output/unnotched-gravity-2026-10-25/srf1p4-h05-001 --coarse-run-dir output/unnotched-gravity-2026-10-25/srf1p4-002 --output-dir output/unnotched-gravity-2026-10-25/srf1p4-h05-001/refinement-review-001 --video
```

The workflow freezes the wrapper, existing native reviewer, VTK reader and
three contracts before execution. Active native status blocks review; failed
fine integrity is retained and blocks downstream comparison. It saves the
fine h-scaled audit separately from the common physical-metre comparison.
Coarse CSV hashes must match their existing audit; coarse audit/render are
not repeated. IDs are followed within each mesh, with common initial 1 m bins
and mass-weighted distributions across meshes. Actual positions use scale 1;
video uses saved fine states without interpolation.

Inspect actual spatial localisation and coherent motion before any landslide
claim. Automatic scientific/landslide validation remains false. Analysis or
media failures retain stage evidence and use saved data for repair; they do
not justify rerunning the solver. The full workflow and refined physical
result remain NOT_RUN at this checkpoint.

### Completed h0.5 result: no verified sliding

Native and worker exit0 at25October16:56:33WIB:6s,61states,3520MPs and15471
updates. The first frozen review/render exits0 at16:58:02WIB. All282 source
hashes and the mapped DLL match; actual61-state/4fps video decodes with exit0,
uses scale1 and no interpolation. Root inspects both actual PNGs.

| Same physical observer | h1 | h0.5 |
| --- | ---: | ---: |
| Cohort count / mass | 576 /293678.269338kg/m | 2304 /293678.269338kg/m |
| Centroid dx,0–6s | 2.619932mm | 5.663399mm |
| Centroid dy,0–6s | -6.475881mm | -8.101346mm |
| Centroid dx,2–6s | 0.196086mm | 2.363090mm |
| Centroid dy,2–6s | -0.099476mm | -1.229986mm |
| Whole/hold motion | NOT_DETECTED | NOT_DETECTED |
| Mass past physical x32.5m | 0 | 0 |

Fine max displacement19.710859mm and max plastic history0.009860387 show
increased deformation/localisation, with no coherent slide or runout. KE peaks
at27.440033J/m at2s and falls to0.07378533J/m at6s. MinimumJ0.998360165;
no center domain exit or floor penetration. Minimum particle-domain margin
-0.995365micrometres remains a limitation; full particle-domain containment
and quantitative runout contact are not validated. Space/time convergence
and scientific validity are not established by this pair.

[Completed evidence](../evidence/unnotched-gravity-2026-10-25/srf1p4-h05-001-completed/README.md)
retains53 indexed artifacts/766ZIP members/282 original sources. Root verifies
54 Git blobs and564 archived source copies. The first packaging-only verifier
failure is preserved: a metadata launch ZIP lacked its manifest payloads.
The corrected archive explicitly includes verified original native sources;
the unchanged verifier passes. No solver, analysis or render was repeated.

### Next finite response study, not yet run

The [post-refinement review](../../research/notes/unnotched-landslide-2026-10-24/post-refinement-study-review.md)
and [frozen response protocol](../../research/references/unnotched-mc-ssr/response-ladder-contract.json)
define a bounded h1 SSR screen at1.6 then2.0, stopping at the first integrity-valid
coherent motion and confirming that SAME factor at h0.5. Cap2.0; no automatic
further reduction. Only SRF and derived cohesion/friction change. These are
disclosed experimental assumptions, not paper values or a factor-of-safety
claim. Common metre thresholds,6s/ramp2s,geometry/material form/BC/solver remain.
Stop on material/integrity failure or unsuccessful planned factors; preserve
negative evidence and diagnose. New input controls precede any full run.

The first Windows input-only gate now passes3 new groups/exit0: literal-only
case changes and frozen protocol; compiled config/component changes restricted
to SRF/c/phi; three native particle constructors with actual perfect-Cauchy
law values. SRF1.6 uses c6250Pa and phi0.22367501236rad; SRF2 uses c5000Pa and
phi0.18001508843rad, both psi0. No material integration or MPM updates occur.
All287 source/input hashes and actual DLL match before/after/current. The
[input evidence](../evidence/unnotched-gravity-2026-10-25/response-ladder-inputs/README.md)
retains21indexed artifacts/295ZIPmembers/root22Gitblobs. Invocation transcription
was saved after execution and is labelled; no full run or old tests repeated.

After this input checkpoint is pushed, launch ONLY the first screen:

```powershell
.\scripts\start-gravity-slope.ps1 -Case cases/benchmarks/gravity-slope-mc-srf-1p6.lisp -OutputDirectory output/unnotched-gravity-2026-10-25/srf1p6-001 -MaxWallHours 1
```

The second factor is conditional on the first integrity-valid negative result.
Use `response-ladder-audit-contract.json` for the h1 saved-data audit, freezing
reviewer/reader/contract before execution. Do not apply the old1.0/1.4 contract
to a new factor or interpret input-only PASS as a dynamic result.

### First response screen launched

SRF1.6 `srf1p6-001` starts25October17:12:41WIB on native sourceb079f05 with
one-hour wall budget until18:12:41WIB. This is a wall limit, not an ETA. The
three input-only groups above precede the launch. Source/raw/runtime are
frozen; native completion and physical outcome remain pending. The same quiet
15-minute monitor is used. No SRF2.0 simulation has been started.

### SRF1.6 terminates at the strict tensile apex

Native and worker exit1 at25October17:18:19WIB, before budget. Last saved1.7s,
18states/880MPs; attempted time1.7334542479310375s/2236updates includes unsaved
work. One frozen partial review passes18VTKs/15840rows/source282/DLL integrity
and actual4.5s playback video. The unchanged reviewer returns0 for valid saved
data; orchestration2 records incomplete native scope. Root inspects the scale1
PNG. Entire motion NOT_DETECTED,hold NOT_EVALUATED,zero toe mass. Rising KE
354.9446J/m during the ramp and21.5742mm max displacement do not verify a slide.
MinimumJ.998454423; no center exit/floor penetration; minimum particle-domain
margin-8.525micrometres is retained as a support-containment limitation.

One original-frozen principal replay confirms the rejection with1call/zeroMPM.
The actual mean Kirchhoff trial27574.643436Pa exceeds the apex27483.866984Pa
by90.776452Pa. All regular psi0 plastic flows have zero trace and preserve that
mean, while all-six-plane admissibility requires mean<=J*c*cot(phi). The mean
excess is far above the unchanged numerical allowance2.8815e-6Pa. More root
search cannot close this constitutive scope. Reaching shear yield is expected
in a landslide; this particular tensile-apex state requires an additional flow
convention. It is not evidence of a completed or unstable simulation.

[Failed evidence](../evidence/unnotched-gravity-2026-10-25/srf1p6-001-failed/README.md)
retains71indexed artifacts/653ZIPmembers/root72Gitblobs, original raw/runtime/
sources and the single replay/partial media. The successful historical live
capture is preserved; a launch packet prepared before quota exhaustion was
never executed and is explicitly labelled. No solver/replay/review was repeated.

The finite response ladder stops here:2.0 remains NOT_RUN. A
[separate composite-apex design](../../research/notes/unnotched-landslide-2026-10-24/PERFECT_MC_APEX_PLAN.md)
is proposed for perfect Cauchy MC, with explicit volumetric flow, strict-default
compatibility and new energy/transaction/native evidence gates. It is a new
constitutive assumption, not a clamp, fracture model or validated paper law.
No implementation or new full run has yet been performed.
