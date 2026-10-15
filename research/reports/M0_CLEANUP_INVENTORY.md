# M0 cleanup inventory — 2026-10-15

Read-only review on `codex/reusable-simulation-framework`; root refreshed live
GitHub status this session (`main` `efd0358`, branch `4d141c3`). No files deleted,
tests run, or solvers launched. **No proven safe deletion candidate identified.**

| Exact path(s) examined | Evidence and decision |
| --- | --- |
| `calibration/triaxial.lisp`; `studio/lisp/{config,scenario,reference-joss}.lisp` | Keep: explicit compatibility loaders/adapters. `scripts/run-triaxial.lisp` copies and loads the calibration entry; Studio ASDF loads its adapters. Small size is intentional. |
| `framework/**/*.lisp` | Keep: enumerated by `framework/cl-mpm-framework.asd`; `scripts/run-case.lisp` snapshots and loads that system. |
| `analysis_scripts/make_video/{make_video,make_video2}.py` | Keep: different field semantics (`plastic_strain` versus `damage_ybar`) and input paths; filenames do not establish redundancy. |
| `analysis_scripts/{paper-2,pdf_maker}/poster_{bench,nobench}.pdf` | Keep: corresponding files have different SHA-256 hashes; equivalence/replaceability unproven. |
| `analysis_scripts/blender/test.blend1` | Defer: tracked historical backup (`45eca64`), 86,878,756 bytes versus current `.blend` 86,882,748 bytes. Unique recoverable state not audited. |
| `example_data/pullout/vary_l/.plot.py.swp` | Defer: tracked editor recovery artifact (`51c5c03`); unsaved-content equivalence unverified. |
| `libs/dr/a.out` | Defer: tracked historical native artifact (`9ef1187`); reproducible replacement unverified. |

Preserve `src/`, examples/dependencies, raw runs, negative evidence, active output,
and personal `.obsidian` directories. Search absence alone is insufficient proof
of disuse, especially for manually invoked analysis scripts.

`.gitignore` contains literal `]` and `2` patterns. Their purpose is uncertain;
removing them changes ignore semantics, so no cleanup is proposed. Existing
`*.swp`, compiled-cache, output and temporary-directory patterns already cover
routine local artifacts.
