---
title: Wang2017 paper tensor history and MC failure capture
type: synthesis
tags: [wang2017, material-history, mohr-coulomb, native-windows]
sources: [research/references/wang2017/mpm-reference-contract.json, docs/benchmarks/WANG2017_HISTORY_ADAPTER.md, materials/models/plastic/wang2017/history.lisp, materials/models/plastic/mohr-coulomb-evolution/diagnostics.lisp]
updated: 2026-10-23
---

# Wang2017 paper tensor history and MC failure capture

[[wang2017-prescribed-descent]] keeps MPM with paper physical inputs. Eq5–6
uses sqrt(.5 dev(Ep):dev(Ep)), with a signed accumulated plastic tensor. Native
summed J2 increments are not generally equivalent. Soil2 cohesion is30→15kPa
over paper kps0→.02. Relief/boundary/endpoint assumptions remain unresolved.

Source db71b63 passes17 actual Windows fixed-frame history controls,7 diagnostic
capture/replay controls and34 existing MC regression groups, all exit0. The
new optional ASDF module owns coordinate/state/law only. Tensor component order
xx yy zz yz zx xy matches engine Voigt order, but physical shear must be half
engineering shear. Owned copies and candidate-state isolation are tested.

This is not a native Soil2 particle, finite-strain transport or slope curve.
A dedicated coupled projector is needed: the old residual/search/tail assume
summed incremental J2. Preserve those models; do not substitute a law callback
or scaled .02. Signed tensor norm may decrease on reversal; no irreversible max
or constitutive healing convention has been silently introduced.

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
