# Native hardening–softening comparative study

This is an illustrative numerical comparison of Mohr–Coulomb hardening-only
(H) and hardening–softening (HS), following the user's
[master plan](plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md).
It is not laboratory calibration or a validated CU prediction. UI work is outside
the scope. The existing solver and legacy material defaults remain the baseline.

## Current stage

| Milestone | Status | Next evidence required |
| --- | --- | --- |
| M0: native framework and contracts | PROVISIONAL | Generic contracts and current 2D pass; current 3D regression running; four-worker exception retained |
| M1: source-aware reference data | COMPLETE (data preparation) | Nine integrity tests pass; runtime execution remains gated by M2 |
| M2: dedicated MC H/HS materials | PROVISIONAL (isolated staging) | 32 native point tests pass; review, complete integration and spatial verification still required |
| M3: parameter verification | NOT RUN | Matched pre-peak, peak continuity, post-peak and return-map checks |
| M4: paired 3D triaxial | NOT RUN | 70 × 140 mm cylinders, 100/200 kPa, matched H/HS |
| M5: paired soil cliff | NOT RUN | Frozen geometry/loading, matched H/HS, numerical outputs and audits |
| M6: sensitivity and report | NOT RUN | Comparisons, limitations, commands and complete evidence status |

The latest implementation checkpoint was pushed as `64f47cc` on
`codex/reusable-simulation-framework`. Its 2D regression passes exactly (51 VTKs,
all CSV differences zero); the four-worker Joss comparison fails the unchanged
strict criterion (176/191 frames). The paired one-worker control completed in
`output/framework-refactor-2026-10-15/joss-serial-before/` and `joss-serial-after/`.
Its 191 physical states, 193 VTK files per run and all CSV values are identical.
See [the source-audited serial report](reports/M0_SERIAL_REGRESSION.md).
Do not start duplicate runs or reinterpret the previous failure as a pass.
See [the retained evidence](../docs/evidence/framework-refactor-2026-10-15/README.md).

Current `64f47cc` diagnostics/configuration changes pass 9 material, 10 config,
10 framework contracts and all 36 Node tests. Its full 2D rerun again has 51
byte-identical VTKs and zero CSV differences; the independent available-field
audit passes. The fresh original 3D baseline finished successfully; the matched
after run remains in progress. Do not declare 3D equivalence before comparison.

The [MC design](reports/M2_RETURN_MAPPING_DESIGN.md) has an isolated, uninstalled
prototype in `.tmp/mc-evolution-stage/`, with 32/32 native material-point tests
passing. Root sampling has no completeness proof or adaptive continuation;
full MPM, calibration and M2 acceptance are not established. Preserve this staging
directory for review on the separate experimental branch.

New constitutive physics will use a separate experimental branch based on the
refactor checkpoint. An unresolved Joss result remains an explicit framework
acceptance exception; independent controlled work may proceed as the plan allows.
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
Small executable cases belong in `cases/`; reusable assembly belongs in
`framework/`; material equations belong in the native material layer.
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

Automatic continuation is scheduled after the next observed usage reset and
every five hours thereafter. Use [the operational handover](../docs/AI_HANDOVER.md)
for the next bounded task; avoid active polling while native jobs run.
