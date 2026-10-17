# Native material-contract and current framework regression evidence

Executed after source: **64f47cc**, committed before both full native runs.
Original 3D monolith: **c749d32**. Both use matched serial MPM/OpenBLAS/OMP
settings. This bundle records actual native Windows outputs, not generated
reference curves or scientific calibration.

| Control | Result |
| --- | --- |
| VM 2D, 480 MPs, 17,443 updates, 0.2 s | PASS: 51 VTK hashes identical; all position/CSV differences zero |
| VM 3D cylinder, 780 MPs, 17,443 updates, 0.2 s | PASS: 51 VTK hashes identical; all position/CSV differences zero |
| Independent consistency audits | PASS for exported fields; 2D full out-of-plane invariant reconstruction unavailable |
| Node / framework / material / configuration contracts | 36 / 10 / 9 / 10 PASS |
| Joss numerical private modules | Bytes identical to audited serial snapshot; no new full Joss run claimed |

`validation-summary.json` gives exact scope. `manifest.json` hashes retained
artifacts; compressed comparisons contain per-field fixed-tolerance results.
Each run retains numerical CSV, metadata and every particle VTK in tar.gz.
`sources/` holds executed source copies and audit/comparison code. The focused
material-contract report truthfully records that its working tree was hashed
after execution, unlike the frozen full regressions.

Native reproduction (fresh output directory, from repository root):

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\triaxial-clay-2d.lisp output\NEW-2d
& .\windows\cl-mpm.cmd scripts\run-case.lisp tests\cases\triaxial-3d-regression.lisp output\NEW-3d
```

Compare fresh outputs with `scripts/compare-framework-runs.py --baseline ...
--candidate ... --output ...`; audit with `scripts/audit-triaxial.py --run-dir ...`.
The saved effective configurations and sources identify the actual baseline.
Use a checkout of `64f47cc` to reproduce this historical implementation exactly.

Mass is constant in each run. The discretized 3D cylinder volume exceeds its
nominal analytical volume by about 3.45%; this is reported by the audit, not
hidden by rescaling particles. No mesh/rate convergence, pore-pressure CU,
experimental calibration or closed signed energy budget is established.
M0 remains PROVISIONAL: the earlier four-worker Joss strict failure and incomplete
transitive dependency provenance remain open. See the separate serial/failure
[framework evidence](../framework-refactor-2026-10-15/README.md).
