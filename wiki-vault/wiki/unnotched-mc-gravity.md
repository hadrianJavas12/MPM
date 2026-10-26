---
title: Unnotched MC gravity scenario and native gates
type: synthesis
tags: [mpm, unnotched, gravity, strength-reduction, windows-native]
sources: [docs/benchmarks/UNNOTCHED_MC_GRAVITY.md, docs/benchmarks/UNNOTCHED_STATIC_DIAGNOSTIC.md, research/references/unnotched-mc-ssr/contract.json, docs/testing.md]
updated: 2026-10-26
---

# Unnotched MC gravity scenario and native gates

Implements [[unnotched-landslide-method-selection]] on branch
`codex/unnotched-gravity-benchmark`, first source2308a1e. Six short scenario
owners compose the existing native perfect MC material/solver with unnotched
D1-inspired polygon, independent SRFs1/1.40, smoothstep gravity ramp0–2s and
constant gravity2–6s. No driver, initial weak seed, notch, elastic release or
state reset is hidden. Fixed grid bottom is not Coulomb runout contact.
The original additive checkpoint preserved the numerical implementation; the
later scoped acceptance repair below is an intentional, separately gated change.

Frozen001 passes five input/geometry/BC/ramp groups then fails a caller-local
counter fixture. It still executes two real updates.002 uses shared synchronized
counters, skips the five passed groups and closes runner/CSV/VTK/read-only:
1760material calls,880MPs,two updates,three states/2640CSV rows. Both285file
snapshots match before/after, actual copied DLL is verified, and all three VTKs
plus two CSVs are byte-identical between attempts. Production numerics unchanged.

Independent002 audit passes with frozen source constants and actual scale1 PNG
inspection;001 fallback/provenance limitations remain recorded. The states are
tiny elastic motion, not landslide proof. Native wall cost and initial stable dt
justify a bounded first6s reduced trial, without guaranteeing plastic runtime.
Baseline follows sequentially. Detection conventions were fixed before results.

Thirteen synthetic supervision assertions and9+2gravity-alias detachment/default
checks pass with zeroMPM; delayed001fixture expiry/exit8 is preserved. Raw/settings
remain intact. [[wang2017-residual-history-scope]] remains a separate tested repair
checkpoint, not an automatic full rerun or an achieved-landslide claim.

## First full trial and actual failure diagnosis

SRF1.40 source `a4de3e6` fails native1 on24October22:42:34WIB during the ramp.
Ten real states0–0.9s retain880IDs/8800material rows. Attempted time0.980934788s
and1265 updates include later unsaved work; saved0.9s is not the exact failure
time. Saved finite/mass/ID/F/J/volume/law/yield/CSV–VTK integrity passes, maximum
motion is3.295mm, and no mass crosses the toe. Post2s and1s persistence windows
are NOT_EVALUATED. Coherent landslide remains unverified.

The51-indexed-artifact/909-ZIP-member negative packet retains actual raw data,
frozen sources, exact review support and scale1 incomplete media. Late launch
capture is honestly INCOMPLETE_CAPTURE. Replay001 is a helper package-lock
failure with zero calls;002 performs exactly one original production principal
return, zero MPM updates, with283 before/after source hashes and mapped DLL
verified. The six MC modules match the failed run. Full-MPM rollback is
NOT_EXECUTED from this pure capsule.

The admitted false edge has multiplier-7.313031e-13, within the old absolute
1e-12 allowance but producing32.42 times the existing stress tolerance in
elastic stress error. A valid face has nonnegative multipliers. Exact old
candidate observations and a separate analytical Schur-complement check explain
the ambiguity without preferring a root or changing physical inputs.

## Scoped repair, 25 October 2026

Base MC-evolution `project-principal` adds a conservative negative-multiplier
backward-error sum inPa, using actual elasticity/flow/yield vectors and the
unchanged stress tolerance. The original shared predicate, all constants,
deduplication and genuine all-roots rejection remain unchanged. Wang point,
native and composite-apex acceptance are outside this repair; no hidden fallback
or multiplier/stress/strength clamp is introduced.

Existing native material-point suite passes34 controls with283 source hashes
verified afterward. Frozen `complementarity-controls-001` passes eight groups,
exit0:61 new fixed-code point calls, one native constitutive rollback call,
zero MPM updates and zero old-baseline replays. All284 source hashes match
before/after and mapped DLL is verified. The captured input now returns the
nonnegative face; false-edge backward stress/plane error1.12508e-4Pa exceeds
unchanged tolerance1.73497e-6Pa. A genuine three-positive-root fixture still
rejects ambiguity. This is new-code verification, distinct from the retained
original-source replay; no whole-MPM rollback claim follows.

Narrow `native-output-fixed-001` passes four output groups with1760 accepted
material calls/two actual USF updates/880MPs/three VTK states/2640CSV rows.
All285 source hashes match before/after, mapped DLL is verified, and three
particle VTKs/two CSVs are byte-identical to pre-fix002 elastic output. Initial
comparison included mesh.vtk by mistake and asserted before a result; retain
the negative artifact and file-selection-only repair, with no solver repetition.

Fix/control evidence retains43 indexed artifacts/886 archive members/852 source
entries; root independently verifies every hash and44 staged Git blobs. A
fresh full continuation has not started. No landslide or calibrated runout is
established by these numerical gates.
[[unnotched-landslide-method-selection]] retains the original source/provenance
limits, and [[wang2017-residual-history-scope]] remains a separate model policy.

## Fresh full attempt, 25 October 2026

Source/checkpoint3ed36a3 is pushed; same-input `srf1p4-002` starts03:57:28WIB,
target6s/61states,3h wall budget to06:57:28WIB. Initial conditions and all study
physics/numerics remain unchanged; only the gated base-MC acceptance repair
justifies this fresh attempt. Exact live process identities/parent chain and
mapped DLL/source provenance are retained. Two launch-proof harness failures
(typed-date parsing and different creation-clock precision) are retained;
successful proof compares each original clock exactly, with no solver restart.
One quiet15min monitor is active. Review actual terminal output before the
sequential SRF1 control; no landslide or quantitative runout is established.

Launch packet retains21 indexed artifacts; root verifies22 staged Git blobs
and all282 actual immutable source files. The only source change versus001 is
the projector; all281 other sources, executable case and full config match.
Full raw/source/media storage and physical review remain due at terminal.

## Completed reduced-strength result and baseline, 25 October 2026

Attempt002 completes6s/61states/7740updates/53680 material rows at04:12:52WIB,
native/worker exit0. ONE exact-source saved-data review/render passes integrity;
all282 immutable source/DLL hashes match. Root also inspects actual scale1 PNG.
Video61actualstates/4fps/15.25s playback/fullDecode0 has no interpolation or
magnification. The prefix ten0–0.9s VTKs/8800particle/10history rows exactly
matches original failed001; all numeric deltas zero, no repeat solver/replay.

**Actual landslide remains absent.** Maximum displacement12.083373mm;
cohort+2.619932mmX/-6.475881mmY,post2–6s adds only+.196086mmX/-.099476mmY.
KE7.099245J/m peak decays to.05890283J/m. Both motion windows NOT_DETECTED,
zero toe runout. MinimumJ.9984039/no center penetration or domain exit support
integrity,while half-domain margin-3.5951micrometres remains a limitation.
Completed evidence45indexed artifacts/445 ZIP members/282 sources and46 staged
Git blobs verified. No full-slope scientific PASS follows.

Sequential predeclared baselineSRF1 starts04:18:27WIB on8d8b544,3h budget until
07:18:27WIB. Its case/config differs ONLYSRF,c,phi; no new gates or hidden
overrides. Baseline launch20indexed artifacts/282 actualsource hashes/21 Git
blobs/livePIDsessioncreationclockparentchain proof verified. Inline inputmatrix
script was not separately saved; provenance gap labelled. Compare actual pair
at terminal before selecting geometry/mesh/ramp study, with no ad-hoc SRF or
duration increase. One quiet15min monitor remains active.

Conditional post-pair design review recommends exact source geometry/static
cross-check before expensive refinement; proposals remain NOT_RUN. Halvingh
also changes the current h-scaled observer. Preserve original results and
preregister common physical-metre cutoffs/thresholds across both meshes; never
use changed detection thresholds to manufacture a positive result. Identical
dtScale with halvedh changes both space and time resolution.

## Paired result closure and static gate

Baseline completes native/worker0 at25Oct04:33:41WIB,6s/61states/7740updates; ONE review/render/source282/DLL audit passes. Maxu7.588638mm versus12.083373mm atSRF1.4; both settle, no motion/runout detected. ONE saved comparison aligns53680 time/ID rows. Baseline+pair46indexed artifacts/444ZIP members/282sources and47Gitblobs independently verified. No old audit/render repeated. New static-reference audit/contract preregisters bounded Bishop circles/slice refinement before results; report negative normals without clamp/physicalPASS. Static controls/search NOT_RUN; actual landslide goal unmet.

## Independent static gate and same-strength refinement

Five new mathematical controls pass; ONE frozen36,006-candidate Bishop search gives fine formal factors1.383870236/SRF1 and0.988478740/SRF1.4. Six negative slice normals/min-7.171kPa, bounded family and near-base arc0.084067m remain limitations, with no clamp/physical/globalFoS PASS. Exactbackend+contract copied beforesearch;19indexed artifacts/20Gitblobs verified. New refinementcontract freezesmesh1→.5 asONLYassignmentchange, unchangedstrength/loading, commonphysicalmetreobserver, bounded3h budget. Native refinedgate/fullrun stillNOT_RUN atcheckpoint; no actuallandslide claimed.

## Native h0.5 integration gate closes

Four frozennativegroups PASS once: onlymeshdiff,3520MP/samemassgeometryBC,2actualupdates/7040acceptedcalls,3VTK/10560CSVindependentreadback.285source/input hashes andmappedDLLmatchbefore/after;25indexedartifacts/300ZIPmembers/26Gitblobs verified. Fineauditcontractkeepsnativehscaledcriteria; physicalmetrecomparison remainsseparate. Full6s refinement NOT_RUN atcheckpoint; no oldtests repeated.

## Full refined study starts

Source1a9f29a h0.5 runstarts25Oct14:53:10WIB,3h budgetto17:53:10WIB;3520MP/6s61frames,onlymeshassignmentchanged. ExactlivePID/session/originalclock/parentchainproofretained; initialincompleteidentityhelperfailureisnotnativefailure. Onequiet15minmonitor. Finehscaledintegrity andcommonmetrecomparisonpending; no actuallandslide claim.

## Common physical observer controls

The first frozen invocation passes nine synthetic tests with exit 0; seven
source/support files match before and after. Controls verify the physical
cohort, graph, motion/persistence and toe thresholds, equivalent coarse/fine
mass, post-2s reference, contract rejection and non-mutation. No actual native
or saved-run analysis, full workflow or plotting occurred. Evidence is in
`docs/evidence/unnotched-gravity-2026-10-25/refinement-observer-controls/`.

`scripts/review-gravity-refinement.py` now prepares one terminal fine audit
and render, freezing exact wrapper/reader/reviewer/contracts before execution.
The fine h-scaled report remains separate from the common physical observer
on both meshes. Coarse CSVs are anchored to their existing audit without
repeating coarse analysis/render; IDs are not matched between meshes. See the
benchmark guide for the command. Full workflow and refined result remain
NOT_RUN; actual spatial review is required before any landslide claim.

## Same-strength refinement completes without sliding

Native/worker exit0 at25October16:56:33WIB;6s61states3520MP15471updates. The
first frozen review/render exits0, with source282/DLL and actual scale1 video
verified; root inspects both plots. The common physical cohort has identical
mass on both meshes. Fine hold centroid dx2.363mm versus coarse0.196mm and
stronger plastic localisation show resolution sensitivity, but KE falls from
27.440 to0.0738J/m. Both physical motion windows and toe runout remain negative.
This is not a converged result or verified landslide. The small negative
particle-domain margin and fixed-bottom/runout limits remain explicit.

Completed evidence53indexed artifacts/766ZIPmembers/root54Gitblobs retains
raw/source/runtime/media and the first packaging-only verifier failure. The
corrected launch archive adds282 verified originals; no solver/review/render
was repeated. Raw and personal settings remain intact.

The next preregistered response study screens h1 atSRF1.6 then2.0, capped2.0,
stopping at the first integrity-valid coherent motion and confirming the SAME
factor on h0.5. It is deliberate disclosed strength reduction, not unchanged
soil collapse or a factor-of-safety estimate. Geometry, boundaries,6s/ramp2s,
solver and metre observer remain fixed. Native input gates/full runs are
pending. See `response-ladder-contract.json` and the post-refinement design note
linked from the benchmark guide. Actual unnotched sliding remains the goal.

The first response input gate closes3 new groups/exit0,three native constructors
and zero material/MPM updates.287 frozen source/input hashes and actual DLL
match; cases differ only literal SRF and actual config/components onlySRF/c/phi.
Input packet21indexed/295ZIPmembers/root22Gitblobs is retained, including the
honestly labelled after-execution command transcription. No full response run
yet; the next authorized run is ONLY1.6 after this checkpoint is pushed.

The first1.6 screen now starts25October17:12:41WIB on sourceb079f05, with a
one-hour wall budget until18:12:41WIB. It uses the disclosed reduced c6250Pa/
phi0.22367501236rad and unchanged geometry/BC/ramp/grid/solver. The input gate
precedes the full run; actual motion remains pending. One quiet15-minute
monitor follows this run;2.0 has not started and remains conditional.

## Strict1.6 rejection: tensile/apex constitutive scope

Native/worker exit1 at25October17:18:19WIB. Last saved1.7s/18states/880MPs,
attempt1.7334542479310375s/2236updates. FIRST partial review passes integrity
for15840rows/source282/DLL/actual18-state scale1 video; root inspects PNG.
Reviewer0 is separate from incomplete orchestration2/native1. Whole motion is
NOT_DETECTED; post2s NOT_EVALUATED,zero toe mass. Partial rising KE does not
verify sliding. Small negative particle-domain margin remains explicit.

ONE frozen principal replay proves regular psi0 flow cannot return the actual
mean27574.643436Pa to the admissible apex27483.866984Pa: all six flow traces
are zero. Excess90.776452Pa is far above existing mean allowance2.8815e-6Pa.
This is a tensile/apex flow-scope issue, not a newly found multiplier bug or
evidence of successful failure. Reaching shear yield and obtaining an
admissible plastic update remain necessary parts of a valid landslide run.

Failed evidence71indexed/653ZIPmembers/root72Gitblobs retains raw sources,
one replay and partial media. Live proof exists, but the prepared launch packer
was never executed during quota exhaustion; the gap is labelled. No repeated
solver/analysis.2.0 remains NOT_RUN. The separate perfect composite-apex plan
adds declared volumetric flow and requires technical review plus new/default/
transaction/native gates; implementation is pending. Actual slide remains unmet.

## Optional perfect composite-apex source checkpoint

Subsequent work is on `codex/unnotched-mc-composite-apex`. The approved separate
model and optional framework diagnostics are implemented and source-reviewed;
native compilation/testing is **NOT_RUN**. The strict projector and Wang
sources remain unchanged. A narrow dispatch hook reuses the owned transaction.
The derived projection stores the actual apex multiplier separately from shear
multipliers and preserves its scalar through copied state; native tests must
verify that behavior. Fifteen frozen source-ready groups cover mathematics,
strict delegation, current J, work/volume and copy/commit/reset/rollback.

The additional `g_A=p` flow is a declared constitutive assumption. Equality
and the numerical cap band continue through strict rejection/success behavior.
Point/default/native output gates are required before a new slope case. Local
yield is distinct from global instability; the prior tensile-apex rejection
does not verify a landslide. No full run or SRF2.0 has been started.

## Subsequent native point and default compatibility evidence

FIRST Windows new-model gate on `ac767e1` passes 15 groups with 38 explicit
new pure calls, 6 strict comparisons, 10 native calls and zero MPM updates.
Point evidence has 18 indexed artifacts / 296 ZIP members; root verifies 19
Git blobs and all 287 archived/actual source copies plus mapped DLL. The old
failure replay is not repeated. The new flow on the retained input records
actual apex volume multiplier 1.0893174239569781e-6 and plastic work
0.029938655183461227 Pa. No full-slope result follows from this point success.

Default strict34 and bounded two-USF-update/four-output-group controls pass
once; three VTKs and both CSVs are byte-identical to the pre-hook strict fixture.
Actual 287/289 source sets, runtime and unloaded optional systems are verified;
corrected default packet passes root checks: 42 indexed / 43 Git blobs /
two archives / 612 members / 576 sources. Original archive-layout and subsequent
packaging-only filesystem failures are preserved; verifier/tests unchanged.
New optional-framework
MPM output remains pending. All prior negative evidence and raw settings stay.

## Subsequent optional scenario source phase

On 2026-10-26, source preparation adds a narrow exact-class validation hook,
explicit optional metadata and the separate composite SRF1.6 case, reusing the
existing numerical runner. A reviewed four-group optional-framework output
gate is NOT_RUN. It separates a single constitutive apex fixture from a tiny
32-MP/two-update MPM export fixture. New variant contract and saved-data review
are source-only; Python AST passes. Targeted scenario and analysis gates precede
a full run. No new full solver, hidden strength change or verified slide.

## Bounded optional integration and first actual variant review

Framework002 closes three remaining groups after001's retained serializer
failure: two genuine USF updates / 64 calls / 32 MPs / three VTK / 96+3 CSV
rows and one separate native apex fixture. Root verifies 41 indexed artifacts,
42 Git blobs, two ZIPs / 602 members / 578 sources. Eleven reviewer helper
controls and three new binding controls pass without native calls.

Scenario001's first four groups and two updates/1760 calls pass; saved reader
fails on nonexistent out-of-plane2D VTK fields. Test repair retains six-stress
CSV/yield checks. Saved-only002 retains a CMD comma-argument failure, zero MPM;
003 will use a single-token alias/absolute path. FIRST independent frozen-child
variant review already passes on actual001's three saved states/291-source/DLL
proof and root-inspected PNG. These20 microseconds have no apex flow/slide;
full6s study and same-factor refinement remain separate future evidence.

## Scenario closure and full-study preregistration

Saved-only003 passes both remaining groups with zero updates, reusing001's
three real states. All six groups close without repeating four passed inputs
or the two native updates. Root verifies55indexed/56Git blobs/fourZIPs/944
members/873 native source copies plus291 actual003 files. Framework evidence
and11+3 Python controls/actual frozen variant review are complete. The separate
full-study document preregisters6s/61states/SRF1.6 and unchanged nonmaterial
inputs. Freeze launch evidence and run once after checkpoint; no new solver
or verified slide yet. Same-factor h0.5 confirmation remains conditional.

## First full optional run active

Native source35427376 starts `srf1p6-composite-001` on26October00:29:14 WIB,
one-hour wall deadline01:29:14 WIB. Full6s/61states/SRF1.6; all nonmaterial
inputs stay fixed and the extra volumetric flow remains explicit. Root verifies
the pre-launch/captured case/config,287 sources/DLL and273 shared numerical
files, plus ONE exact-clock four-process parent proof. Launch packet35indexed/
36Git blobs/288ZIP members/287sources is verified; capture0.5s is incomplete.
At that launch checkpoint one quiet15-minute monitor continues. The result
below supersedes this historical active status; do not repeat closed work.

## Full composite SRF1.6: completed, transient deformation settles

Native source35427376 completes26October00:44:59WIB, native/worker0,
6s/61states/880MPs/7740updates. FIRST actual frozen review002 exits0 with
integrityPASS:287 sources/DLL and61VTK/53680particle rows, F/J/mass/IDs/law,
six-plane yield and apex work/volume. Invocation001 fails before Python opens
the script because of PowerShell argument concatenation; negative caller
evidence is preserved, not called a native/material failure.

Root views the real scale1 summary. Plasticity localizes near lower face/toe;
upper-cohort final displacement is(+63.987,-36.197)mm and2–6s increment
(+44.893,-21.262)mm, followed by a plateau. Final mean vx=-0.00033955m/s.
Whole/hold connected-motion and toe-runout tests are NOT_DETECTED. Local yield
occurs but no sustained global landslide is verified. The0.18279m maximum
displacement and colour are not sufficient evidence. Minimum half-support
margin-8.525micrometres limits containment claims; no sampled centre exits or
floor penetrations. The declared volumetric apex extension is still not
unchanged strictMC, fracture or exact paper physics.

Existing61-state/4fps/15.25s video represents6physical seconds, scale1/no
interpolation/full-decode0. ONE frozen prefix comparison passes exact0–1.7s:
18history/15840particle rows and positions/IDs/38commonVTK fields all match.
Two declared extra apex fields explain full VTK byte differences. Full
source/raw/runtime/review/media/prefix and caller failure are retained in
`docs/evidence/mc-composite-apex-2026-10-26/srf1p6-composite-001-completed`.
Root verifies58 indexed/59 Git blobs/509 members/287 archived and287 actual
sources. Root spatial review and saved-result diagnosis are included.

The goal of [[unnotched-landslide-method-selection|unnotched failure]] remains
open. Diagnose fixed-base/adapted-foundation and resolution before a new
expensive study; no automatic duration extension/SRF2.0. A justified same-factor
h0.5 study tests resolution with common metre thresholds and coupled space/time
refinement, rather than confirming an already observed slide. Idle automation
returns to5hours; no old native/review/render/gate repetition.
The basal GIMP gate now passes six new controls on source4eeb2fe9,0material/
MPM calls and unchanged actual particles. Actual partition/gradient errors0;
positive basal weights affect centres up to0.75m versus0.375m. Hypothetical
minimum-arc probes cross the floor at both domain sizes, so their partition
loss is not an actual-MP defect. Prescribed-field RMS values use different
particle samples and prove neither convergence nor locking. Root22indexed/
23Git blobs/302members/290sources and separate summary7indexed/8blobs verify;
collector-only schema failure remains. No native diagnostic is repeated.

Root/independent review select one same1.6/composite h0.5/6s resolution study,
NOT_RUN until new targeted gate closes. Physical-metre observer stays fixed;
native h-scaled detection remains separate. Same CFL couples space/time and
MP sampling. After that pair, no automatic finer mesh/SRF/time extension;
resolve physical foundation/base/reference definition before another experiment.

The FIRST six new CSV-comparison binding controls now PASS from two copied
sources, before/after hashes unchanged. CSV is restored before testing contract
tamper separately. This is synthetic glue verification only: no old observer
tests/native/audit/render repeats, no actual fine comparison or fine solver.
Native fine input/output gate remains NOT_RUN; do not repeat these six controls.

Subsequent FIRST native fine gate sourcef0b5fb69 exits0: four NEW groups,
3520MPs/2USF/7040 accepted calls/3VTK/10560CSV rows and source/DLL proof.
No standalone constitutive calls or apex activation, no old test/slope repeat.
This supersedes the prior native-gate NOT_RUN; full fine run/actual review and
pair comparison remain NOT_RUN. Launch draft still requires actual profile
completion/review before use; no verified landslide is claimed.

## Earlier Urmi-inspired collapse is a different control

User's recollection is correct that the old videos show slumping. Read
`docs/benchmarks/URMI_LEGACY_COMPARISON.md`: actual H/HS recipes use a2.5x2.5m
notch,72degree face,4m soil foundation and elastic-only stage1 followed by
plastic enable/resets. They are not unnotched evidence. Their bulk summary
filters domain/displacement/speed outliers and conditionally replaces KE;
raw HS outliers prohibit interpreting its PASS as full physical integrity.

Actual paper p6 uses stable drained elastoplastic MC before an undrained
parameter switch; this is distinct from disabling plasticity. A separate
faithful drained→undrained softening hypothesis is retained for after the
finite resolution pair, not silently enabled in the perfect control. Old raw
data/video/source are preserved; no old run/audit/render repeated.
