# Architecture migration — next AI checkpoint

Prepared **2026-10-17, Asia/Jakarta**, at the user's explicit request to
document/commit before continuing with another AI. This checkpoint overrides
older "next actions" in the append-only history. **Do not start another run
until checking existing processes and saved statuses.**

## Repository and scope

- Workspace: `D:\MPM`; branch `codex/material-architecture-migration`.
- Production P4-F: `436b561`. Latest implementation/support HEAD before this
  documentation checkpoint: `326268a2b6e1441c5c8a9947e83427e0fc16e34f`.
  The latter fixes the isolated old-baseline preparation, not material math.
- Remote main last checked at `efd0358b7f571e738c0ecc022c4313fb7fca0d15`.
  Refresh live GitHub status before new changes. No migration PR created yet.
- Governing document: [migration specification](CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md).
  Scientific M0–M6/MC H/HS experiments are separate, not part of folder cleanup.
- User wants all architecture stages completed, regressions, commit/push and
  PR to main. **No merge/main modification, UI feature, new physics, upstream
  sync, force push, or deletion of unproven code/evidence.**
- Latest instruction is handover first. Further test launches were stopped;
  existing independently running bounded baseline was preserved.

## What is already done — do not repeat

| Work | Source / evidence | Verified scope |
| --- | --- | --- |
| P0 | `6f15148`; immutable `FILE_MIGRATION_MATRIX.json` | 884 original paths, 104 ASDF systems; do not regenerate original inventory |
| P1/P3 | `62adb50`, `7d879e8` | Contracts, diagnostics, native controls; P3 37 evidence hashes |
| P5 | `59928ba`; `p5/` 12 hashes | Whole-file exact numeric/linear solver relocation; analytical controls and 100-MP/50-update smoke |
| Native freezing | `7e2aac3`; `native-freeze/` 47 hashes | Copied ASDF sources/private FASLs, hashed performed inputs, actual Windows copied DLL path; VM/MC controls |
| P2 A–D | `4ed46b4`, `5a1501b`, `791dd64`, `a016cdb` | All 49 approved native material owners; twenty post-move catalogs exact against five baseline catalogs |
| P4 B/C/D | `76cac13`, `f76618d`, `f9ba947` | Config/geometry/lifecycle/scenarios relocated; compatibility and bounded numerical controls pass |
| P2 wave evidence | `p2-a/` 42, `p2-b/` 57, `p2-c/` 74, `p2-d/` 58 hashes | Each VM/MC saved VTK pair and CSV exact versus previous wave; real Windows runs, no tolerance changes |
| P4-E | `d6d3f61`, executed `06eba1e`; `p4-e/` 34 hashes | Standalone 3, orchestration 3, VM 27 updates, MC diagnostics 9; strict comparisons and saved VTK/CSV exact versus D |
| P4-F implementation | `436b561` | Root canonical `cl-mpm-framework.asd`, active Windows/Studio config/calibration callers and snapshot tests updated |
| P4-F & P6 short suite | `326268a` / `9dfb58b`; `p6-short/` 64 hashes | All 11 short native checks pass (`exit 0`), 252 sealed source files verified; initial PS 5.1 `p4-orchestration` stderr wrapper exception retained alongside passing `p4-orchestration-002` |
| Node at F | `p4-f-node/` 4 hashes | Syntax check and 36 tests pass, zero failed/skipped |
| Bounded 4s serial Joss control | `joss-bounded/` 54 hashes | `before-003` (`a99a4e1` / `7e2aac3`) vs `after-001` (`9dfb58b`): both 1,658 equilibration steps, 4.0 s, `exit 0`; `equilibrium.vtk`, `sim_00001.vtk`, `sim_00002.vtk` byte-identical, zero diff; failed attempts `before-001`/`before-002` retained |
| Full final-layout VM 2D & 3D | `9dfb58b`; `p6-full/` 38 hashes | `triaxial-2d` (480 MPs, 17,443 updates, 51 states) and `triaxial-3d` (780 MPs, 17,443 updates, 51 states) both `exit 0`; all 51 VTKs per run and `stress-strain.csv` byte-identical to `p1-full` (`62adb50`); strict comparisons and independent audits PASS |
| Ownership result ledger | `FILE_MIGRATION_RESULT.json`, `COMPONENTS.md` | All 884 P0 paths accounted for without mutating `FILE_MIGRATION_MATRIX.json`: `812` `RETAINED_UNCHANGED`, `14` `RETAINED_MODIFIED`, `58/58` `MAPPED_OWNERS_PRESENT` (`0` pending) |

Evidence directories above are under
`docs/evidence/architecture-migration-2026-10-16/`; working runs are under
`output/architecture-migration-2026-10-16/`. Source/CLOS compatibility and
numerical regression are distinct from scientific validation.

P2's chosen plan is `P2_COMPACT_MIGRATION.json`: 23 original sources/495 audited
forms/49 cohesive targets. The 109-fragment plan is an unused audit alternative.
P4 plan was committed at `f3a57ae` before moves. `p4/migration-state.json` now
contains B/C/D/E/F. **Do not apply the migration helpers again.**

## Completed post-handover execution (no active native jobs remain)

1. All 8 remaining `p6-short/` checks (`p4-orchestration-002`, `engine-smoke`,
   `ownership-normal`, `ownership-legacy`, `diagnostics-legacy`, `custom-delegate`,
   `cliff-mc`, `legacy-triaxial`) completed with `exit 0` under `pwsh.exe` and
   are packaged in `docs/evidence/architecture-migration-2026-10-16/p6-short/` (64 hashes).
   Note: use PowerShell 7 (`pwsh.exe`), not Windows PowerShell 5.1 (`powershell.exe`),
   when running wrappers that redirect SBCL `stderr` with `$ErrorActionPreference = 'Stop'`.
2. Pre-P2 4-second serial Joss baseline `before-003` completed (`exit 0`, 1,658
   equilibration steps, 4.0 s), and the matched canonical final-layout run `after-001`
   completed (`exit 0`) with byte-identical VTKs and zero position/field/CSV differences;
   packaged in `docs/evidence/architecture-migration-2026-10-16/joss-bounded/` (54 hashes).
3. Full final-layout VM Triaxial 2D and 3D regressions completed (`exit 0`) with all
   51 VTKs per run and `stress-strain.csv` byte-identical to `p1-full` (`62adb50`);
   packaged in `docs/evidence/architecture-migration-2026-10-16/p6-full/` (38 hashes).
4. `docs/architecture/COMPONENTS.md` and `docs/architecture/FILE_MIGRATION_RESULT.json`
   are generated (`58/58` `MAPPED_OWNERS_PRESENT`), documentation and `wiki-vault/` are
   updated, and the branch is ready for PR review against `main` (**do not merge without
   express user direction**).

## Scientific and compatibility exceptions

- New full Joss remains STOPPED_BY_USER/INCOMPLETE at 4.2 s. **Never restart it.**
  Historical original `c749d32` versus executed `41403f4` serial 40 s was exact
  (191 states/193 VTKs); four-worker strict regression failed and stays failed.
- G1/G3 remain PARTIAL. Existing damage/ice global overrides, concrete forward
  superclass and atomic mixed native C++ success/fallback transaction remain
  explicit exceptions. Relocation does not fix them or validate optional models.
- `framework/` is now old-path forwarding loaders/ASDF forwarder, not an owner.
  Retained wrappers are deliberate compatibility exceptions; don't delete them
  merely to satisfy a directory picture. Common particle slots remain engine-owned.
- Windows source freezing verifies selected first-party ASDF sources and mapped
  copied DLL, not all third-party modules or arbitrary trusted non-ASDF LOADs.
- PNG plotting remains unresolved; do not mark it PASS. Existing CI billing lock
  remains open until actual new hosted execution proves otherwise.
- 2D triaxial is plane strain; assumed clay strength is not lab calibration or
  a pore-pressure-coupled CU model. New MC H/HS belongs on a separate experiment.

## Local state and handover operations

Keep these pre-existing user/local changes unstaged: `tests/diagnostics-ownership-compat.lisp`,
`wiki-vault/AGENTS.md`, `wiki-vault/wiki/joss-reference-reproduction.md` (observed
CRLF-only/no text diff), plus untracked personal `.obsidian/` directories.
Do not restore, delete, stage or change private settings/raw sources.

The automatic five-hour continuation was paused for this explicit handover to
avoid concurrent edits. Resume only when the human directs continuation.
Latest observed quota: primary 1%, weekly 95% consumed; those are observations,
not promises of future availability. Check current limits only when needed.
Use compact status reads and offline native wrappers; no busy polling.
