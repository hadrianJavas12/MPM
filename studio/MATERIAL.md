# CL-MPM Studio material configuration

These controls configure the existing **`particle-chalk-delayed` constitutive
model** in `studio/lisp/scenario.lisp`. They do not implement a new material
law, make the simplified scenario identical to Joss Bay, or validate it for
prediction.

| Studio UI | JSON parameter | Lisp constructor argument | Units |
| --- | --- | --- | --- |
| Young's modulus | `E` | `:E` | Pa (UI displays GPa) |
| Poisson ratio | `nu` | `:nu` | dimensionless |
| Friction angle | `frictionAngle` | `:friction-angle`, `:phi` | degrees (phi converted to radians) |
| Cohesion | `cohesion` | `:c` | Pa (UI displays kPa) |
| Dilation angle | `dilatancyAngle` | `:psi` | degrees (converted to radians) |
| Plasticity enabled | `enablePlasticity` | `:enable-plasticity` | boolean |
| Damage enabled | `enableDamage` | `:enable-damage` and simulation damage flag | boolean |
| Damage onset | `initiationStress` | `:initiation-stress` | Pa (UI displays kPa) |
| Damage delay time | `delayTime` | `:delay-time` | s |
| Post-peak ductility | `ductility` | `:ductility` | dimensionless |
| Nonlocal interaction length | `nonlocalLength` | `:local-length` | m |

All new parameter defaults match the earlier hardcoded scenario values:
`cohesion = 1,000,000 Pa`, `dilatancyAngle = 0°`,
`nonlocalLength = 3 * sqrt(7) m` and `enablePlasticity = true`.
The `Elastic Gravity Settle` preset now disables **both plasticity and
damage**, so the pre-existing chalk constitutive model follows its elastic
branch. It does **not** switch the particle class.

`enableDamage` also sets each particle's `:enable-damage` flag. Custom elastic
templates require both damage and plasticity off; they do not replace the
separate damage-evolution API. See [CUSTOM_MODELS.md](CUSTOM_MODELS.md).

## Practical cautions

- Cohesion and tensile damage initiation stress describe distinct model
  quantities and should not be interchanged.
- The dilatancy angle controls plastic flow and typically should not exceed
  the friction angle without a specific physical justification.
- Nonlocal damage length influences localization and must be assessed
  together with the mesh size, particle resolution and fracture parameters.
- The current Studio time loop retains fixed mass scaling. Dynamic collapse
  results should not be interpreted as fully validated physical outcomes
  without the multi-phase solver and experimental/reference comparisons.
- Schema controls are intentionally clamped for numeric safety. They do not
  substitute for physical admissibility checks or calibration.

## Tests

`cd studio && npm run check && npm test` exercises JavaScript syntax and
parameter validation. It does not execute the Lisp solver. The physics
implementation still requires SBCL tests and reference-case validation.
