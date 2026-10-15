# Studio verification

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

## GitHub Actions blocker

[Run 38512874136](https://github.com/hadrianJavas12/MPM/actions/runs/38512874136)
has no executed steps or assigned runner. Its
[check annotations](https://api.github.com/repos/hadrianJavas12/MPM/check-runs/115685122821/annotations)
state that **the job was not started because the account is locked due to a
billing issue**. This confirms the account-level cause and supersedes the
older unknown-cause note. The workflow installs SBCL and requires the contract
tests on Node 22/Ubuntu 24.04. Hosted CI cannot be marked green until the account
owner resolves the billing lock and a fresh run completes.
