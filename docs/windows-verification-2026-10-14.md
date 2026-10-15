# Native Windows verification — 2026-10-14

Checkout: `D:\MPM\MPM-test`, branch
`feat/studio-custom-constitutive-lisp-export`, starting commit
`a2e615712b14154a776dba6839041d34be9465cf`. PRs
[#1](https://github.com/hadrianJavas12/MPM/pull/1)–
[#4](https://github.com/hadrianJavas12/MPM/pull/4) were checked live: all remain
open drafts with the stacked bases recorded in [the handover](AI_HANDOVER.md).
The fixes below are local working-tree changes; no commit, push or merge was made.

The baseline is 41 commits ahead of `main`, zero behind. Main/lifecycle/material
heads are ancestors; latest geometry head `98eff24` is not a literal ancestor.
Its fix is already inherited through material commit `648ceca` with identical
patch ID `ba608523e5f0068a9e05f23465ce0caccbc60721`. Actual app code includes the
update, so no cherry-pick is required. The PR stack bases and implementation
coverage remain as documented.

## Toolchain and installation

| Component | Observed version |
| --- | --- |
| Windows | Windows 11 Home Single Language, build 26300 |
| Setup host | Windows PowerShell 5.1.26100.9444 |
| SBCL | 2.6.9, 4000 MB dynamic space |
| Node / npm | 24.13.0 / 11.6.2 |
| Quicklisp | Client 2021-02-13, dist 2026-01-01 |
| OpenBLAS | 0.3.34 |
| gnuplot | 6.0 patchlevel 1 |
| ffmpeg | 9.0.1 essentials build |

Machine executables were already installed. Quicklisp and OpenBLAS were copied
from the existing `D:\MPM\toolchain` into this checkout's `toolchain`; the tracked
`libs/kirchoff.dll` was reused. `setup.ps1 -SkipWinget` exited 0. Separately,
the actual Quicklisp installation function downloaded and installed a fresh
client/dist into `output/windows-verification-2026-10-14/fresh setup/quicklisp`
under PowerShell 5.1. This verifies the bootstrap with spaces in the target path;
it does not imply that every existing dependency was downloaded again.

## Failures found and fixed

- Quicklisp setup passed a Lisp string through fragile PowerShell `--eval`
  quoting. It now writes a temporary source file and checks SBCL's exit code.
  The fresh-install test also exposed a user `.sbclrc` loading CFFI before
  Quicklisp; installation now disables user/system init files.
- Particle VTK used two append streams for text and binary data. Windows
  output interleaved headers and arrays. `src/output.lisp` now writes ASCII
  declarations and big-endian doubles through one octet stream. The preserved
  malformed baseline is rejected by the independent parser.
- `save-frame` could return without a PNG, or accept an old/partial target.
  It now removes the old target, polls for a readable PNG signature and IEND
  trailer, and raises a clear error after the five-second polling window.
  The existing runner handler reports plotting failure. The negative smoke
  took 6.60 seconds including gnuplot setup, then reported the expected error;
  the positive case produced a readable PNG.
- Studio button SVGs had no size constraint and expanded the controls.
  `.btn svg` now uses 18 px dimensions; the browser confirmed normal button sizing.

These are setup, output and UI fixes. The numerical solver update and default
constitutive law were preserved.

## Executed checks

| Check | Result | Scope |
| --- | --- | --- |
| `npm run check` | Passed | Server/browser JavaScript syntax |
| `npm test` with SBCL required | 33 passed, 0 failed/skipped | Node tests and real SBCL contracts with explicit dependency stubs |
| `scripts/smoke-test.lisp` via `windows\cl-mpm.cmd` | Passed, exit 0 | 100 elastic particles, 50 updates, finite positions/velocities/stresses; mean y 0.25 → 0.24322331 m |
| `scripts/studio-custom-smoke.lisp` via launcher | Passed, exit 0 | 64 final particles, two updates, 80 custom delegate calls; maximum position/stress difference 0 |
| Smoke VTK readback | Passed | Both files: 64 points, 36 finite scalar arrays; points and masses match the simulation |
| `scripts/studio-plot-smoke.lisp` via launcher | Passed, exit 0 | Failed-output path reports an error; successful output has a complete PNG |
| Independent Node VTK parser review | Passed | Fresh output accepted; seven corruptions rejected, including the preserved malformed baseline |
| Browser custom delegate | Passed, exit 0 | Actual UI → API → Windows launcher → solver; Finished, 3/3 frames displayed |
| Downloaded `simulation.lisp` | Passed, launcher exit 0 | Unchanged browser export run from a path containing spaces with adjacent custom source |
| UI/export comparison | Passed | All 28 configuration settings and custom source match; mesh + three VTK + three PNG files byte-identical |

The delegate smoke used one worker with plasticity/damage disabled. Its tolerance
is `1e-10 * max(1, abs(left), abs(right))`; the measured differences were zero.
The parser checks this repository's particle-output layout, required scalar
fields, finite big-endian arrays and positive mass. It is not a general VTK
reader or evidence of interoperability with every visualisation application.

## Browser and export comparison

Studio was opened in the in-app browser on loopback port 3014 with custom
execution enabled for the trusted built-in delegate. The lexical check passed;
the actual Run button launched the full Windows engine and finished at 100%,
3/3 frames, exit 0. The browser displayed the final PNG.

The run used `maxSteps=3`, `substeps=5`, `meshSize=10`, `mpsPerCell=1`,
`workers=1`, and the default damage/plasticity flags on. The initial count was
280 particles. The exported frames contained 1120, 1120 and 1309 particles
after the engine's splitting; those counts were checked rather than assuming
that particles remain constant.

The browser downloaded both exact files into `export with spaces/`. The
unchanged `simulation.lisp` was executed through `windows\cl-mpm.cmd` from the
repository root and wrote `output/studio-export/`. Independent comparison
passed for all 28 schema settings and exact custom-source bytes. Mesh VTK,
three particle VTK files and three PNGs had identical bytes and SHA-256 hashes
between the UI and exported runs. Each particle VTK had 36 finite scalar arrays;
the checked finite values per frame were 43,680, 43,680 and 51,051.

See [testing](testing.md) for repeatable commands. This result covers this
short trusted-delegate case on the recorded toolchain, not arbitrary custom laws.
The temporary opted-in loopback server was stopped after preserving evidence;
a normal subsequent Studio launch retains default-deny custom execution.

Recheck the preserved comparison without running a simulation:

```bat
node scripts\verify-studio-output.js output\windows-verification-2026-10-14\ui-run output\windows-verification-2026-10-14\export-run 3
```

## Evidence

All paths below are relative to `output/windows-verification-2026-10-14/`:

- `toolchain.json`, `windows-version.json`, `setup.log` — versions, binary hashes,
  dependency origin and setup exit codes.
- `branch-ancestry.json` — live branch ancestry, ahead/behind and equivalent geometry patch IDs.
- `fresh-quicklisp-initial-failure.log`, `fresh-quicklisp-install.log`,
  `verify-fresh-quicklisp.ps1` — failed and corrected fresh bootstrap.
- `node-check.log`, `node-tests.log`, `smoke-test.log`, `studio-custom-smoke.log`
  — actual syntax, contract and full-engine executions.
- `built-in.vtk`, `custom-delegate.vtk`, `vtk-smoke-parser.log`,
  `malformed-custom-delegate-before-fix.vtk`, `vtk-baseline-failure.log` — VTK
  output and regression evidence.
- `plot-smoke-baseline.log`, `plot-smoke-fixed.log`, `plot-smoke/positive.png`
  — actual gnuplot failure/success evidence.
- `parser-review.log`, `parser-review.cjs`, `parser-negative-fixtures/` —
  independent positive and seven negative byte-layout checks.
- `ui-run/config.json`, `ui-run.log`, `ui-status.json`, `ui-api-logs.json`,
  `studio-delegate-config.jpg`, `studio-delegate-finished.jpg` — browser run,
  normalized inputs, final status, logs and visual evidence.
- `export with spaces/custom-model.lisp`, `export with spaces/simulation.lisp`,
  `export-run.log`, `config-parity.json`, `config-parity.cjs`, `output-parity.json`
  — exact downloaded files and independent config/source/output comparison.
  UI outputs are in `ui-run/{vtk,frames}/`; exported outputs are in
  the preserved `export-run/{vtk,frames}/` copy. The unchanged script originally
  wrote `output/studio-export/{vtk,frames}/` relative to the repository root;
  `output-parity.json` was repeated against the preserved copies.
- `studio-vtk-list.jpg` — browser output list showing mesh and three particle VTK files.
- `ci-annotations.json` — public hosted-check billing-lock annotation.

`output/` and toolchain binaries are git-ignored; preserve or copy this evidence
before discarding the checkout. This tracked report records the observed results.
Historical Linux hardening and the earlier Windows refactor remain attributed
in [the wiki verification note](../wiki-vault/wiki/studio-verification-2026-10-14.md).

## Remaining limits

Hosted [Actions run 38512874136](https://github.com/hadrianJavas12/MPM/actions/runs/38512874136)
never started its job. [Check 115685122821 annotations](https://api.github.com/repos/hadrianJavas12/MPM/check-runs/115685122821/annotations)
again identify an account billing lock. Only the account owner can resolve
that external blocker; hosted CI has not passed.

These short runs establish integration and output consistency. They do not
validate a new physical law, the experimental custom elastic template under
the full engine, long-run stability, mesh convergence or Joss Bay reproduction.
Custom Lisp still executes with local OS-user permissions and requires the
existing default-deny/local-opt-in/confirmation gates.
