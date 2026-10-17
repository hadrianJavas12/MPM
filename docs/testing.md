# Native framework and Studio verification

## Reusable native framework regression, 2026-10-15

The initial refactor was committed as `66ea5fb` before running the requested
post-refactor native regressions. Compatibility/launcher fixes followed;
`c5fd10d` corrects native material constructor options and `9f26cb1` retains the
composition contracts/regression tooling. See [framework usage](REUSABLE_FRAMEWORK.md)
for supported components, explicit compatibility limits and short case files.

From PowerShell in `D:\MPM`:

```powershell
& .\windows\cl-mpm.cmd tests\framework-components.lisp
& .\windows\cl-mpm.cmd tests\triaxial-components.lisp
$runDir = Join-Path 'D:\MPM\output' ('triaxial-2d-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\triaxial-clay-2d.lisp $runDir
if ($LASTEXITCODE -ne 0) { throw 'Native simulation failed' }
& .\toolchain\analysis-venv\Scripts\python.exe scripts\audit-triaxial.py --run-dir $runDir
& .\toolchain\analysis-venv\Scripts\python.exe scripts\plot-triaxial.py --run-dir $runDir --video
```

Use a new output directory for every run. The public launcher copies and loads
framework, case and JSON inputs before simulation; dependency/FASL/DLL identity
is recorded separately. The calibration compatibility launcher also snapshots
the complete split triaxial module tree. No UI/server is needed.

| Executed check | Observed result | Scope |
| --- | --- | --- |
| Framework component contracts | 10 passed, 0 failed | Native construction/configuration, VM/elastic choice, geometry/clipping, inheritance, explicit rejection; no time integration |
| Triaxial component contracts | Passed | Per-run factory/filter composition, initial Fzz, unsupported class rejection and context preservation |
| Node syntax and suite | 36 passed, 0 failed/skipped | Existing API/schema/reader/compiler contracts; no new browser session |
| Native custom delegate smoke | 64 MPs, two updates, zero stress/position difference | Actual solver and VTK readback; original delegate compatibility |
| Joss reference unit checks | Passed | Volume-weighted statistics, damping mapping and state thresholds |
| Full spatial 2D before/after | 51/51 VTKs byte-identical; every CSV column and exported native field has zero difference | Frozen original monolith with minimal 2D adaptation versus refactored public CLI snapshot `2f6476f` |
| Independent 2D output audit | Passed available-field checks on both runs | Finite fields, mass/volume/kinetic energy/displacement, axial stress and CSV identities; missing tensor components explicitly unavailable |
| Full spatial Joss before/after | Both completed 40 s, exit 0; **strict regression failed** | 176 versus 191 physical states; common-time pointwise diagnostics also exceed `atol=1e-8`, `rtol=1e-7` |
| Full serial Joss control, audited 2026-10-16 | **PASS, exact:** 191 physical states / 193 VTKs per run, positions and all 36 scalar arrays differ by zero; complete CSVs byte-identical | Frozen original `c749d32` versus executed after `41403f4`, one worker and one BLAS/OMP thread; four-worker FAIL remains |
| M1 reference-data integrity | Nine stdlib tests pass | SI conversions, source provenance, paired-law data and execution gates; no constitutive solver or experimental validation |
| Generic material diagnostics, current M0 working tree | Nine native contracts pass | Native MC/linear elastic/VM, analytic corrected MC yield, output collision and history capability guards; MC 32 MPs / two updates, zero mass drift |
| Strict triaxial/JSON configuration | Ten native contracts pass, no timesteps | Unknown/range/count/mode/null/duplicate/trailing-data rejection, isolation and actual JSON false disabling particle plasticity |

Both successful 2D runs use 480 MPs, 17,443 updates, 51 saved states and reach
0.2 s / 10% prescribed strain. Their final qJ2 is 50.01733976 kPa and projected
triaxial q is 43.30520503 kPa. This rectangle is **plane strain with unit thickness**,
not an axisymmetric approximation of the earlier 3D cylinder. Saved-frame native
assertions check Fzz=1 and zero out-of-plane shear/position/velocity. Existing 2D
VTK exports omit sigma_zz and out-of-plane velocity/displacement, so independent
full qJ2/yield/stress recomputation from those VTKs is marked unavailable; missing
components are not inferred. The exact regression still compares all native CSV
columns and all exported fields. Old 3D curves are labeled contextual only.

The first one-MP-per-cell-direction 2D attempt failed mass conservation around
6.3% strain because lateral domain expansion reached the engine's existing GIMP
particle-removal limit. Its source/log/failure record are retained. Successful
before/after runs use two MPs per cell direction on both sides; no removal rule,
solver equation or mass invariant was relaxed.

Current working evidence is in `output/framework-refactor-2026-10-15/`: the frozen
sources/adaptation patch, `triaxial-before-after-comparison.json`, both run folders,
test/audit logs, and actual-data PNG/video/curve overlay with hashes. Native time
is 0.2 s; video playback is 51 frames at 15 fps, or 3.4 s. These are software
regression and consistency checks, not laboratory calibration, convergence proof,
a closed energy budget or validation of the earlier cliff physics.

The full Joss runs are complete; their strict comparison is **not a pass**.
Saved damage first exceeds 0.05 in the lower reference region at 4 s and upper
reference region at 7.5 s in both runs. At 40 s, run-out domain edges are
31.01589046 / 31.01587968 m, and initial-top-particle mean y values are
8.17637462 / 8.17579450 m (before / after). Final position-component differences
reach 0.0811648 m, RMS 0.00234568 m. Final-domain IoU 0.99667193 is a shape
diagnostic, not physical accuracy or a replacement for pointwise tolerances.
The comparator retains the unequal frame counts and performs no interpolation.
See [the detailed status](REUSABLE_FRAMEWORK.md#hasil-validasi-saat-ini) and
`joss-before-after-comparison.json`, `joss-before-after-diagnostics.json`, and
`joss-full-regression-summary.json` in the working evidence directory. Cause
investigation and overall refactor acceptance remain unresolved. The user
authorized committing and pushing this interim evidence while the paired
single-worker controls ran; the final PR remains pending. The serial controls
are now complete and exactly identical; see [the audited result](../research/reports/M0_SERIAL_REGRESSION.md).
This separates a passing deterministic control from the retained four-worker
failure. Current `64f47cc` VM 2D/3D regressions have now passed separately;
see the completed checkpoint below. M0 retains the parallel/provenance limits.
No physics change or scientific validation is claimed.

## Repeatable automated checks

```bat
cd studio
npm run check
set STUDIO_REQUIRE_SBCL_TESTS=1
npm test
```

Node.js ≥18 is required. SBCL is found on PATH or via `STUDIO_TEST_SBCL`
(the executable path). On POSIX, use `STUDIO_REQUIRE_SBCL_TESTS=1 npm test`.
Without SBCL, three tests are explicitly skipped unless this flag is set.
CI requires them. There are no npm runtime dependencies.

| Check | What it exercises | Limit |
| --- | --- | --- |
| `npm run check` | Server/browser JavaScript syntax | No browser or physics execution |
| Node unit/API tests | Schema defaults/limits, preview, lexer, source round trip, disabled/enabled guards, run lock, body limits | Child launch is mocked; no actual `cmd.exe` runner |
| Three SBCL contract tests | Real reader/compiler/CLOS; production config/loader; delegate/elastic dispatch; missing/stale/invalid methods and stresses; exports from paths with spaces | JSON parser, matrices, Quicklisp and runner are explicit stubs; no MPM solver |
| `scripts/studio-custom-smoke.lisp` | Real engine, two steps, built-in/delegate dispatch and finite/matching positions/stresses, VTK | No calibration, long-run benchmark or mesh convergence |
| `scripts/smoke-test.lisp` | Real elastic block, finite timestep and all position/velocity/stress components; downward mean position | Does not establish equilibrium |
| `scripts/studio-plot-smoke.lisp` | Actual gnuplot complete-PNG success and failed-output error | No constitutive-law validation |
| `scripts/verify-studio-output.js` | Repository particle VTK layout, finite arrays, positive mass, UI/export VTK/PNG bytes | Specialized checker, not a general VTK reader or scientific benchmark |

## Full Windows toolchain

From the repository root with the complete installation:

```bat
windows\cl-mpm.cmd scripts\smoke-test.lisp
windows\cl-mpm.cmd scripts\studio-custom-smoke.lisp
windows\cl-mpm.cmd scripts\studio-plot-smoke.lisp
```

The custom smoke writes `output/studio-custom-smoke/built-in.vtk` and
`custom-delegate.vtk`, reads back their big-endian particle arrays and compares
points/masses with the actual simulation. It checks every position/stress
component for finiteness and compares delegate vs built-in with tolerance
`1e-10 * max(1, abs(left), abs(right))`. Its tolerance compares implementations,
not scientific predictions. Inspect geometry at the actual particle resolution
in a suitable viewer when changing the scenario.

For browser/export reproduction, start Studio with a separate UI output directory:

```bat
set STUDIO_HOST=127.0.0.1
set STUDIO_ALLOW_CUSTOM_LISP=1
set STUDIO_OUTPUT_DIR=output\windows-verification-2026-10-14\ui-run
studio\start-studio.cmd
```

Select the trusted Delegate template, use `maxSteps=3`, `substeps=5`,
`meshSize=10`, `mpsPerCell=1`, `workers=1`, and keep the default plasticity/damage
flags on. Run with the per-run confirmation. Download both Lisp files into the
same directory and execute the exported script from the repository root:

```bat
windows\cl-mpm.cmd "output\windows-verification-2026-10-14\export with spaces\simulation.lisp"
node scripts\verify-studio-output.js output\windows-verification-2026-10-14\ui-run output\studio-export 3
```

Preserve the UI output before another run replaces it. The exported script's
default output is `output/studio-export/`. The comparison checks exactly three
particle VTKs and PNGs, mesh bytes, PNG signature/IEND, finite particle fields,
required scalar arrays, positive mass and identical SHA-256 hashes.
The captured session also preserves an exported-output copy in
`output/windows-verification-2026-10-14/export-run/`; compare this with `ui-run/`
to repeat the evidence check without launching SBCL. The temporary opted-in
server was stopped after testing; custom execution is disabled by default on
a normal new launch.

## Evidence on 2026-10-14

Historical baseline `95ded55b9fee22d9e5871d12d5bd09174a8a401f`: syntax checks and
22 Node tests passed locally. After hardening: syntax checks and **33 tests
passed, zero failed/skipped**, with Node 24.19.0 and SBCL 2.2.9 on Linux.
This includes compilation of the production config/custom-loader files in the
dependency-stub harness. Browser automation was unavailable in that earlier session.

The subsequent native Windows session cloned starting commit `a2e6157` into
`D:\MPM\MPM-test`. Final syntax checks and **33/33 tests passed, zero skipped**,
with Node 24.13.0 and SBCL 2.6.9. Actual Windows launcher executions passed:
100-particle/50-update elastic smoke; 64-particle/two-update delegate smoke
(80 custom calls, maximum position/stress difference zero); VTK readback
(36 finite scalar arrays); and positive/negative gnuplot PNG smoke.

The browser custom run finished 3/3 with exit 0 and displayed all three PNGs.
The unchanged browser-exported script ran from a directory with spaces, exit 0.
Independent comparison passed for all 28 config settings, exact source bytes,
and all seven output files (mesh + three VTK + three PNG) byte for byte.
Particle counts were 1120, 1120 and 1309 after splitting; all exported arrays
were finite. Seven corrupted VTK fixtures were rejected. See
[the native Windows report](windows-verification-2026-10-14.md) for versions,
failure reproductions, fixes, exact artifact paths and remaining limits.

The original Windows-refactor wiki and Linux hardening evidence remain
attributed historical reports. The current Windows evidence separately covers
the custom delegate and export. It does not establish physical calibration,
the full-engine custom elastic template, long-run convergence or Joss Bay reproduction.
See `wiki-vault/wiki/studio-verification-2026-10-14.md`.

## Scientific/authenticity checks on 2026-10-15

[The audit report](SCIENTIFIC_AUDIT_2026-10-15.md) and its retained evidence
separate174-frame artifact/visual consistency from physical validation.
Native two-MP, disconnected-support and prescribed-displacement controls
reproduce kernel/aggregation/kinematic concerns. Their diagnostic process
exit0 means the counterexample was observed; it does not mean scientific
contracts passed. A fresh native production4s replay passed equilibrium and
finite-field/base/mass checks with near-identical lower-face initiation, but
it is not a full40s replay, energy balance or mesh-convergence study.

## Native triaxial calibration demonstration, 2026-10-15

The new standalone module has two separate scopes: actual spatial 3D MPM and
a native constitutive-point homogeneous comparator. Both completed 51 frames;
the spatial case completed 17,443 updates and the homogeneous case 1,000 increments.
Their VTK/CSV audits passed finite-field, constant-mass, stress and displacement
consistency checks. Native controls passed the analytical elastic tangent, VM
yield mapping, lateral stress control and a 20-update 3D hydrostatic hold.
The parameter initializer passed 4/4 unit tests, including explicit strain-column
selection without changing the input CSV. Current Node checks/36 tests also
passed with no skips; Studio code is unchanged by this module.

Commands and scientific limits: [calibration/README](../calibration/README.md).
Retained numerical evidence: [triaxial bundle](evidence/triaxial-clay-2026-10-15/README.md).
These checks do not claim laboratory calibration, full undrained pore-water
modelling, mesh/rate/timestep convergence or a closed energy budget.

## Completed framework evidence and migration baseline, 2026-10-16

Executed native checkpoint `64f47cc` (2026-10-16): 9 material-diagnostic,
10 configuration, 10 framework contracts and 36 Node tests pass. Full VM 2D
(480 MPs) and 3D (780 MPs) pairs each completed exit 0, 17,443 updates, 51 states
and 0.2 s. Each pair has all 51 corresponding VTKs byte-identical and every CSV,
position and exported-field difference zero under unchanged criteria. All four
independent audits pass within their available-field scope; missing 2D
sigma_zz/out-of-plane kinematics still preclude the full independent tensor checks.

The collector completed; [the retained summary](evidence/material-contract-2026-10-16/validation-summary.json)
and its 60 SHA-256-verified manifest entries record executed snapshot `64f47cc`,
frozen original 3D `c749d32`, statuses, CSVs, audits and comparison evidence.
Working VTK outputs/logs remain under `output/material-contract-2026-10-16/`.
Those baseline jobs are complete. The Joss byte comparison covers only listed
dedicated numerical modules versus `41403f4`; no new full Joss run is claimed.
M0 remains **PROVISIONAL** because four-worker strict FAIL and incomplete
transitive loaded FASL/DLL provenance remain open.

The [migration specification](architecture/CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md)
governs the migration. P0 inventory was pushed as `6f15148` before moves; its
matrix/approvals remain immutable. These saved results are baseline evidence, not tests
of the target root `materials/`, `scenarios/` and `src/simulation/` layout.
Preserve exact
regression criteria and historical Windows/ASDF/Studio/calibration entry points.
The isolated `.tmp/mc-evolution-stage/` has 32 native point checks passing, with
sampled-root/continuation limits. It is uninstalled; new physics is deferred
until migration gates and requires a separate experimental branch.

## P1 bounded migration verification, 2026-10-16

Production extraction `3cd172e` was committed/pushed before tests. Its 16 defining
forms and whole native factory file retain exact bytes; class/package symbols,
historical source shims and ASDF IDs are preserved. The
[retained P1 evidence](evidence/architecture-migration-2026-10-16/p1/README.md)
has 32 hash-verified artifacts. Actual Windows checks pass: 10 framework,
10 configuration, 9 material (including 32 MPs/two updates), 36 Node with zero
skipped, 7 normal and 7 legacy ownership checks, and 3 snapshot/escape checks.

Strict bounded VM (27 updates) and MC (two updates) comparisons pass across two
states each with zero CSV/position differences. Both two-update MC cliff VTKs
are byte-identical to the prior control; gnuplot PNG is unavailable and plotting
is not marked PASS. The initial 6/7 ownership failure assumed an incorrect SBCL
precedence tail; original-source control confirms `SLOT-OBJECT` already existed.
Only the assertion changed. The first escape fixture preferred the wrong ASDF
registry; correcting the fixture made the unchanged guard reject escape.
Both failed fixtures/logs are retained.

Focused units loaded committed production sources from the working tree;
CLI controls retained copied source/input trees. Full transitive loaded FASL/DLL
provenance is incomplete. P1 is PROVISIONAL, G1 PARTIAL. Full migrated VM 2D/3D
on frozen `62adb50` completed with native/comparison/audit exit 0. The new serial
Joss run was STOPPED_BY_USER at 4.2 s; it has no full comparison or observed exit
code. [P1 full evidence](evidence/architecture-migration-2026-10-16/p1-full/README.md)
retains completed VM controls separately from cancelled partial Joss output.
P2 is plan only; new physics remains deferred.

### P3 diagnostics ownership, Windows native

Implementation was committed before validation; executed source is `333306b`.
Fresh-process contracts, Node checks and two bounded VM/MC controls passed.
Both corresponding VTK pairs are byte-identical to P1, with zero numerical
CSV/position/field differences under the unchanged strict comparator.
[Evidence and actual commands](evidence/architecture-migration-2026-10-16/p3/README.md)
include source hashes, logs and retained VTK/CSV. These are focused compatibility
results, not full scientific or architectural acceptance.

```powershell
.\windows\cl-mpm.cmd tests\diagnostics-ownership-compat.lisp
.\windows\cl-mpm.cmd tests\diagnostics-ownership-compat.lisp legacy
.\windows\cl-mpm.cmd tests\case-snapshot-contracts.lisp output\snapshot-FRESH
```

Use a new empty output path for each snapshot check. The old diagnostics source
path remains a loader; normal ASDF loads the three new owner files directly.

## GitHub Actions blocker

[Run 38512874136](https://github.com/hadrianJavas12/MPM/actions/runs/38512874136)
has no executed steps or assigned runner. Its
[check annotations](https://api.github.com/repos/hadrianJavas12/MPM/check-runs/115685122821/annotations)
state that **the job was not started because the account is locked due to a
billing issue**. This confirms the account-level cause and supersedes the
older unknown-cause note. The workflow installs SBCL and requires the contract
tests on Node 22/Ubuntu 24.04. Hosted CI cannot be marked green until the account
owner resolves the billing lock and a fresh run completes.

## Architecture migration final verification, 2026-10-17

Current source/status and commands are in
[the next-AI checkpoint](architecture/NEXT_AI_CHECKPOINT.md) and
[architecture status](architecture/STATUS.md). P2 A–D and P4 B–F passed all
saved native controls; all twenty post-move family catalogs match the five
baseline catalogs byte for byte.

On the final canonical root-ASDF layout (`436b561` / `9dfb58b`):
- **`p6-short/` (11/11 native checks PASS, 64 verified artifacts)**:
  `case-snapshot` (3/3), `native-snapshot` (7/7), `standalone-triaxial` (3/3),
  `p4-orchestration-002` (4/4; initial Windows PowerShell 5.1 stderr redirection
  attempt `p4-orchestration` is retained unchanged), `engine-smoke` (100 MPs, 50 steps),
  `ownership-normal` (7/7), `ownership-legacy` (7/7), `diagnostics-legacy` (3/3),
  `custom-delegate` (64 MPs, 2 steps, 80 custom calls, zero position/stress diff, VTK readback),
  `cliff-mc` (70 MPs, 2 substeps, byte-identical `vtk/mesh.vtk` and `vtk/sim_00001.vtk` vs P1),
  and `legacy-triaxial` (480 MPs, 27 updates, strict comparison PASS vs P4-E), plus
  Node syntax check and 36/36 tests passing (`p4-f-node/`).
- **`joss-bounded/` (4-second serial initiation control PASS, 54 verified artifacts)**:
  Pre-P2 baseline `before-003` (`a99a4e1` / `7e2aac3`) and final-layout candidate
  `after-001` (`9dfb58b`) both completed 1,658 elastic equilibration steps and 4.0 s
  physical time (`exit 0`). All saved VTKs (`equilibrium.vtk`, `sim_00001.vtk`,
  `sim_00002.vtk`) are byte-identical (`SHA-256` match) and `compare-framework-runs.py`
  exited 0 with zero position, scalar-field, or CSV differences. Earlier harness
  failures `before-001` and `before-002` are retained.
- **`p6-full/` (full final-layout VM Triaxial 2D and 3D regressions PASS, 38 verified artifacts)**:
  Both `triaxial-2d` (480 MPs, 17,443 updates, 51 states) and `triaxial-3d` (780 MPs,
  17,443 updates, 51 states) completed on `9dfb58b` with `nativeExitCode=0`,
  `comparisonExitCode=0`, and `auditExitCode=0`. Every saved VTK (`51/51` in 2D and
  `51/51` in 3D) and `stress-strain.csv` is byte-identical (`SHA-256` match) to
  `p1-full` (`62adb50`), with zero position/CSV/field differences and independent
  consistency audits passing.

No new 40-second full Joss run was started (the earlier run on `62adb50` remains
`STOPPED_BY_USER` at 4.2 s); PNG plotting, complete G3, and scientific validation
are not claimed.
