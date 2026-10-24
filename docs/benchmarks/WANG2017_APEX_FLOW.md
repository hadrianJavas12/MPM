# Explicit Soil2 apex-flow experiment

The strict Soil2 failure is preserved in [the failure review](WANG2017_SOIL2_FAILURE.md)
and commit9dc3649. A separate opt-in material now implements an additional
volumetric flow mode at the hydrostatic apex. This changes the constitutive
flow graph; it is not unchanged pure-shear psi0 physics or an exact Wang law.
The original strict material and all its negative evidence remain available.

The first60mm/6s full trial now completes native/audit/render0. Its independent
review finds no coherent landslide; [results and the bounded100mm study](WANG2017_APEX_TRIAL.md)
record actual apex activation and remaining scientific limits.

## Contract

Optional ASDF system `cl-mpm/models/wang2017-apex`, package of the same name:

- `particle-wang2017-soil2-apex`: native particle subclass with inherited owned
  signed tensor, corotation, commit/reset/copy and outer transaction behavior.
- `project-paper-principal-with-apex`: pure candidate enumeration.
- `make-soil2-apex-law`: identical c30→15kPa, kps0→.02,phi35/regularpsi0,
  Cauchy strength curve; descriptive convention explicitly differs.

The added mode is `fA=p-J*c(kps)*cot(phi)<=0`, `gA=p`. It adds no fitted tensile
strength parameter. At an apex, the trial deviator determines plastic deviator
`d=(trial-pTrial)/(2G)`. Map d through the current eigenbasis and add committed,
rotated Ep to calculate kps. Then compute `pA=J*c(kps)*cot(phi)` and plastic
volume `q=(pTrial-pA)/K`. Require q≥0; total principal plastic strain is
`d+q/3`, returned tau is hydrostatic pA, and elastic compliance/history/flow/work
identities must hold. q is the multiplier of gA=p. This is an explicit volumetric
mode in addition to zero-trace shear modes, not the associated MCphi normal cone.

All regular roots and the apex candidate are enumerated/deduplicated together.
Zero or multiple distinct admissible states reject; there is no exception-driven
fallback, arbitrary apex preference or stress-only reset. The original elastic
screen remains. Native monotonic-history rejection also remains; no hidden max.
Independent J2 reporting is not replaced by1.5times paper history.

[Itasca's primary model documentation](https://docs.itascacg.com/itasca950/common/models/mohr/doc/modelmohr.html)
documents separate tensile flow and apex treatment; original CL-MPM C++ also has
an apex branch. These motivate an explicit convention, not a claim that this
coupled signed-history extension is uniquely specified by Wang.

## Uniqueness limit

For trace-free returned stress s, MC requires
`p <= a(kS)-betaMin*||s||F`, where a=J*c*cot(phi) and
`betaMin=(3-sin(phi))/(2*sin(phi)*sqrt(6))`.
The history norm is Lipschitz: `|kA-kS|<=||s||F/(2*sqrt(2)*G)`.
Since cohesion slope magnitude is at most h750000Pa, distinct apex and regular
solutions cannot coexist if `J*h*cot(phi)/(2*sqrt(2)*G)<betaMin`.
For E20MPa,nu.25,phi35, betaMin=.863514615509, critical J18.2419050843;
the captured J1.00189081946 gives coefficient.047426371410.
This excludes only apex-versus-regular coexistence under that sufficient bound,
not multiplicity among regular roots or all-path uniqueness.

A concrete E0.5MPa counterexample has both positive-work regular and apex states;
it violates that sufficient bound. The new solver must retain ambiguity
rejection there. Positivity alone is not a branch-selection rule.

## Current validation and next action

Source review/lexical balance and native loading/input3groups pass. New focused
frozen controls report11PASS:12 new-model point calls,5 native constitutive
calls, zero strict capsule replays and zero MPM updates. They cover the captured
input under the NEW model, compliance/CauchyJ/volume/work, rotations/permutations,
ownership, regular compression, ambiguity and native transactions. The original
strict failed-point replay is not repeated or reclassified as success.

Regression after shared candidate extraction/default dispatch passed on Windows:
strict point19, old MC34, framework10, strict native18 and strict input3 groups,
all exit0. The new apex input3 groups also passed with zero MPM updates.
The point/MC/framework/input runs loaded workspace sources; native18 and the
output controls below used frozen private sources and verified copied DLLs.

The first regression wrapper stopped after those five passing commands because
its PowerShell argument array joined the output path and variant. An operator
fresh-directory guard stopped that malformed invocation before any MPM update.
Its FAILED status, original wrapper and guard are preserved, not overwritten.
Only the two missing output gates were resumed in `apex-integration-002` with
correct separate arguments: strict and composite-apex each exit0/8PASS, exactly
2 genuine USF updates,25MPs,2VTKs,50material and4contact rows. Thus four actual
MPM updates were performed in this stage, not a full slope. Strict's two VTKs
and two CSVs are byte-identical to the original strict output002 control.
Each frozen integration load has275 source records matching before/after.

Evidence is under `docs/evidence/wang2017-soil2-2026-10-24/`: `apex-controls/`,
`apex-flow-design/` and `apex-integration/`. The design packet retains its
historical NOT_RUN scope separately from subsequent executed controls. All
failed harness evidence remains available. No completed gate needs repeating.

The next prospective full case is
`cases/benchmarks/wang2017-soil2-apex-fast-010.lisp`.
That case preserves0.01m/s to60mm/6s, geometry, mesh, BC, damping and all numerical
strength/elasticity inputs. Metadata and volume diagnostics label the new model.
The first fresh full trial started24October12:08:32WIB on55bc85d in
`output/wang2017-soil2-2026-10-24/apex-fast-010-001`,2h wall budget until14:08.
It finished native0 at13:33:43WIB and audit/render/worker0 at13:34:44.
No landslide PASS is claimed; the saved-state review is linked above.
Mesh/rate/boundary/reference
and finite-strain limitations remain; this convention does not guarantee failure.
