---
title: Wang2017 paper tensor history and MC failure capture
type: synthesis
tags: [wang2017, material-history, mohr-coulomb, native-windows]
sources: [research/references/wang2017/mpm-reference-contract.json, docs/benchmarks/WANG2017_HISTORY_ADAPTER.md, materials/models/plastic/wang2017/history.lisp, materials/models/plastic/mohr-coulomb-evolution/diagnostics.lisp]
updated: 2026-10-23
---

# Wang2017 paper tensor history and MC failure capture

Update24October: [[wang2017-soil2-native]] now implements the separate native
particle/declared incremental-polar transport and transaction contract, with
18actual frozen Windows controls PASS. The fixed-frame prototype described
below stays unchanged; native full slope and scientific validation are pending.

[[wang2017-prescribed-descent]] keeps MPM with paper physical inputs. Eq5–6
uses sqrt(.5 dev(Ep):dev(Ep)), with a signed accumulated plastic tensor. Native
summed J2 increments are not generally equivalent. Soil2 cohesion is30→15kPa
over paper kps0→.02. Relief/boundary/endpoint assumptions remain unresolved.

Source db71b63 passes17 actual Windows fixed-frame history controls,7 diagnostic
capture/replay controls and34 existing MC regression groups, all exit0. The
new optional ASDF module owns coordinate/state/law only. Tensor component order
xx yy zz yz zx xy matches engine Voigt order, but physical shear must be half
engineering shear. Owned copies and candidate-state isolation are tested.

An isolated coupled projector now exists in optional ASDF system
`cl-mpm/models/wang2017-point`. Final frozen Windows native attempt002 passes
19 controls, exit0, with optional ASDF load/elastic call exit0. Ten source copies
match before/after; existing MC and original paper primitives remain unchanged.
The old residual/search/tail assume summed incremental J2 and are preserved.
Do not substitute a law callback or scaled .02.

The new pure entry point maps principal increments into the history's same fixed
frame, solves every softening quadratic root plus constant tail, checks the
unsquared tensor norm and all MC admissibility conditions. Both two-plane edges,
rotations/all6 permutations, nonproportional/reversal, ownership/rollback and
actual3-root ambiguity rejection are tested.36 artifact hashes retain both
initial16 and final19-control sources/results/proofs in docs/evidence/
wang2017-reference-2026-10-23/soil2-point-projection.

This is **small-strain/fixed-frame only**, not a native Soil2 particle,
finite-strain transport or slope curve. Signed tensor norm may decrease on
reversal and the literal cohesion law can increase strength; no irreversible max
or healing convention is approved or silently introduced. Next integration gate
is explicit finite-strain/irreversibility interpretation, then particle state
transactions. The independent [[wang2017-apex-and-rate-study]] remains active.

MC failure conditions now carry exact supplied trial,E,nu,J,law,kappa only when
they fail, with pure JSON replay. Successful equations/tolerances are unchanged.
Synthetic/native rejection fixtures prove replay and complete state rollback;
they do not reconstruct the missing J in the historical Wang failed update.
The CLI retains a capsule while propagating the original error. A capsule is
one material return, not a full-MPM restart checkpoint.

The first CLI negative fixture exited0 because trial initialization did not seed
the committed strain state; preserve it as failed test evidence. The corrected
fixture explicitly uses a test-only scenario with zero MPM steps. Do not call
either fixture a physical Wang result. See [[scientific-authenticity-audit-2026-10-15]].

Corrected frozen CLI source9267dcb passes expected native exit1 with capsule,
exact replay exit0 and a positive legacy MC two-update/VTK run exit0. The full
source/DLL provenance is retained in cli-controls-002. This tests infrastructure;
the actual failed Wang state still requires new capture.

29 artifact hashes retain completed controls, initial fixture failure and frozen
CLI source/VTK/DLL proof. User then said "jalankan!". A new unchanged0.005m/s
Soil1 diagnostic started11:24WIB fromd60335a,90min budget, at
output/wang2017-reference-2026-10-23/diagnostic-fast-005-002. It specifically seeks
the missing failed-return inputs. This50x-rate diagnostic is not reference speed;
full1000s and native Soil2 remain NOT_RUN. The first shell launch failed before
native startup and is retained separately. One5h automation continues the work.

User then explicitly extended the running wall limit. Source a3afef0 adds a
tested monitor handoff; the same cmd21008/SBCL49524 now has3h total until14:24WIB,
supervised by25584 instead of18936. Initial launch1.5h remains immutable;
status/handoff record the change. No solver restart or physical parameter change.
Synthetic Windows SBCL control003 verifies survival past old timeout, continued
file logging and exact exit7 after attachment. Two initial fixture quoting
failures remain evidence. Postprocessors unchanged; full reference still pending.

The run subsequently FAILED_NATIVE exit1 at12:35WIB, before its extended deadline.
Last saved15.4s/77mm,78 VTKs and78 force/energy rows survive. Actual failed J is
1.0032291051924629. Six MC source files match frozen execution; exact JSON replay
PASS. Mean trial42985.3710489162Pa exceeds the necessary perfect-MC/psi0 mean
bound42982.78940658873Pa by2.581642Pa. This diagnoses the captured accelerated
state, not the paper-speed trajectory. No clamp, psi/tolerance change or restart.
Continue dedicated Soil2 work; do not repeat the full diagnostic/replay already done.

Partial video now available in docs/evidence/wang2017-reference-2026-10-23/
diagnostic-fast-005-002-video/slope-descent.mp4.78 actual states0–15.4s become
19.5s playback at4fps. Fixed spatial/colour ranges; native mc-kappa is plastic
history, not damage or Soil2 history. All78 VTK hashes match immutable raw output;
full H264 decode PASS.14 media evidence hashes. Native run remains INCOMPLETE.
