# Architecture migration status

Updated 2026-10-17. This table overrides earlier checkpoint descriptions, which
remain historical evidence. The supplied migration specification and immutable
P0 inventory remain the authority for scope.

| Stage | Current state | Evidence |
| --- | --- | --- |
| P0 | Complete inventory and dependency audit | `6f15148`; 884 original paths, 104 ASDF systems |
| P1 | Contract owners extracted, compatible old source loaders | `62adb50`; focused contracts and bounded controls |
| P2-A | Constitutive laws/native bridge extracted; arithmetic bodies unchanged | `4ed46b4`; five catalogs byte-identical, strict VM/MC controls pass, native MC 9 and ownership 7, Node 36 |
| P2-B | Particle/material state owners extracted | `5a1501b`; five catalogs exact, VM/MC controls exact; 57 evidence hashes |
| P2-C | Damage/evolution owners extracted | `791dd64`; five catalogs exact, VM/MC and cliff controls exact; custom delegate passes; 74 evidence hashes |
| P2-D | Optional chalk, ice, limestone and visco owners extracted | `a016cdb`; five catalogs exact, VM/MC controls exact; 58 evidence hashes |
| P3 | Diagnostics/material output owners extracted and tested | `7d879e8`; 37 verified artifacts |
| P4-B/C/D | Configuration, geometry, lifecycle and scenario owners relocated | `76cac13`, `f76618d`, `f9ba947`; bounded comparisons and compatibility contracts pass |
| P4-E | Nested legacy material diagnostics/state transfer extracted and tested | `d6d3f61`; exact reconstruction; standalone 3, orchestration 3, VM/MC strict comparisons pass; 34 evidence hashes |
| P4-F | Canonical root ASDF and active callers implemented and validated | `436b561` / `9dfb58b`; Node 36 pass; all 11 `p6-short/` native checks pass (64 evidence hashes); full VM 2D/3D `p6-full/` exact PASS vs `p1-full` |
| P5 | Useful numeric/linear-solver grouping complete | `59928ba`; byte-identical files, analytical solve and 50-step smoke pass |
| P6 | Final compatibility, results ledger (`FILE_MIGRATION_RESULT.json`), bounded 4s Joss control, full VM 2D/3D regressions, docs/wiki and PR complete | `58/58` mapped owners present; no `main` merge authorized |

Native source freezing is implemented and tested: selected source hashes,
private FASLs and the actual Windows copied DLL path are verified. Its 47-artifact
bundle is committed as `7e2aac3`. The first pre-step metadata-placement failure
is retained; the guard was preserved and the corrected run passes. Core ASDF
remains separate; the frozen CLI currently requires Windows.

Full P1 VM 2D/3D passed on `62adb50`, and full final-layout P6 VM 2D (480 MPs,
17,443 updates, 51 states) and VM 3D (780 MPs, 17,443 updates, 51 states) passed
on `9dfb58b` with all 51 VTKs per run and `stress-strain.csv` byte-identical to
`p1-full` (`0` position/CSV/field difference; independent audits PASS).
The 40-second full Joss run on `62adb50` remains `STOPPED_BY_USER` at 4.2 s and
was not restarted; historical exact 40-second serial results (`c749d32` vs `41403f4`)
remain separate. The historical 4-worker parallel Joss failure is retained.
Full G3 and G1 remain `PARTIAL`: legacy global overrides in damage/ice, the
concrete forward class, and the atomic mixed C++ transaction remain explicit
compatibility exceptions, not repaired physics.

P2 A–D installs all 49 approved material owners. Twenty post-move native
family catalogs match the five original baseline catalogs byte for byte. This
preserves class/slot/method identity, not scientific validation of every model.
P2-B/C/D bundles include launch hashes, extraction proofs, actual Windows DLL
paths, VTK/CSV comparisons and sealed live-unit sources. Node has 36 passing
tests at each wave.

The separate fresh **four-second** serial Joss integration control (`joss-bounded/`)
completed on both immutable pre-P2 sources (`before-003`, `a99a4e1` / `7e2aac3`)
and canonical final-layout sources (`after-001`, `9dfb58b`): both finished 1,658
elastic equilibration steps and reached 4.0 s physical time (`exit 0`), with
byte-identical `equilibrium.vtk`, `sim_00001.vtk`, and `sim_00002.vtk` and zero
position/field/CSV differences (`54` verified evidence artifacts). It is a
bounded initiation control, not the cancelled 40-second run, and does not close
the full G3 exception.

`docs/architecture/FILE_MIGRATION_RESULT.json` records all 884 original P0 paths
without mutating `FILE_MIGRATION_MATRIX.json`: following the explicit user-directed
Section 2/5 physical directory alignment (`5d6a5cf`), `749` paths are
`RETAINED_UNCHANGED`, `15` are `RETAINED_MODIFIED`, and `120/120` are
`MAPPED_OWNERS_PRESENT` (`0` pending). Legacy `framework/`, `src/models/`, and
root `src/` forwarding shims are retired, `src/` is organized into the 15 Section 2
engine subdirectories, and `cases/` is organized into `cases/{triaxial,cliff,benchmarks,direct-shear}/`
(two pre-existing absent legacy example paths `examples/dr/quasi-time.lisp` and
`examples/octree/slope-stability.lisp` remain documented `BLOCKED` exceptions).

On the aligned Section 2 directory tree (`5d6a5cf`), all contract suites (`smoke-test`,
`engine-numerics-compat`, `material-ownership-compat` normal/legacy,
`p4-orchestration-compat`, `framework-components`, `config-contracts`,
`material-diagnostics`, `p4-standalone-triaxial-compat`, `case-snapshot-contracts`,
`native-snapshot-contracts`, and Studio Node `npm run check` + `36/36` `npm test`)
pass (`exit 0`), and the two primary user-requested benchmarks pass:
1. **Triaxial 2D (`cases/triaxial/triaxial-clay-2d.lisp`)**: 480 MPs, 17,443 updates,
   51 saved VTK states (`section2-benchmarks/triaxial-2d`); all 51 VTKs and
   `stress-strain.csv` are byte-identical (`SHA-256` match) to `p1-full/triaxial-2d`
   (`max_position_difference_m = 0.0`, `audit-triaxial.py` `passed_consistency_checks = true`).
2. **Joss Bay bottom-to-top progressive cliff damage (`tests/cases/joss-serial-integration.lisp`
   and `cases/benchmarks/joss-collapse.lisp`)**: bounded 4.0 s serial control
   (`section2-benchmarks/joss-serial-4s`) completes 1,658 equilibration steps and 4.0 s
   with `initial.vtk`, `mesh.vtk`, `equilibrium.vtk`, `sim_00001.vtk`, and `sim_00002.vtk`
   byte-identical (`SHA-256` match) to `joss-bounded/before-003`, initiating lower
   notch/toe damage ($y \le 4\text{ m}$, `lower_max_damage = 0.3336` at `[13.125, 3.625]`)
   while upper cliff damage ($y \ge 9\text{ m}$) is `0.0`, followed by progressive
   bottom-to-top upward propagation (`section2-benchmarks/joss-collapse`).
