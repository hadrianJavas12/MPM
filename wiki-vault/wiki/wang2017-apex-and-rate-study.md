---
title: Wang2017 apex convention and controlled rate study
type: synthesis
tags: [wang2017, mohr-coulomb, apex, rate-study, native-windows]
sources: [docs/benchmarks/WANG2017_APEX_REVIEW.md, tests/materials/mc-legacy-apex-comparison.lisp, tests/benchmarks/wang2017-rate-comparison.lisp, cases/benchmarks/wang2017-soil1-rate-002.lisp]
updated: 2026-10-24
---

# Wang2017 apex convention and controlled rate study

[[wang2017-prescribed-descent]] continues after the human's request to succeed.
The captured accelerated state violates the necessary strict psi0 perfect-MC
mean bound. [[wang2017-paper-history]] retains actual J/replay and partial video.

Five new Windows native point controls pass, zero MPM updates. Actual loaded
legacy DLL accepts the state by an explicit apex return with positive plastic
volume; strict return rejects it with unchanged inputs. Raw legacy cohesion is
Kirchhoff; J-scaled cohesion gives matching Cauchy strength. An admissible shear
control agrees between implementations. This is a different tensile flow
convention, not proof the strict solver should accept the state unchanged.
Primary official FEM/vendor conventions are linked from the apex review.

Three new native rate002 input controls pass: only velocity,derived duration,
frame count and computational cap differ. Material,geometry,mesh,timestep scale,
damping,boundaries and penalty remain unchanged.13 artifact hashes retain the
point/preflight sources/results/proof under docs/evidence/wang2017-reference-
2026-10-23/rate-and-apex-controls. No legacy clamp was enabled.

Historical rate002 run started14:35:52WIB on68efa27, wrapper16236/cmd38152/SBCL25128,
five-hour budget.0.002m/s is20x paper;0.1m requires50s,251 states at0.2s cadence.
It tests the trajectory's rate dependence, without claiming rate independence,
scientific validation or guaranteed completion. Do not duplicate a healthy run.

Update24Oct: rate002 is INTERRUPTED_UNKNOWN_EXIT,33states to6.4s/12.8mm, all old
processes absent.24 retained evidence hashes and7 exact common-settlement pairs
record consistent data without rate-convergencePASS. Session logoff correlated
with stopped outputs, no exitcode/MCfailure proof. User-confirmed replacement
trial and monitor controls are in [[wang2017-fast-trial-2026-10-24]].

Fast010 subsequently completed native6s/60mm, exit0,61states; audit/video0.
Comparison on61exact saved settlements withfast005 gives reactionend+2.5173%
and maxpositiondistance3.390mm, with identical gravity initialization. This
does not establish rate independence or a landslide, and it does not erase the
different fast005 failure at77mm. No apex/tensile convention was changed.
New [[wang2017-paper-history|Soil2 coupled point prototype]] passes19 controls
and optional ASDF smoke independently of this frozen native source;36 hashes
retain its evidence. It does not enable a Soil2 particle or finite-strain rule.
