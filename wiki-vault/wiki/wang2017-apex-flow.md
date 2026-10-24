---
title: Wang2017 explicit volumetric apex-flow experiment
type: synthesis
tags: [wang2017, soil2, apex-flow, native-windows]
sources: [docs/benchmarks/WANG2017_APEX_FLOW.md, tests/materials/wang2017-apex.lisp, docs/testing.md]
updated: 2026-10-24
---

# Wang2017 explicit volumetric apex-flow experiment

[[wang2017-soil2-return-failure]] remains a strict negative control. A separate
optional material adds a hydrostatic apex support surface and volumetric flow
potential. This explicitly changes the constitutive flow graph; it is not an
unchanged psi0 law or a uniquely specified Wang finite-strain model. Regular
shear dilation, strength curve, elasticity and loading inputs stay fixed.

The trial deviator determines plastic deviator/history; resulting softened
cohesion determines hydrostatic apex stress and positive plastic volume through
elastic compliance. Full Ep/volume/work/state are recorded, not just stress
clamped. All regular/apex candidates are considered; zero/multiple states reject.
Signed-history decrease guard and corotated state ownership remain unchanged.

A sufficient Lipschitz/MC bound excludes distinct regular/apex coexistence for
paper E20MPa and J near1. It does not prove all-path uniqueness. A weaker-E
positive-work ambiguous counterexample remains rejected in native controls.

Frozen11 controls exit0 (12 new-model point/5 native calls, zero MPM), plus
apex input3 groups. Strict point19/MC34/framework10/native18/input3 regression
groups pass after shared candidate extraction/default dispatch. Only native18
is frozen among that regression batch; the rest use workspace sources.
Resumed strict/apex output gates each8PASS/exit0,2 genuine USF updates/25MPs/
2VTKs and50material/4contact rows. Strict2VTK+2CSV byte-identical to previous
strict output control. Four MPM updates total, not a slope benchmark.

The initial wrapper's malformed argument array was blocked before MPM by an
operator guard. Its FAILED status and original script are retained; completed
regressions were not repeated. Evidence packets apex-controls/apex-flow-design/
apex-integration retain exact source/runtime proof and historical NOT_RUN scope.

First full trial started24October12:08:32WIB on55bc85d in apex-fast-010-001,
2h budget until14:08. Worker23904/wrapper21136/cmd49564/SBCL23428 Session11;
native initial RUNNING, same quiet automation15min. This case keeps approved
0.01m/s to60mm/6s and all geometry/
grid/BC/damping/strength settings from [[wang2017-soil2-native]]. No landslide
claim follows from controls. Actual coherent free-mass motion/run-out and the
mesh/rate/boundary/reference limits still require review. See also
[[wang2017-apex-and-rate-study]] and [[wang2017-paper-history]].

Launch-only packet retains6 artifact hashes/292 verified ZIP members,275 frozen
files matching manifest/workspace, actual copiedDLL,3 postprocessor hashes and
one4-process identity observation. Captured RUNNING/complete=false only; active
CSV/VTK/logs were not read or archived. No solver/tests repeated for collection.
