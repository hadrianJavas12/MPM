# Earlier Urmi-inspired runs versus the unnotched study

26 October 2026. Read-only comparison prompted by the user's recollection of
earlier MC collapse. No old simulation, material test or video was rerun.

## What the earlier runs demonstrate

The retained H/HS cases and saved spatial image show substantial computed face
slumping. They are **not an unnotched control**. Both long cases explicitly use
a12m-high,72degree cliff, a4m foundation of the same soil, and a2.5m-high by
2.5m-deep toe notch. The saved effective configurations confirm those notch
dimensions. The runner cuts the face and notch before gravity initialization;
it does not excavate a new notch at the dynamic transition.

| Item | Earlier long H/HS cases | Current composite SRF1.6 study |
| --- | --- | --- |
| Geometry | 12m/72degree cliff;4m soil foundation; toe notch | 10m/26.565degree slope; no foundation/notch |
| Material | c5→7kPa,phi15→20degrees hardening; HS then c2kPa/phi13degrees;psi1degree | Perfect c6.25kPa/phi atan(tan20/1.6); regularpsi0 plus declared volumetric apex mode |
| Gravity initialization | 220 fixed elastic-only updates, high damping | Plasticity active during2s gravity ramp |
| Transition | Zero velocity/displacement, reset time, enable plasticity, lower damping | No stress/history/velocity reset or material switch |
| Result available | Notched slumping and filtered bulk-motion metrics | Complete6s, transient deformation arrests; no verified coherent slide/runout |

The old Stage1 loop has no convergence criterion. Its CSV label
`stage1_equilibrated` is not proof of equilibrium: the saved first-state
MC residual is approximately27kPa. Enabling plasticity then redistributes a
stress state already outside the initial MC surface. This differs from a
verified stable drained initialization.

Reaching MC yield permits plastic flow. A consistent accepted return lies on
or within the yield surface; it need not remain outside it for the body to
move. Local yield alone is not a global instability criterion. The difference
between these experiments is not that the current solver forbids yielding.

## The actual paper's initialization is different

The local paper, Urmi et al.(2024), *Engineering Geology*340,107669, is retained
unchanged at `docs/Prediction of retrogressive landslide in sensitive clays.pdf`,
SHA256 `3f6aa9f5ba914564df3031aa8d6853ffef91b045a433446126e49316c150785a`.
Page6 was visually inspected; text on pages6–7 was checked against the tables.

The paper initializes stresses under gravity with **elastoplastic MC, drained
strength and no softening**, obtaining a stable state. It then switches to
undrained material parameters for dynamic failure. Its single-phase total-stress
formulation does not solve excess pore pressure. Stage1 mainly elastic response
does not mean plasticity is disabled. The paper also calibrates its softening
law at the field mesh scale; borrowing an exponential curve alone does not
reproduce that calibration.

Thus the old runner borrows aspects of the paper but is not its full method:
Zhan-like material/geometry inputs, a toe notch, elastic-only initialization,
and a generalized c/phi evolution are distinct adaptations. A future faithful
drained→undrained study needs its own parameter/state-transfer and equilibrium
contract; do not silently relabel the existing recipe as that study.

## Preserve the raw-versus-filtered result distinction

`scripts/plot_m5_urmi_long_cliff.py` recomputes bulk metrics from VTK. Its filter
keeps centres in x[0,102]m/y[0,18]m, displacement below35m and frame-average
speed below25m/s. It changes cohorts for crest/softening metrics and replaces
large native kinetic energy with a filtered finite-difference estimate when
native KE is at least10^7J. The removed IDs/mass are not reported there.

Consequently the summary's HS runout13.0667m/displacement13.5387m/KE22803J
are filtered quantities. The retained raw final CSV instead includes
runout156.787m/displacement307.990m/maxspeed92691m/s/KE5.147e11J. This is an
intentional difference of scope, not unexplained file corruption, but those
excluded numerical outliers prevent using the summary's PASS as whole-run
physical integrity. The raw VTKs exist locally(81states per case). Historical
manifests lack a source commit/hash snapshot, so today's source cannot prove
the exact historical numerical version. All old data/media are preserved.

## Next action toward unnotched failure

Close the already preregistered **single same-factor h0.5 resolution pair**;
its four new native groups and six Python binding controls have passed. This
changes no strength, notch, material law or initialization protocol. It tests
the present anchored-base model and is not a Urmi reproduction or guaranteed
landslide. After the pair, follow its finite stop rule. If it remains negative,
the user's Urmi hint identifies a useful separate next hypothesis: a genuinely
stable drained initialization followed by documented undrained softening,
using an unnotched geometry. That is a new material/loading experiment, not a
hidden tuning of the perfect-plastic control.

## Inspectable sources

- [H recipe](../../cases/cliff/cliff-urmi-long-mc-h.lisp),
  [HS recipe](../../cases/cliff/cliff-urmi-long-mc-hs.lisp),
  [runner](../../scenarios/cliff/execute.lisp),
  [geometry](../../scenarios/cliff/geometry.lisp).
- [Raw HS history](../../research/cliff/l-urmi-long-hs/cliff-timeseries.csv),
  [raw H history](../../research/cliff/l-urmi-long-h/cliff-timeseries.csv),
  [filtered summary](../../research/cliff/m5_urmi_long_summary.json),
  [filter implementation](../../scripts/plot_m5_urmi_long_cliff.py).
- [Current full-study case](../../cases/benchmarks/gravity-slope-mc-composite-apex-srf-1p6.lisp),
  [basal diagnostic and finite pair](UNNOTCHED_BASAL_REPRESENTATION.md).
