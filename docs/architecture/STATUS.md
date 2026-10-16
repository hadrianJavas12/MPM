# Architecture migration status

Updated 2026-10-16. This table overrides earlier checkpoint descriptions, which
remain historical evidence. The supplied migration specification and immutable
P0 inventory remain the authority for scope.

| Stage | Current state | Evidence |
| --- | --- | --- |
| P0 | Complete inventory and dependency audit | `6f15148`; 884 original paths, 104 ASDF systems |
| P1 | Contract owners extracted, compatible old source loaders | `62adb50`; focused contracts and bounded controls |
| P2-A | Constitutive laws/native bridge extracted; arithmetic bodies unchanged | `4ed46b4`; five catalogs byte-identical, strict VM/MC controls pass, native MC 9 and ownership 7, Node 36 |
| P2-B/C/D | Remaining material state, damage/evolution and optional families pending | Committed compact plan: 23 sources, 495 forms, 49 cohesive targets |
| P3 | Diagnostics/material output owners extracted and tested | `7d879e8`; 37 verified artifacts |
| P4 | Orchestration/scenario migration approved; implementation pending | Plan `f3a57ae`; guarded B/C/D/E/F helper ready |
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
