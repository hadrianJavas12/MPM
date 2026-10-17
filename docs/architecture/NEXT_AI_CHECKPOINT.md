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
| P4-F partial validation | launch HEAD `326268a`; `p6-short/` | Snapshot 3, native snapshot 7, standalone calibration 3 all exit 0; no production/test fixes needed |
| Node at F | `p4-f/node-{check,tests}.log`, `node-status.json` | Syntax check and 36 tests pass, zero failed/skipped |

Evidence directories above are under
`docs/evidence/architecture-migration-2026-10-16/`; working runs are under
`output/architecture-migration-2026-10-16/`. Source/CLOS compatibility and
numerical regression are distinct from scientific validation.
F partial evidence is saved in `p6-short/` (20 hashes, 252 sealed source files);
Node logs/status are additionally committed in `p4-f-node/` (4 hashes).

P2's chosen plan is `P2_COMPACT_MIGRATION.json`: 23 original sources/495 audited
forms/49 cohesive targets. The 109-fragment plan is an unused audit alternative.
P4 plan was committed at `f3a57ae` before moves. `p4/migration-state.json` now
contains B/C/D/E/F. **Do not apply the migration helpers again.**

## Active job and preserved failures

One independent **old-source four-second serial Joss baseline** was already
launched: `output/architecture-migration-2026-10-16/joss-bounded/before-003/`.
Last inspected wrapper PID **39560**, cmd **8832**, native SBCL **45988**.
Treat PIDs as observations, not proof they remain alive. Read:

1. `before-003-status.json` if present, else launch metadata/process existence.
2. `before-003/reference-metadata.json`: `complete`, physical time, termination.
3. One last line of `before-003.stdout.log`; stderr if failure is observed.

Last observed was settling iteration 350; completion was not established.
Never duplicate this job or actively poll it. It uses verified immutable pre-P2
source bytes copied from `native-freeze/triaxial-short-002/source/`, old CLI,
private FASLs and copied native DLL. Physics/settings match the committed
`tests/cases/joss-serial-integration.lisp`: one worker, 4 s, frame cap 10.
This is not the cancelled 40 s simulation or full-collapse acceptance.

`before-001` failed before native stepping because a quoted Windows argument
ended with a backslash and merged arguments. `before-002` failed before stepping
because old path guards resolved a missing empty `studio/lisp/` registry root.
Both failures/logs are retained. `2fee283` fixes argument/log capture;
`326268a` supplies the empty directory, without replacing numerical source.
`scripts/prepare-joss-bounded-baseline.py --verify-retry --attempt before-003`
checks prepared inputs without launching a solver. Preserve these failed attempts.

The F short-suite Python controller **34140** was deliberately terminated for
the human handover. Its command exit 1 means **USER_STOPPED_QUEUE**, not a failed
native assertion. Already-launched standalone wrapper 32920 finished exit 0;
no F short-suite process remains. Do not restart the whole eleven-check queue.

## Remaining implementation/validation work

1. Read saved final short statuses first. Already completed snapshot3/native7/
   standalone3/Node36 must not rerun. Remaining F checks were **NOT_RUN**:
   orchestration F (4 assertions), engine smoke 50 updates, ownership normal/
   legacy, diagnostic legacy, custom delegate, bounded cliff MC, and the changed
   `scripts/run-triaxial.lisp` copied legacy-source loader.
   Use fresh named outputs and existing `p6-short/run-check.ps1`; inspect its
   arguments/legacy-config before use. Preserve source launch hashes.
2. Full final-layout VM 2D and 3D are **NOT_RUN**. Prepared but never launched:
   `p6-full/launch-triaxial-2d.ps1`, `launch-triaxial-3d.ps1`.
   They run native once, strict compare against completed P1-full `62adb50`,
   and independent audit after exit 0. Both historical baselines have 51 VTKs,
   17,443 updates, 0.2 s, all native/compare/audit exits 0. Do not rerun baselines.
   Helper `.tmp/launch-migration-p6-full.py` exists; inspect wrappers, do not
   regenerate/overwrite prepared evidence. Snapshot code before permitting edits.
3. Once old bounded Joss baseline actually completes, run the same 4 s case once
   on final canonical code with a fresh frozen output. Strictly compare whole
   outputs at matching states, unchanged tolerances, no interpolation/cropping.
   No current-source after run has been launched yet. Preserve failures honestly.
4. Run `scripts/report-architecture-migration.py` for the final path/hash ledger
   without changing P0. Every original path must appear once; target existence
   is not a test PASS. Preserve old LOAD wrappers while compatibility is needed.
5. Final evidence collector, updated `STATUS.md`, `docs/testing.md`, human guide,
   handover and wiki/index/append-only log; commit/push coherent checkpoints.
   Make PR to main and attach it in Codex. **Do not merge.**

Useful ignored helpers remain under `.tmp/`; stage extraction originals/proofs
are under `output/.../p2-*-before/` and `p4/original/`, `p4/stage-*/`.
Committed evidence bundles include their reproducibility support. Do not waste
tokens rebuilding inventories, catalog baselines, plans, or completed tests.

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
