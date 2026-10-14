# AI Engineering Handover — CL-MPM Studio

> **Read this at the start of a new AI session.** Snapshot verified against GitHub on **2026-10-14**. This is a **handover**, not a claim that the software has passed numerical validation. Check live branches, PRs, code and CI status before acting; this document can become stale. Keep it updated when significant decisions or statuses change.

## 1. Mission: what we are building and why

**Repository:** https://github.com/hadrianJavas12/MPM

The goal is to turn the SBCL/Common Lisp **Material Point Method** research code into a **usable, modular simulation workbench**, especially on Windows, without destroying its original mechanics engine.

The user wants to:
1. Change the **2D cliff geometry** (dimensions, slope, overhang, eventually arbitrary profiles).
2. Change the **toe erosion notch / undercut geometry** (rectangular, elliptical, triangular; eventually custom polygon/freeform).
3. Change the **physical constitutive response**, first through material controls and then through author-authored **Common Lisp methods**.
4. **Import/edit/export `.lisp`** files, including a custom model and a script reproducing the Studio run.
5. Eventually obtain trustworthy **damage / crack development / cliff collapse / runout** simulations that can be checked against research reference cases.
6. **Import/export selected Lisp modules or entire simulation presets**, independently of GUI editing: Geometry, Materials, Constitutive Source, Boundary Conditions, Loading, Solver, Simulation Phases and Output. A partial import must not overwrite unrelated modules; preview, merge/replace, safety and round-trip portability are required. See [MODULAR_LISP_IO.md](MODULAR_LISP_IO.md) and [issue #5](https://github.com/hadrianJavas12/MPM/issues/5). **Planned, not implemented.**

**Critical distinction:** the user explicitly said this project is **not related to their thesis**. Never redirect the project to an unrelated thesis, machine-learning project, or geotechnical sensor optimisation. Keep the user's intended focus on this MPM simulator.

**Engineering values / shared approach:** preserve the established CL-MPM solver wherever possible; extend it through modular interfaces, not one-off hacks; keep the Windows workflow simple; maintain compatibility with existing configurations and upstream examples; make the output scientifically auditable; and mark experimental functionality honestly. The browser is a workbench/controller, **not** an alternative physics engine.

## 2. Current development topology (verified 2026-10-14)

Four **open DRAFT stacked PRs** exist. NONE is merged into `main`.

| Order | PR | Working branch | PR base | Change |
| --- | --- | --- | --- | --- |
| 1 | [#1](https://github.com/hadrianJavas12/MPM/pull/1) | `fix/studio-run-lifecycle-and-validation` | `main` | API lifecycle locks, video race protection, input controls, basic Node tests |
| 2 | [#2](https://github.com/hadrianJavas12/MPM/pull/2) | `feat/studio-notch-geometry-preview` | `fix/studio-run-lifecycle-and-validation` | Notch shapes, triangle-tip control, geometry preview, geometry tests and CI workflow |
| 3 | [#3](https://github.com/hadrianJavas12/MPM/pull/3) | `feat/studio-material-parameter-controls` | `feat/studio-notch-geometry-preview` | Cohesion, dilatancy, plasticity, nonlocal-length controls, elastic preset |
| 4 | [#4](https://github.com/hadrianJavas12/MPM/pull/4) | `feat/studio-custom-constitutive-lisp-export` | `feat/studio-material-parameter-controls` | Custom CLOS material model, Lisp editor/import/export, default-deny local execution |

**Recommended starting branch for the next AI:** `feat/studio-custom-constitutive-lisp-export`. It contains **the entire current series** (all earlier feature branches are ancestors). The reviewed baseline before this hardening session was `95ded55b9fee22d9e5871d12d5bd09174a8a401f`. The implementation and synchronized docs/wiki are in commit [`52c5ed7`](https://github.com/hadrianJavas12/MPM/commit/52c5ed7c68985703f845b1331d389aab36664124); a subsequent documentation commit records this provenance. Query the branch for its current HEAD before continuing.

**DO NOT** commit to `main` or merge the PRs without explicit instruction from the user. For new tasks, branch from the most appropriate feature branch; prefer a new small PR rather than silently mixing unrelated work into PR #4. Before changing PR bases, inspect the live PR graph. If the user requests merges, resolve the stack in **#1 → #2 → #3 → #4** order, then rebase/retarget and rerun tests. Never assume a PR is merged just because a branch exists.

## 3. Source of truth and architecture

### The two layers

```text
Browser UI (`studio/public/index.html` + `app.js`)
    ├─ geometry preview in `public/geometry.js`
    ├─ custom source + Lisp export in `public/model-workspace.js`
    └─ HTTP/JSON
         ▼
Node HTTP server (`studio/server.js`)
    ├─ validates `studio/schema.json`
    ├─ enforces one run / one video job, writes config/output
    ├─ optionally writes trusted custom-model.lisp (explicit opt-in)
    └─ starts Windows launcher -> SBCL (`studio/lisp/run.lisp`)
                                            ▼
ASDF `cl-mpm-studio` (`studio/lisp/cl-mpm-studio.asd`)
    ├─ config.lisp — schema-based config/defaults
    ├─ custom-model.lisp — dedicated class, trusted loader, stress contract
    ├─ scenario.lisp — geometry, particle class, material params, BCs
    └─ runner.lisp — optional Lisp load; time integration; PNG/VTK
                                            ▼
Existing CL-MPM numerical engine (`src/`)
    ↳ particles ↔ grid (P2G / G2P), stresses, damage, boundary conditions
```

**Files to read before making changes:**

| Concern | File(s) |
| --- | --- |
| Setup/platform | `README.md`; `docs/windows-setup.md`; `docs/development.md` |
| Core numerical engine | `cl-mpm.asd`; `src/setup.lisp`; `src/core/`; `src/models/chalk.lisp`; `src/damage/` |
| Original reference research scenario | `examples/chalk/joss.lisp` and `examples/chalk/chalk.lisp` |
| Windows/Studio architecture | `docs/architecture.md`; `studio/lisp/cl-mpm-studio.asd` |
| User parameters and units | `studio/schema.json` (canonical) |
| UI wiring | `studio/public/index.html` and `app.js` |
| Frontend preview | `studio/public/geometry.js` |
| Backend validation/security | `studio/server.js` |
| Actual geometry/particle creation | `studio/lisp/scenario.lisp` |
| Run loop / VTK / PNG | `studio/lisp/runner.lisp` |
| Custom authoring / Lisp exports | `studio/public/model-workspace.js` |
| Details of newly added features | `studio/GEOMETRY.md`; `studio/MATERIAL.md`; `studio/CUSTOM_MODELS.md` |
| Node tests / CI | `studio/test/`; `.github/workflows/studio-node.yml` |

The schema is the **single source of truth** for parameter keys, values, types, defaults and units for Node and Lisp. The UI works with human-friendly units for some fields (e.g. GPa→Pa, kPa→Pa); unit conversions must remain explicit and tested. No silent reinterpretation of existing settings.

### Geometry conventions

`soilBoundary` is the geometric base-layer thickness. It is **not automatically a separately constitutively modelled soil material**: the current scenario initially fills the block with chalk particles and preserves the base during clipping. `shelfHeight` measures height above the base. `shelfLength = shelfHeight * shelfAspect`. `cliffSlope` is the face angle; `undercut` remains the additional face overhang setting (it does **not** control the angle of an individual notch). `notchHeight = 0` disables the notch; `notchDepth = 0` means automatic depth `1.5 * notchHeight`.

The three current `notchShape` values are `rectangle` (legacy default), `ellipse`, and `triangle`; `notchTipFraction` only affects the triangle. Removal uses `cl-mpm/setup:remove-sdf` and the shape expressions in `scenario.lisp`. The JavaScript preview samples **corresponding formulas** but is not a solver mesh, physics result, or exact particle geometry. Compare with initial VTK when testing new geometry and verify the shape is resolved at the chosen mesh/particle spacing.

### Material-model contract

- Current default material: `cl-mpm/particle::particle-chalk-delayed` from `src/models/chalk.lisp`, with Mohr–Coulomb plasticity + nonlocal delayed damage features.
- PR #3 exposes `cohesion`, `dilatancyAngle`, `nonlocalLength`, `enablePlasticity`, along with existing density, E, nu, friction, initiation stress, delay, damage, ductility.
- PR #4 adds `cl-mpm-studio::studio-custom-chalk` in `custom-model.lisp`, subclassing the chalk particle class; choose it only if `constitutiveModel = :custom`.
- A custom user model defines a CLOS primary method on `cl-mpm/particle:constitutive-model`, e.g.:

```lisp
(in-package :cl-mpm-studio)
(defmethod cl-mpm/particle:constitutive-model
    ((mp studio-custom-chalk) strain dt)
  (call-next-method)) ; reference/delegation template
```

- `main` and exported scripts use the shared `load-custom-model` before constructing a run. It removes stale/partially installed primary methods and requires the exact new primary method. `make-cliff-sim` checks the same contract.
- A Studio-specific CLOS `:around` guard rejects wrong matrix type/dimensions and NaN/infinite returned Kirchhoff stresses before core copies. This is interface validation, not scientific validation or code isolation.
- The elastic template refreshes undamaged and Kirchhoff stress, and requires plasticity/damage off and zero initial damage. UI template selection switches to custom and disables both flags; constructors now propagate the damage flag to particles as well as the simulation.
- A custom **constitutive stress update is not the same thing as a custom damage-evolution law**. Current PR #4 does not create a general UI/plugin interface for `update-damage` or damage initiation criteria. Do not claim it does.
- Treat the experimental elastic template as an example to validate, not a certified physically complete constitutive model.

### Export behaviour

The editor supports local text editing/import and downloads:
- `custom-model.lisp`: exact user-edited text.
- `simulation.lisp`: Lisp script setting configuration and running the existing CL-MPM Studio library; when custom is selected it loads the adjacent `custom-model.lisp`.

Exported scripts are **NOT standalone**. They need SBCL, Quicklisp, CL-MPM and other repository dependencies. `public/config.js` now shares API/export normalization, and exports every schema setting with numeric limits/defaults/zero/false preserved. Lisp coercion matches decimal strings and positive half-up integer rounding. Reader/config/adjacent-source parity has passed SBCL tests with dependency stubs; physical output parity under the full toolchain remains unverified. Do not make export invoke arbitrary code silently.

## 4. Extremely important scientific distinction

The existing Studio scenario in `studio/lisp/scenario.lisp` is a **simplified chalk-cliff setup** derived from `examples/chalk/chalk.lisp`. It is **NOT yet** a full reproduction of `examples/chalk/joss.lisp` or the published Joss Bay cliff-collapse research.

The Studio runner currently loops `substeps` calls to `cl-mpm:update-sim` per output frame; defaults use fixed `*mass-scale* = 1d4` in scenario configuration. The original Joss example/paper involves specialised damage / relaxation / acceleration / dynamic collapse logic. Full reproduction requires separate implementation, tests and comparison to reference results.

**Never** call Studio results "validated Joss Bay results" or interpret damage contours / debris motion as physically predictive without establishing material calibration, time stepping, boundary conditions, mesh convergence and reference-case comparison. Do not invent or silently infer parameters from the original paper.

## 5. What has actually been verified — and what has not

Current verified evidence (2026-10-14 follow-up):

- All PRs #1–#4 remain open drafts; their bases match the table above. Baseline #4 was `95ded55b9fee22d9e5871d12d5bd09174a8a401f`, ahead of `main` by 39 commits and behind by zero.
- Baseline JavaScript syntax checks and 22 Node tests actually passed locally. After hardening, syntax checks and **33 tests passed, zero failed/skipped**, on Linux with Node 24.19.0 and SBCL 2.2.9.
- Three tests invoke a real SBCL reader/compiler/CLOS and compile the production `config.lisp` and `custom-model.lisp`. Their JSON/matrix/Quicklisp/runner dependencies are explicitly stubbed. This is **not** an ASDF/full-engine simulation or physical benchmark.
- API tests exercise both disabled and opted-in local policy, confirmation/size/NUL/Host/origin checks, exact source writes and concurrent-run locks; child launch is mocked.
- **CI cause confirmed:** Actions run `38509402658`, check `115674197084`, has no steps/runner. The public check annotation says the job was not started because the account is locked due to a billing issue. Hosted CI remains blocked until the account owner resolves that lock. Do not invent a code-based workaround or call it a passing run.
- The workflow now pins Ubuntu 24.04, uses Node 22, installs SBCL, and requires the contract tests. Its hosted execution is still blocked.
- `scripts/studio-custom-smoke.lisp` was added for real-engine built-in/delegate comparison, finite stresses/positions and VTK. Only lexical structure was checked here; it has **not** run under the full Windows toolchain.
- **NOT VERIFIED:** full Windows/SBCL/Quicklisp/MAGICL/OpenBLAS custom simulation, actual exported-vs-UI numerical output parity, full Joss Bay reproduction, mesh-independent predictions. Browser automation could not run because the binary was unavailable and its download failed.
- Historical wiki [[refactor-2026-10-14]] reports full Windows tests of the earlier port. That is attributed historical evidence; it does not validate these new custom-model changes.

See [testing.md](testing.md) and the Obsidian/LLM Wiki `wiki-vault/wiki/studio-verification-2026-10-14.md` for exact scope. Next: restore hosted Actions through the account owner, then run the supplied full-engine Windows smoke and export/UI comparison before making physical claims.

## 6. How to run / verify

### Node frontend and API (no SBCL needed for unit tests)

```sh
cd studio
npm run check
npm test
```

The Studio server uses Node.js >=18 (CI Node 22); no npm runtime dependencies. Three SBCL tests skip explicitly when SBCL is absent; use `STUDIO_REQUIRE_SBCL_TESTS=1` to require them, or Windows `set STUDIO_REQUIRE_SBCL_TESTS=1`. `STUDIO_TEST_SBCL` may specify the executable path. See `docs/testing.md`.

### Native Windows SBCL & studio

```bat
powershell -ExecutionPolicy Bypass -File windows\setup.ps1
windows\cl-mpm.cmd scripts\smoke-test.lisp
windows\cl-mpm.cmd scripts\studio-custom-smoke.lisp
studio\start-studio.cmd
```

For short smoke runs, use a small JSON config (e.g. `{"maxSteps":3,"substeps":5,"meshSize":10,"mpsPerCell":1}`) and launch:

```bat
windows\cl-mpm.cmd studio\lisp\run.lisp my.json output\run1
```

Inspect actual output VTK in ParaView, log/status, frame count and (if installed) gnuplot PNGs. Compare built-in vs custom **delegate** method, then experimental elastic method, with damage/plasticity disabled as appropriate. A custom elastic branch may not be physically consistent with all damage/history fields; measure and test this.

### Execute trusted custom Lisp (local only)

```bat
set STUDIO_HOST=127.0.0.1
set STUDIO_ALLOW_CUSTOM_LISP=1
studio\start-studio.cmd
```

The server ordinarily **rejects execution**. Custom execution additionally requires JSON and origin checks, per-run affirmative user confirmation, and a size limit (32 KiB). Code still executes under the local OS user's permissions. **It is NOT sandboxed.** Never enable this on a shared, remote, internet-facing, or untrusted environment. Never load source from an arbitrary web request without these explicit gates. For multi-user deployment, proper OS/container isolation and a separate threat model are required.

## 7. Known gaps / risks to preserve in context

1. **CI account blocker confirmed:** billing lock prevented jobs from starting. Account owner must resolve it; then capture a fresh run. Local tests are green; hosted CI is not.
2. **Full-engine Lisp integration missing:** real SBCL contract tests now pass with dependency stubs. Execute the supplied `scripts/studio-custom-smoke.lisp` on the complete Windows toolchain; add the elastic/export physics comparisons after that baseline.
3. **Physical exporter parity unverified:** shared normalization and SBCL reader/config/custom relative-path evaluation passed with stubs. Compare exported vs UI VTK/PNG/config under the actual launcher; those outputs have not been compared.
4. **UI validation limited:** the editor's "check" is a lexical delimiter/string/comment check, **not** semantic Lisp compilation, API conformance or proof of safety. Syntax highlighting and completion do not yet exist.
5. **Custom scripting security:** source is arbitrary code; localhost + confirmation are only *operational safeguards*, not sandboxing. Harden CSRF/local service exposures and avoid persistent unintended sensitive output; do not present current code as secure against malicious local/network actors.
6. **Numerical model:** stress update and independent damage evolution are separate APIs; implement them distinctly if the user requests genuinely custom damage laws.
7. **Geometry:** no freeform polygon/imported profile yet; sampled SVG preview may differ from discretised geometry. Validate at actual resolution.
8. **Run bookkeeping:** current Studio uses fixed output directories; source run locks guard concurrency, but per-run output isolation/historical run management remains a future task.
9. **Validation:** no demonstrated benchmark reproducing paper Joss Bay collapse stages or fracture-energy sensitivity.
10. **Documentation now synchronized:** Studio/custom/material/development/testing and the wiki describe the hardening. Historical full-Windows claims are attributed and distinguished from current contract-test evidence. Keep all claims current as real-engine evidence arrives.

Report new discoveries as **confirmed by code**, **observed by tests**, or **hypotheses requiring investigation**. Do not hide unexpected errors.

## 8. Prioritised next work

### Priority 0 — establish a green baseline
- Inspect the currently checked-out branch and stacked PR bases.
- Ask the account owner to resolve the confirmed GitHub billing lock; inspect a fresh Actions run. Do not repeatedly retry jobs while locked. Local Node/SBCL contract tests already pass.
- On a Windows SBCL install, run `scripts/smoke-test.lisp` and a minimal default Studio scenario.
- Add executable integration tests for custom delegate and elastic model, import/export round trips, parameter validation, API denial paths, and finite output. Fix actual failures.

### Priority 1 — make custom modelling genuinely reliable
- Test a reference custom CLOS constitutive model end-to-end without modifying the default chalk class.
- Ensure contract errors are helpful (missing method, wrong method qualifiers/signature, invalid state/stress).
- Provide a way to validate compiled Lisp source locally **without running it in the unrestricted web-server process**; be explicit that compiling or loading arbitrary Lisp is itself unsafe.
- Verify exported `simulation.lisp` and `custom-model.lisp` execute together with the actual command-line launcher.
- Consider a model registry and safe catalog of **trusted built-in** constitutive classes before a general-purpose untrusted plugin architecture.

### Priority 2 — geometry and scientific features
- Add custom polygon/freeform cliff profiles and notch import (CSV coordinates) with geometry validity tests.
- Add physical separation of base material if requested; the current base is a geometric region, not a separate soil model.
- Expose advanced constitutive and **damage initiation/evolution** hooks separately with unit tests.
- Introduce dynamic relaxation / accelerate / collapse phases by tracing original `examples/chalk/joss.lisp`, not by inventing behaviour.
- Build reference-case benchmarks: geometry, mass balance, stable timestep, crack path, displacement, runout, parameter sensitivity and mesh refinement. Document the source/reference numbers and tolerance.

### Priority 1b — modular Lisp import/export and full preset portability (new user request)
- Track [issue #5](https://github.com/hadrianJavas12/MPM/issues/5) and [MODULAR_LISP_IO.md](MODULAR_LISP_IO.md). It is a **backlog requirement**, not a shipped Studio feature.
- Implement versioned, declarative, non-executing .lisp modules with explicit per-module ownership (Geometry, Materials, BCs, Loading, Solver, Phases, Output and Constitutive Source).
- Add partial or multi-module import/export, before/after preview, merge vs replace, compatibility checks and atomic application without resetting unselected modules.
- Add **full preset import and export**, including configuration, metadata and custom-model source dependencies, with deterministic round-trip tests and UI parity. Never execute arbitrary Lisp upon import.
- Roll out scalar parameter modules first; BC/loading/phases/multi-material support requires matching engine adapters and numerical tests.

### Priority 3 — usability/research workflow
- Version and export complete simulation manifests/config, code, VTK/CSV, metadata and run logs.
- Add robust run IDs, failure recovery, progress reporting and user-facing guidance.
- Improve Lisp editor (syntax highlighting, diagnostics) without increasing code-execution risk.
- Update consolidated docs, examples and user instructions.

## 9. Definition of done for each new feature or PR

A feature is **not done** just because UI controls render or code passes a static check.

Required:
- The frontend control, API input validation, schema default/type/unit, Lisp config and physics usage all match.
- No silent unit conversions or changed existing defaults; legacy chalk scenario works.
- Automated tests cover normal/edge/failure cases, and CI passes; identify what tests actually exercised.
- For physical changes: execute SBCL and demonstrate numerical checks, conserved quantities where applicable and a reference baseline.
- For geometry changes: preview and actual VTK material points are both inspected.
- For custom code: default deny, explicit opt-in, user confirmation, accurate security disclosures, and no claim of sandboxing.
- Documentation and this handover are updated; include commands and results, limitations, branch and PR links.
- Changes go into an appropriate branch/PR; do not merge or overwrite `main` without authorization.

## 10. Session startup / shutdown checklist for AI collaborators

At **start**:
1. Read root `AGENTS.md`, this handover, and the three topic documents under `studio/`.
2. Check `git status`, default branch, current commit and live PR #1–#4 statuses. Confirm branch ancestry instead of trusting this date-stamped snapshot.
3. Read affected code and schema (not just an earlier assistant explanation). Identify minimal intended behaviour change, numerical consequences and test strategy.
4. Preserve the existing full CL-MPM solver and backward-compatible defaults unless a specific change is justified and tested.
5. Tell the user which branch and PR will be changed.

At **handoff/end**:
1. State precisely what changed (files/function names), tests **actually run**, failures and scientific limitations.
2. Give the exact GitHub branch, commit and PR URL and whether it is draft/open/merged.
3. Append a short date-stamped progress entry below; update open issues and priorities, rather than erasing known unresolved risks.
4. Do not silently merge into `main` or present the experimental simulator as validated.

### Progress log

- **2026-10-14:** Existing repository ported toward native-Windows use with CL-MPM Studio; PR #1 lifecycle + API fixes; PR #2 geometrical notch selection/preview; PR #3 chalk material controls; PR #4 custom Lisp editor, opt-in local CLOS model execution and export. All four PRs remain open drafts; GitHub Actions failures remain unresolved; end-to-end SBCL physics tests not performed in these AI sessions. Handover documentation created on the PR #4 branch.

- **2026-10-14 follow-up hardening:** Implementation commit [`52c5ed7`](https://github.com/hadrianJavas12/MPM/commit/52c5ed7c68985703f845b1331d389aab36664124). Reviewed baseline `95ded55` and PR stack. Added shared `public/config.js` normalization; schema-complete exports through `load-custom-model`; dedicated `custom-model.lisp` class/loader/finite-stress guard; stale/partial primary-method cleanup; corrected elastic stress/history handling and per-particle damage flags; Lisp decimal/rounding/boolean coercion parity; character/escaped-symbol lexical handling; robust import errors/reimport; API confirmation/body/Host/origin/run-lock regression tests. Added real-engine Windows smoke script (not executed). **33 tests passed**, including real SBCL compilation/reader/CLOS with explicit dependency stubs. CI billing lock confirmed again for run `38512583746` / check `115684219301` through annotations; Windows physics/browser gates remain open. Updated documentation and Obsidian/LLM Wiki, preserving historical sources and appending the log. Branch remains `feat/studio-custom-constitutive-lisp-export`, PR #4 draft; `main` and the numerical engine are unchanged.

- **2026-10-14 modular portability requirement:** User additionally requested UI + selective .lisp import/export (individual, multiple selected modules) and full preset import/export. Defined proposed contract in [MODULAR_LISP_IO.md](MODULAR_LISP_IO.md) and opened [issue #5](https://github.com/hadrianJavas12/MPM/issues/5). This is documentation/roadmap only; existing code imports custom constitutive source and exports runnable scripts but does not provide a general module/preset import manager. Preserve no-execution-on-import and unselected-module isolation. 

- **2026-10-14 modular preset implementation (new stacked branch):** Created `feat/studio-modular-lisp-presets` based on the PR #4 branch. Execution plan: [EXECUTION_PLAN_MODULAR_PRESETS.md](EXECUTION_PLAN_MODULAR_PRESETS.md). Implemented `studio/public/preset-modules.js` as an inert restricted line-oriented Lisp interchange format with module ownership and v1 headers. Added declarative export for one/selected/all modules (Geometry, Materials, Solver, Output and Constitutive Source); staged import with before/after diffs, merge/replace and dependency checks; browser controls and apply/cancel guarded against stale preview; Unicode source preservation as hexadecimal text. Added `studio/test/preset-modules.test.js` and `studio/PRESETS.md`. V8 isolated test checks completed; Node/GitHub CI and full Windows browser/SBCL solver integration **not verified** in this session (hosted Actions billing block persists). No arbitrary code is executed during preset import. **Do not claim support for BC/loading/phases, multi-material or arbitrary Lisp parsing.** Branch not merged; main unchanged. Issue #5 tracked; [Draft PR #6](https://github.com/hadrianJavas12/MPM/pull/6) now tracks implementation. Eleven modular preset regression cases were executed with a V8 compatibility harness and passed; not Node-native tests, browser automation or full SBCL/MPM validation.

- **2026-10-14 PR #6 follow-up:** Added an explicit selected-only import mode: a complete .lisp preset may be imported as Geometry-only (or any declared subset), preserving all other modules and custom source. Strengthened exact schema ownership, full export source completeness, UI rollback and parser errors. **11/11 new regression cases passed in an isolated V8 compatibility harness**; source JS syntax and referenced UI IDs/load order checked. This does **not** establish native Node `npm test`, interactive browser results, Windows SBCL or numerical validation. Canonical user steps in [studio/PRESETS.md](../studio/PRESETS.md). Branch: `feat/studio-modular-lisp-presets`, [draft PR #6](https://github.com/hadrianJavas12/MPM/pull/6), base PR #4; main unmodified.

### Useful navigation

- [Verification guide](testing.md)
- [Obsidian/LLM Wiki index](../wiki-vault/wiki/index.md)
- [Current verification note](../wiki-vault/wiki/studio-verification-2026-10-14.md)

- [PR #1](https://github.com/hadrianJavas12/MPM/pull/1)
- [PR #2](https://github.com/hadrianJavas12/MPM/pull/2)
- [PR #3](https://github.com/hadrianJavas12/MPM/pull/3)
- [PR #4](https://github.com/hadrianJavas12/MPM/pull/4)
- [CL-MPM Studio custom-model specification](../studio/CUSTOM_MODELS.md)
- [Geometry specification](../studio/GEOMETRY.md)
- [Material parameters](../studio/MATERIAL.md)
- [Developer setup](development.md)
