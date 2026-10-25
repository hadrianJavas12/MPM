# Exact saved strict/composite prefix comparison

First and only execution: 2026-10-26 05:54:11–05:54:18 WIB. Actual exit 0,
`PASS_EXACT_COMMON_PREFIX`. No solver, material replay, full audit or rendering.

The scope is the strict run's 18 actual saved states from 0 to 1.7 s. Exact
actual timestamps and captured particle IDs are used without interpolation or
numerical tolerance. This does not compare the later unsaved strict failure at
1.7334542479310375 s or validate the new model's subsequent trajectory.

- 18 aggregate history rows and 15,840 particle rows: selected CSV prefix bytes,
  headers, row order, strings, numeric doubles and IEEE representations match.
- All 18 VTK pairs: positions and all 38 common scalar fields, including IDs,
  match exactly. Complete VTK files differ because the new writer adds the two
  declared `mc-apex-active-last` and `mc-apex-lambda-last` fields.
- Copied comparator and reader hashes match before and after execution. The
  command, actual log/exit and exact executed support files are retained.

`result.json` contains per-file input hashes, CSV prefix hashes, per-field VTK
metrics and explicit non-validation flags. This is compatibility evidence for
the saved common prefix, not evidence of landslide or scientific validation.
