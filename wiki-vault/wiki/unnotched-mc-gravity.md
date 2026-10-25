---
title: Unnotched MC gravity scenario and native gates
type: synthesis
tags: [mpm, unnotched, gravity, strength-reduction, windows-native]
sources: [docs/benchmarks/UNNOTCHED_MC_GRAVITY.md, research/references/unnotched-mc-ssr/contract.json, docs/testing.md]
updated: 2026-10-25
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
