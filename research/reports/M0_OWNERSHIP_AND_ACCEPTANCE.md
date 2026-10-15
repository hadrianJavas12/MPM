# M0 ownership and acceptance gates

Checkpoint date: 2026-10-16. M0 is **PROVISIONAL** until the remaining code and
regression gates pass. Recording an exception does not complete its gate.

## Ownership boundaries

| Layer | Owns | Extension rule |
| --- | --- | --- |
| Native engine: `src/`, `libs/src/` | Constitutive integration, material state, momentum mapping and time integration | Dedicated material classes; justified engine fixes need direct controls and regression |
| Framework: `framework/components/`, `simulation.lisp` | Material/geometry/diagnostic contracts, assembly and run lifecycle | Validate capabilities; do not disguise an MC model as a VM subclass |
| Scenarios: `framework/scenarios/` | Geometry assembly, boundaries, loading, measurements and output schedules | Call material protocols; no duplicated constitutive equations |
| Cases: `cases/` | Short SI-based recipes and assignments | Select existing components; no global method replacement |
| Research: `research/` | Source-aware reference data, experiment definitions and evidence interpretation | Keep assumptions/source values and reference families distinct |
| Compatibility launchers | Historical native entry points | Retain documented commands and reject unsupported options explicitly |

The maintained fork's existing engine is the internal baseline. This stage does
not fetch or merge another repository or create an ongoing upstream-sync policy.
UI development remains excluded.

## Acceptance register

| Gate | Status at this checkpoint | Required next action |
| --- | --- | --- |
| Deterministic legacy 2D | PASS on snapshot `2f6476f` | Recheck the current generic-diagnostic implementation |
| Deterministic legacy Joss | PASS, exact, snapshot `41403f4` | Prove Joss numerical source identity after unrelated changes |
| Parallel Joss repeatability | OPEN EXCEPTION: four-worker strict FAIL | Retain exact evidence; do not claim deterministic parallel behavior |
| Current generic material diagnostics | IN PROGRESS | Native capability, reserved-output and unsupported-state contracts |
| Current legacy 3D regression | INCOMPLETE | Fresh frozen original is running; compare current after run with fixed criteria |
| Configuration integrity | IN PROGRESS | Unknown/duplicate input, physical range and no-side-effect rejection tests |
| M1 structured data | COMPLETE, data scope | Execution remains disabled until M2 mechanics/strain mapping verification |
| Human maintenance cleanup | REVIEWED | No safe deletion candidate proved; preserve historical recovery/evidence |
| New MC H/HS physics | NOT RUN | Separate branch, explicit strain/state and corner/apex verification |

## Licensing inventory

The tracked-file inventory found no repository-wide LICENSE, COPYING or NOTICE
file. Existing vendored license files include `deps/magicl/LICENSE.txt`,
`deps/magicl/expokit/LICENSE-expokit.txt` and `deps/vgplot/LICENSE`.
Their presence does not supply a license for the whole inherited engine.
An unsupported `MIT` declaration in the newly added framework ASDF metadata is
being removed in this M0 change; no license is invented or granted here.
Repository-wide inherited-code permissions and attribution remain an open
ownership item for a public/commercial release decision.

See the [material-contract audit](M0_MATERIAL_CONTRACT_AUDIT.md),
[cleanup inventory](M0_CLEANUP_INVENTORY.md),
[serial regression](M0_SERIAL_REGRESSION.md), and
[master plan](../plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md).
