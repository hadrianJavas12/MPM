# Scientific audit evidence — 2026-10-15

See [the audit report](../../SCIENTIFIC_AUDIT_2026-10-15.md) for findings and
limitations. This bundle does not alter the accepted pilot or production solver.
`manifest.json` records source locations and exact captured-byte hashes.

- `forensic-artifacts-{audit,summary}.json`: all174 saved physical frames,
  mass/damage/position checks, log/CSV agreement, warm-start readback and hashes.
- `forensic-visual-audit.json`:174 exact PNG regenerations and175 decoded video
  frames compared against their corresponding PNGs.
- Matching Python scripts independently parse/check existing accepted artifacts.
- `native-invariant-controls.{lisp,log,json}` and `NATIVE_CONTROLS.md`: native
  disconnected-support aggregation and prescribed-displacement F-bar controls.
- `nonlocal-control.{lisp,log,json}`: native two-MP unnormalized kernel/averaging
  counterexample; exit0 means the counterexample was observed, not that the
  physical contract passed. See `symmetricKernelContractSatisfied=false`.
- `fresh-replay-*`: config/log/metadata/CSV, audit script and final VTK gzip
  from a new native process to4s, with1658 equilibrium updates and2 frames.
  The script compiler/cache entry is retained in the earlier pilot bundle.

The source scripts were executed under
`D:\MPM\output\scientific-audit-2026-10-15\`. Archive scripts keep those local
paths and may rely on original output artifacts. To repeat them, copy scripts
back there, retain the referenced accepted output files and use the Windows
launcher/Python runtime. These are audit tools, not automatic Studio components.
Raw paper page renders used for formula checking remain local; original paper
and supplied videos were not added to this bundle.

Representative commands from `D:\MPM`, after creating the audit output folder:

```powershell
windows\cl-mpm.cmd output\scientific-audit-2026-10-15\native-invariant-controls.lisp
windows\cl-mpm.cmd output\scientific-audit-2026-10-15\nonlocal-control.lisp
```

The controls intentionally prescribe tiny synthetic states, without replacing
production functions. They do not prescribe any state in the accepted collapse.
Native controls are counterexamples/kinematic checks, not full material tests.
Fresh4s replay supports genuine initiation; it is not a full40s rerun or proof
of physical calibration, energy balance, mesh convergence or paper equivalence.
