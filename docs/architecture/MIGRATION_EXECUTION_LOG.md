# Architecture migration execution log

## 2026-10-16 — P0 intake and audit

- Branch: `codex/material-architecture-migration`, created from `7c399fb`.
- Main refreshed as `efd0358`; open fork PRs #2/#3/#4/#6 inspected. No main edit,
  PR merge, upstream synchronization or new physics integration.
- User specification copied unchanged from Downloads to
  `docs/architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md`; SHA-256
  `40a4583286de05024869eedcfae7f08d6bd18444e0a4fa64c14cf2aa266734ca`.
- Initial inventory: 884 tracked paths at `7c399fb`. Dirty tracked wiki files
  and untracked evidence/settings are recorded separately and preserved.
- No native SBCL process is still running. Existing `64f47cc` VM 2D and 3D
  regressions both completed: 51 VTKs per dimension identical to baseline,
  positions/CSV differences zero; independent available-field audits PASS.
  Evidence: [current material-contract bundle](../evidence/material-contract-2026-10-16/README.md).
- Previous Joss serial control is exact PASS at executed `41403f4`; the original
  four-worker strict FAIL remains open. Full transitive FASL provenance and
  experimental physical validation are not established.
- P0 permits audit tooling/documentation only. No material/engine source has
  moved. The matrix covers all 884 captured paths exactly once across 29 roots;
  every path has a conservative decision and an explicit semantic-review scope.
  Native ASDF introspection found 104 systems across 11 definitions, with zero
  metadata errors. It did not execute engine source or a simulation.
- Existing ASDF declarations reference two absent tracked examples:
  `examples/dr/quasi-time.lisp` and `examples/octree/slope-stability.lisp`.
  Their availability is BLOCKED independently of migration; declarations and
  evidence are preserved. No missing example has been invented or activated.
- Material source audit records concrete's forward superclass and existing
  global definition replacements in damage/ice. Their order is part of the
  preserved baseline, not repaired under the guise of folder cleanup.

| Phase / gate | Current status | Exit evidence / next action |
| --- | --- | --- |
| P0 / G0 inventory | DONE, bounded inventory gate | 884/884 paths; 104 systems; 11 audit integrity tests PASS; only two P1 sources approved for extraction |
| P1 / G1 contracts | NOT_RUN | Central material contract ownership with tested compatibility |
| P2 model ownership | NOT_RUN | One family per checkpoint, exact forms/order/backend preserved |
| P3 material diagnostics/definitions | NOT_RUN | Separate model-owned and generic diagnostics; no duplicate implementation |
| P4 / G2 orchestration | NOT_RUN | Native engine assembly and scenario owners, legacy loaders retained |
| P5 engine internals | NOT_RUN | Only justified small changes with direct regression |
| P6 / G5 compatibility and cleanup | NOT_RUN; pre-existing example exceptions | Proven caller transition before removal; two missing legacy examples remain blocked |
| G3 numerical baseline | PASS for executed snapshots; parallel exception OPEN | Repeat affected controls on each migrated executed snapshot |
| G4 new MC H/HS physics | DEFERRED | Separate experimental branch; staged point prototype is not full MPM acceptance |

## Checkpoint discipline

Each stage appends changed paths/reason, source/form hashes, executed commit,
commands/exit codes, PASS/FAIL/NOT_RUN and evidence locations, known risks and
the next bounded action. Commit and push cohesive stages. If a gate fails,
retain its output, explain the cause before expensive investigation, and revert
or repair the stage without deleting history. Rollback uses a forward corrective
commit or a separate checkout of the recorded parent, never a destructive reset.

The former auto-continuation entry is currently unavailable: update returned
"Automation does not exist in the app" and its saved TOML is absent. It has not
been recreated or claimed active.

### P0 verification and next stage

Actual audit output is retained in `P0_AUDIT_VALIDATION.txt`: 11/11 integrity
checks, generation and `--check` passed. This proves inventory/approval guard
behavior, not numerical migration. `MIGRATION_APPROVALS.json` binds two reviewed
sources to exact pre-extraction hashes and concrete target/form lists. The other
882 semantic reviews remain pending; bulk migration is not approved. New tracked
checkpoint files are registered separately as NEW rather than silently added to
the immutable 884-path capture. [P1 extraction plan](P1_CONTRACT_EXTRACTION.md)
defines the next small change and its still-unexecuted regression requirements.
