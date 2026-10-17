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
| P4-F | Canonical root ASDF and active callers implemented; validation incomplete | `436b561`; Node 36 pass; final short native suite running under `p6-short/` |
| P5 | Useful numeric/linear-solver grouping complete | `59928ba`; byte-identical files, analytical solve and 50-step smoke pass |
| P6 | Final compatibility, results matrix, docs and PR pending | No main merge authorized |

Native source freezing is implemented and tested: selected source hashes,
private FASLs and the actual Windows copied DLL path are verified. Its 47-artifact
bundle is committed as `7e2aac3`. The first pre-step metadata-placement failure
is retained; the guard was preserved and the corrected run passes. Core ASDF
remains separate; the frozen CLI currently requires Windows.

Full P1 VM 2D/3D passed on `62adb50`. The newer full Joss run remains
STOPPED_BY_USER at 4.2 s and must not restart; historical exact serial results
remain separate. The parallel Joss failure is retained. Full G3 is PARTIAL.
Legacy global overrides, the concrete forward class and the atomic mixed C++
transaction remain explicit compatibility exceptions, not repaired physics.

Continue the existing stages and test only changed code. Preserve all negative
evidence, immutable raw sources, and personal Obsidian settings. The next native
test must follow an implementation commit, with a fresh output directory.

P2 A–D now installs all 49 approved material owners. Twenty post-move native
family catalogs match the five original baseline catalogs byte for byte. This
preserves class/slot/method identity, not scientific validation of every model.
P2-B/C/D bundles include launch hashes, extraction proofs, actual Windows DLL
paths, VTK/CSV comparisons and sealed live-unit sources. Node has 36 passing
tests at each wave; those finished checks must not be repeated without changes.

A separate fresh **four-second** serial Joss integration baseline is running
from immutable pre-P2 sources (`joss-bounded/before-003/`). It is not the cancelled 40-second run,
does not validate full collapse/run-out, and cannot close the full G3 exception.

The user requested a handover checkpoint before further work. Read
[NEXT_AI_CHECKPOINT.md](NEXT_AI_CHECKPOINT.md) first for active jobs, partial
checks, exact source commits and remaining actions. Final full VM 2D/3D on the
canonical layout and the final PR are NOT_RUN; old full results are historical.
