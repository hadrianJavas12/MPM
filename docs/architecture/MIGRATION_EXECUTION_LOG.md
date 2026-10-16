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

## P1 implementation checkpoint — validation pending

P0 was committed and pushed as **6f15148 before any production extraction**.
The two approved sources now forward to their new owners. Sixteen existing
defining forms were extracted with identical body bytes; the native factory
file was copied byte-identically. Evidence before sources and form hashes:
`output/architecture-migration-2026-10-16/p1-source-before/` and
`p1-extraction-form-hashes.json`.

ASDF preserves the old specification/factory component IDs with relative owner
paths and explicit base/material-definition prerequisites. The CLI copies the
new ownership trees, compares each copy byte-for-byte, and verifies all framework
source component paths lie within the frozen source root **before** loading.
It records those paths; the external collector supplies SHA-256 manifests.
Native engine/FASL/DLL identity remains a separate, limited provenance scope.

No constitutive algorithm, particle ancestry, numerical parameter or tolerance
was changed. P1 compatibility/native/Node and full numerical tests are **NOT_RUN**
at this implementation checkpoint; neither P1 nor G1 is declared complete.

### P1 bounded verification after 3cd172e

Actual checks pass: 10 framework, 10 configuration, 9 material diagnostics,
7 normal and 7 legacy ownership, 3 snapshot-boundary checks, Node syntax and
36 tests with zero skips. VM 27-update and MC two-update triaxial controls pass
the unchanged strict comparator with zero position/CSV differences. Both saved
native MC cliff VTKs are byte-identical to the prior control.

The initial ownership test failed due to its incorrect hardcoded SBCL class
tail; an original-source control proves `SLOT-OBJECT` was already present. The
first snapshot negative fixture still preferred the frozen registry; its setup
was corrected so the unchanged guard now rejects actual checkout paths.
Both failed logs remain retained. No numerical assertion/tolerance was changed.
The cliff control reports an unavailable gnuplot PNG; plotting is not PASS.

[Bounded evidence](../evidence/architecture-migration-2026-10-16/p1/README.md)
retains 32 hash-verified artifacts, actual source copies, VTK/CSV, all logs and
form-byte comparisons. P1 remains PROVISIONAL/G1 PARTIAL pending deeper owner
migration and full G3 runs. P2 is only a conditional plan, not execution approval.
