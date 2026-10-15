# M0 paired serial Joss regression — 2026-10-16

**PASS for the paired serial control.** The unchanged strict comparator reports
191 before and 191 after physical states through 40 s, with zero differences in
positions, all 36 exported scalar fields and recorded CSV numeric columns.
Absolute tolerance remains `1e-8`, relative tolerance `1e-7`; no interpolation or
physics/tolerance modification was used. No new simulation was launched.

| Evidence | Before | After |
| --- | ---: | ---: |
| Native exit code / complete metadata | 0 / true | 0 / true |
| Final physical time / termination | 40 s / simulation-time | 40 s / simulation-time |
| Saved physical particle states | 191 | 191 |
| Particle VTKs including initial/equilibrium | 193 | 193 |
| Particles in every audited state | 4,155 | 4,155 |
| Total mass, kg per unit out-of-plane depth | 425,664.0625 | 425,664.0625 |
| Maximum relative mass drift | 0 | 0 |
| Protected-base particles / maximum damage | 496 / 0 | 496 / 0 |

All 193 corresponding particle VTK files are byte-identical. Every exported
array parsed as finite; mass and particle-domain sizes remain positive. The
entire `timesteps.csv` (1,849 data rows, including 1,658 settle rows),
`transitions.csv` (20 data rows), and `reference-metadata.json` are also
byte-identical. The strict maximum position-component difference is **0 m**,
maximum exported-field difference **0**, and maximum recorded numeric CSV
difference **0**. Both processes used one worker, `OPENBLAS_NUM_THREADS=1` and
`OMP_NUM_THREADS=1`. The original accepted material, geometry, staged loading
and 40 s horizon remain the controlled case.

## Executed source provenance

The before run uses frozen original **`c749d32`**. All 21 files in its private
source snapshot match that commit's exact Git blob bytes, and all original
snapshot-manifest hashes verify. The after run loaded copied framework, case
and bundled JSON files from launch snapshot **`41403f4`**: all 46 files match an
exact Git representation of that commit, comprising 10 canonical-blob and 36
checkout-filtered byte matches (`core.autocrlf=true`). The retained audit records
each snapshot path, repository path and SHA-256, including both Git forms.

The after wrapper's status JSON records **`909fddf`** because it calls
`git rev-parse HEAD` after the solver exits. This is the repository HEAD at
completion, **not the executed snapshot**. The wrapper and exact copied source
archive are retained. This provenance claim covers copied framework/case/input
bytes; complete native dependency, FASL and DLL identity is outside its scope.
The earlier four-worker after run remains attributed to **`2f6476f`**.

## Interpretation and preserved negative evidence

This control establishes before/after numerical equivalence under its serial
runtime configuration. The earlier **four-worker strict FAIL remains 176 before
versus 191 after states**, with its original comparison and validation summary
unchanged. Serial success supports runtime sensitivity as a hypothesis, but
does not isolate the cause of the parallel difference or prove deterministic
parallel operation. This is numerical regression evidence, not laboratory,
material or field validation, convergence proof, or full M0 acceptance.

No first-divergence investigation is needed for this pair because every saved
state is identical. The unresolved four-worker failure should remain explicit
in any acceptance or release decision. No new expensive diagnostic run was made.

## Reproduction and retained evidence

Executed on native Windows outputs using the existing analysis environment:

```powershell
& .\toolchain\analysis-venv\Scripts\python.exe scripts/compare-framework-runs.py `
  --baseline output/framework-refactor-2026-10-15/joss-serial-before `
  --candidate output/framework-refactor-2026-10-15/joss-serial-after `
  --output output/framework-refactor-2026-10-15/joss-serial-before-after-comparison.json
```

The command exited 0. The independent audit then checked all particle VTKs,
all CSV rows, run completion, protected-base damage, mass and source bytes.
The existing completion-guarded serial append helper retained the results.
All **134 manifest entries** verify by SHA-256: all 114 earlier
entries other than the serial running status are unchanged, and the original
running status survives byte-for-byte as `serial-control/launch-status.json`.
Original full runs and frozen snapshots remain on disk.

- [Compact machine-readable summary](M0_SERIAL_REGRESSION.json)
- [Strict comparison, compressed](../../docs/evidence/framework-refactor-2026-10-15/serial-control/strict-comparison.json.gz)
- [Independent state/source audit, compressed](../../docs/evidence/framework-refactor-2026-10-15/serial-control/independent-audit.json.gz)
- [Executed after-source archive](../../docs/evidence/framework-refactor-2026-10-15/serial-control/executed-after-source.tar.gz)
- [Evidence manifest](../../docs/evidence/framework-refactor-2026-10-15/manifest.json)
- [Original four-worker summary, preserved FAIL](../../docs/evidence/framework-refactor-2026-10-15/validation-summary.json)
