# Native hardening–softening comparative study

This is an illustrative numerical comparison of Mohr–Coulomb hardening-only
(H) and hardening–softening (HS), following the user's
[master plan](plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md).
It is not laboratory calibration or a validated CU prediction. UI work is outside
the scope. The existing solver and legacy material defaults remain the baseline.

## Current stage

The immediate priority is the [architecture migration specification](../docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md),
on `codex/material-architecture-migration` from `7c399fb`. P0/G0 requires complete
actual-file ownership, ASDF/caller and compatibility inventories before any move.
Root `materials/` is the target model owner; `framework/` remains temporary
compatibility. This target is not implemented. New MC physics is deferred until
migration gates, then belongs on a separate experimental branch.

| Milestone | Status | Next evidence required |
| --- | --- | --- |
| M0: native framework and contracts | PROVISIONAL | Current full VM 2D/3D exact PASS; four-worker FAIL and transitive FASL/DLL provenance limits remain |
| M1: source-aware reference data | COMPLETE (data preparation) | Nine integrity tests pass; runtime execution remains gated by M2 |
| M2: dedicated MC H/HS materials | PROVISIONAL (isolated staging), integration DEFERRED | 32 native point tests pass; migration gates, integration and spatial verification still required |
| M3: parameter verification | NOT RUN | Matched pre-peak, peak continuity, post-peak and return-map checks |
| M4: paired 3D triaxial | NOT RUN | 70 × 140 mm cylinders, 100/200 kPa, matched H/HS |
| M5: paired soil cliff | NOT RUN | Frozen geometry/loading, matched H/HS, numerical outputs and audits |
| M6: sensitivity and report | NOT RUN | Comparisons, limitations, commands and complete evidence status |

The full regression implementation was frozen as `64f47cc` on
`codex/reusable-simulation-framework`. Its 2D and 3D regressions each pass exactly
(51 VTKs byte-identical, all CSV/position differences zero); the four-worker Joss comparison fails the unchanged
strict criterion (176/191 frames). The paired one-worker control completed in
`output/framework-refactor-2026-10-15/joss-serial-before/` and `joss-serial-after/`.
Its 191 physical states, 193 VTK files per run and all CSV values are identical.
See [the source-audited serial report](reports/M0_SERIAL_REGRESSION.md).
Do not start duplicate runs or reinterpret the previous failure as a pass.
See [the retained evidence](../docs/evidence/framework-refactor-2026-10-15/README.md).

Current `64f47cc` diagnostics/configuration changes pass 9 material, 10 config,
10 framework contracts and all 36 Node tests. Full 2D (480 MPs) and 3D (780 MPs)
pairs completed exit 0, 17,443 updates, 51 states and 0.2 s; all independent
audits pass within available-field scope. The 2D export still lacks sigma_zz and
out-of-plane kinematics for full independent tensor checks. The completed
[evidence summary](../docs/evidence/material-contract-2026-10-16/validation-summary.json)
has 60 SHA-256-verified manifest entries. No native job remains running.
Byte identity of the listed private Joss numerical sources versus `41403f4`
does not constitute a new full Joss run at `64f47cc`.

The [MC design](reports/M2_RETURN_MAPPING_DESIGN.md) has an isolated, uninstalled
prototype in `.tmp/mc-evolution-stage/`, with 32/32 native material-point tests
passing. Root sampling has no completeness proof or adaptive continuation;
full MPM, calibration and M2 acceptance are not established. Preserve this staging
directory for review on the separate experimental branch.

Migration must preserve equations, algorithms, parameters, source availability
and historical entry points. P1–P6 and their migration verification are NOT RUN;
the saved baseline does not validate the target layout. M0 remains provisional
with its retained parallel failure and incomplete transitive loaded provenance.
No automatic merge to `main` is authorized.

## Source handling and reproducibility

- The copied master plan is byte-identical to the supplied file; its hash and
  source location are recorded in [source provenance](plans/source-provenance.json).
- The 28-page residual-soil presentation is available locally and its SHA-256
  matches the plan. Values are reference inputs, not experimental observations.
- Residual soil and Zhan's separate cliff reference must stay separate datasets.
  No automatic strain multiplier or fitting to slide images is permitted.
- Each native run needs a new output directory, effective configuration, source
  identity, numerical CSV/VTK, completion state and audit. Failed runs are retained.
- Commit cohesive changes and push each stage. Update the handover and linked wiki
  with exact PASS/FAIL/INCOMPLETE/NOT RUN scope, rather than silently relabeling old
  evidence as a new code revision.

## Human maintenance

Start with [framework usage](../docs/REUSABLE_FRAMEWORK.md) and
[the Windows native quickstart](../docs/QUICKSTART_WINDOWS_NATIVE.md).
Current executable cases belong in `cases/`; reusable assembly still lives in
`framework/` pending the audited migration to `src/simulation/` and `scenarios/`.
Model implementation will move to root `materials/` with compatibility evidence.
Reference data, parameter provenance and reports belong in `research/`.

M1 outputs are [source-aware values and provenance](references/PROVENANCE.md),
[four disabled reference proposals](configs/) and
[the data-only verification evidence](references/verification.json).
Run `python research/references/test_reference_data.py` to check their integrity.
They are not executable native configurations or a verified MC implementation.

Delete a file only after checking its callers, ASDF/native loading and documented
commands. Compatibility entry points, negative evidence, immutable sources,
active outputs and personal Obsidian settings must be preserved. A file without
a text-search match is not by itself proven unused.

The former continuation automation is unavailable/deleted; no next wakeup is
confirmed and no replacement is authorized without a new request. Use
[the operational handover](../docs/AI_HANDOVER.md) for the next bounded P0/G0 task.
