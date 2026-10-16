# M0 ownership and acceptance gates

Checkpoint date: 2026-10-16. M0 remains **PROVISIONAL** despite completed exact
current VM 2D/3D controls: four-worker Joss strict FAIL and incomplete transitive
loaded FASL/DLL provenance remain open. Recording an exception does not pass it.

The [architecture specification](../../docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md)
now governs migration on `codex/material-architecture-migration`, from `7c399fb`.
The following current owners are transitional. P0/G0 must map every actual tracked
path, untracked work, ASDF/load/caller and mixed-source form before any move.

## Ownership boundaries

| Layer | Owns | Extension rule |
| --- | --- | --- |
| Native engine: `src/`, `libs/src/` | Constitutive integration, material state, momentum mapping and time integration | Dedicated material classes; justified engine fixes need direct controls and regression |
| Framework: `framework/components/`, `simulation.lisp` | Material/geometry/diagnostic contracts, assembly and run lifecycle | Validate capabilities; do not disguise an MC model as a VM subclass |
| Scenarios: `framework/scenarios/` | Geometry assembly, boundaries, loading, measurements and output schedules | Call material protocols; no duplicated constitutive equations |
| Cases: `cases/` | Short SI-based recipes and assignments | Select existing components; no global method replacement |
| Research: `research/` | Source-aware reference data, experiment definitions and evidence interpretation | Keep assumptions/source values and reference families distinct |
| Compatibility launchers | Historical native entry points | Retain documented commands and reject unsupported options explicitly |

The target moves model implementation/state/evolution/diagnostics to root
`materials/`, generic engine/numerics/orchestration to `src/`, and reusable
procedures to `scenarios/`. Material definitions remain parameter/provenance
profiles; model-specific laws stay with their model. This is a target design,
not an implemented migration. `framework/` remains compatibility until G5 proves
caller transition. Numerical algorithms, parameters and legacy defaults must not
change as a side effect of file ownership. P1–P6 remain NOT RUN here.

The maintained fork's existing engine is the internal baseline. This stage does
not fetch or merge another repository or create an ongoing upstream-sync policy.
UI development remains excluded.

## Acceptance register

| Gate | Status at this checkpoint | Required next action |
| --- | --- | --- |
| Deterministic legacy 2D | PASS, exact, executed `64f47cc` | 480 MPs, 17,443 updates, 51 VTKs byte-identical; all CSV/position differences zero; available-field audits PASS |
| Deterministic legacy Joss | PASS, exact, snapshot `41403f4` | Listed private numerical modules remain byte-identical; this is not a new full Joss run at `64f47cc` |
| Parallel Joss repeatability | OPEN EXCEPTION: four-worker strict FAIL | Retain exact evidence; do not claim deterministic parallel behavior |
| Current generic material diagnostics | PASS, focused 9/9 | Actual VM/MC/elastic identity, capability/output guards and bounded two-update MC smoke; no new H/HS physics |
| Current legacy 3D regression | PASS, exact, executed `64f47cc` | Original `c749d32`; both exit 0, 780 MPs, 17,443 updates, 51 VTKs byte-identical, all CSV/position differences zero; audits PASS |
| Configuration integrity | PASS, 10/10 | Input/range/mode/null/duplicate rejection, isolation and JSON false behavior |
| Complete loaded dependency provenance | INCOMPLETE | Source/binary hashes do not establish all transitive loaded FASL/DLL bytes |
| Migration P0/G0 | IN PROGRESS, not accepted | Initial 884-path snapshot at `7c399fb`; complete semantic/caller/ASDF audit and baseline register before moves |
| M1 structured data | COMPLETE, data scope | Execution remains disabled until M2 mechanics/strain mapping verification |
| Human maintenance cleanup | REVIEWED | No safe deletion candidate proved; preserve historical recovery/evidence |
| New MC H/HS physics | DEFERRED | Uninstalled 32/32 point prototype only; migration gates before separate experimental branch/integration |

The [completed material-contract evidence](../../docs/evidence/material-contract-2026-10-16/validation-summary.json)
has 60 SHA-256-verified manifest entries. No native process remains running.
All independent audits pass within available-field scope; 2D sigma_zz and
out-of-plane kinematics are absent from VTK, so full independent tensor checks
remain unavailable. None of these controls establishes calibration, convergence,
a closed energy budget or post-migration compatibility.

## Licensing inventory

The tracked-file inventory found no repository-wide LICENSE, COPYING or NOTICE
file. Existing vendored license files include `deps/magicl/LICENSE.txt`,
`deps/magicl/expokit/LICENSE-expokit.txt` and `deps/vgplot/LICENSE`.
Their presence does not supply a license for the whole inherited engine.
The unsupported `MIT` declaration was removed from framework ASDF metadata;
no repository-wide license is invented or granted here.
Repository-wide inherited-code permissions and attribution remain an open
ownership item for a public/commercial release decision.

See the [material-contract audit](M0_MATERIAL_CONTRACT_AUDIT.md),
[cleanup inventory](M0_CLEANUP_INVENTORY.md),
[serial regression](M0_SERIAL_REGRESSION.md), and
[master plan](../plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md).
