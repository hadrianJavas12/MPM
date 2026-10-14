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

## Modular Lisp I/O — new draft PR #6

Feature branch: `feat/studio-modular-lisp-presets`. Added
`studio/test/preset-modules.test.js` with **11** regression cases:
partial-module isolation, selected-module import from a full file, Merge vs Replace, multi-module staging,
full Unicode/source round-trip, inert rejection of arbitrary reader
syntax, bounds, duplicate/unknown keys, output completeness and
malformed/trailing input and exact schema ownership.

On 2026-10-14 these 11 test cases were **executed in an isolated V8 harness**
with explicit assertion and UTF-8 compatibility stubs: **11 passed**.
Syntax checks for the changed JS files and the HTML control/script
binding contract also passed static inspection. This evidence is
**not the same as running `npm test` under native Node.js**, does not
constitute browser end-to-end automation, and does not exercise SBCL
solver physics. Run `cd studio && npm run check && npm test` on the
checked-out branch when the toolchain is available.

See [PRESETS.md](../studio/PRESETS.md) for the exact declarative file
format; imported .lisp configuration is parsed as inert data, never
loaded/evaluated.

## Full Windows toolchain

From the repository root with the complete installation:

```bat
windows\cl-mpm.cmd scripts\smoke-test.lisp
windows\cl-mpm.cmd scripts\studio-custom-smoke.lisp
```

The custom smoke writes `output/studio-custom-smoke/built-in.vtk` and
`custom-delegate.vtk`. Inspect both in ParaView. Also compare a short UI run
with downloaded `simulation.lisp`/`custom-model.lisp` under the actual launcher,
checking config, logs, VTK and PNG parity.

The new full-engine custom smoke was added and checked lexically in this session;
it has **not been executed** with the Windows toolchain. Keep that gate open
until captured output exists. Its tolerance compares implementations, not
scientific predictions.

## Evidence on 2026-10-14

Baseline `95ded55b9fee22d9e5871d12d5bd09174a8a401f`: syntax checks and
22 Node tests passed locally. After hardening: syntax checks and **33 tests
passed, zero failed/skipped**, with Node 24.19.0 and SBCL 2.2.9 on Linux.
This includes compilation of the production config/custom-loader files in the
dependency-stub harness. Full browser automation could not run: the browser
binary was unavailable and its download did not yield a valid archive.

The original Windows-refactor wiki records an earlier full Windows run.
That report is retained with attribution and is not current validation of
the custom-model branch. See `wiki-vault/wiki/studio-verification-2026-10-14.md`.

## GitHub Actions blocker

[Run 38509402658](https://github.com/hadrianJavas12/MPM/actions/runs/38509402658)
has no executed steps or assigned runner. Its
[check annotations](https://api.github.com/repos/hadrianJavas12/MPM/check-runs/115674197084/annotations)
state that **the job was not started because the account is locked due to a
billing issue**. This confirms the account-level cause and supersedes the
older unknown-cause note. The workflow installs SBCL and requires the contract
tests on Node 22/Ubuntu 24.04. Hosted CI cannot be marked green until the account
owner resolves the billing lock and a fresh run completes.
