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

**Recommended starting branch for the next AI:** `feat/studio-custom-constitutive-lisp-export`. It contains **the entire current series** (all earlier feature branches are ancestors). At snapshot time, its head was `59a0dc54ef3db422082db1dfb729c03031426ac0`, **before** this handover is committed.

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
- PR #4 adds `cl-mpm-studio::studio-custom-chalk`, subclassing the chalk particle class; choose it only if `constitutiveModel = :custom`.
- A custom user model defines a CLOS primary method on `cl-mpm/particle:constitutive-model`, e.g.:

```lisp
(in-package :cl-mpm-studio)
(defmethod cl-mpm/particle:constitutive-model
    ((mp studio-custom-chalk) strain dt)
  (call-next-method)) ; reference/delegation template
```

- `runner.lisp` loads the custom source **before** constructing a run and checks that the expected primary method exists.
- A custom **constitutive stress update is not the same thing as a custom damage-evolution law**. Current PR #4 does not create a general UI/plugin interface for `update-damage` or damage initiation criteria. Do not claim it does.
- Treat the experimental elastic template as an example to validate, not a certified physically complete constitutive model.

### Export behaviour

The editor supports local text editing/import and downloads:
- `custom-model.lisp`: exact user-edited text.
- `simulation.lisp`: Lisp script setting configuration and running the existing CL-MPM Studio library; when custom is selected it loads the adjacent `custom-model.lisp`.

Exported scripts are **NOT standalone**. They need SBCL, Quicklisp, CL-MPM and other repository dependencies. Check parity between browser run settings, schema sanitisation and exported Lisp values. Do not make export invoke arbitrary code silently.

## 4. Extremely important scientific distinction

The existing Studio scenario in `studio/lisp/scenario.lisp` is a **simplified chalk-cliff setup** derived from `examples/chalk/chalk.lisp`. It is **NOT yet** a full reproduction of `examples/chalk/joss.lisp` or the published Joss Bay cliff-collapse research.

The Studio runner currently loops `substeps` calls to `cl-mpm:update-sim` per output frame; defaults use fixed `*mass-scale* = 1d4` in scenario configuration. The original Joss example/paper involves specialised damage / relaxation / acceleration / dynamic collapse logic. Full reproduction requires separate implementation, tests and comparison to reference results.

**Never** call Studio results "validated Joss Bay results" or interpret damage contours / debris motion as physically predictive without establishing material calibration, time stepping, boundary conditions, mesh convergence and reference-case comparison. Do not invent or silently infer parameters from the original paper.

## 5. What has actually been verified — and what has not

Snapshot from previous development sessions:

- GitHub source changes were committed and compared; PRs were opened as **Draft**.
- Some JavaScript syntax checks were performed; isolated tests of geometry predicates, basic material schema validation and export/lexical helper functions passed in an execution environment.
- Lisp parenthesis balance was checked. **Parenthesis balance is not Lisp compilation.**
- Node test files exist under `studio/test/` and can run independently from the physics engine.
- **NOT VERIFIED:** a full `npm test` run on the user's setup, end-to-end Windows + SBCL simulation, exact scientific correctness of custom CLOS method execution, complete Joss Bay reproduction, or mesh-independent runout/crack predictions.
- A GitHub Actions workflow `.github/workflows/studio-node.yml` was added. Workflow runs observed earlier on the feature branches were reported **failed**, and usable job-level logs/steps were unavailable through the connected session. **Root cause UNKNOWN.** Do not describe this as passing CI or assert a particular cause.

**First thing the next AI should do:** query fresh GitHub CI + PR status; diagnose CI failure (check Actions UI/logs/settings/runners and workflow syntax/permissions), get `npm run check` and `npm test` green, and run a Windows SBCL smoke test. Keep testing claims tied to actual captured output.

## 6. How to run / verify

### Node frontend and API (no SBCL needed for unit tests)

```sh
cd studio
npm run check
npm test
```

The Studio server uses Node.js >=18 (CI intends Node 22); no npm runtime dependencies. See `studio/package.json`.

### Native Windows SBCL & studio

```bat
powershell -ExecutionPolicy Bypass -File windows\setup.ps1
windows\cl-mpm.cmd scripts\smoke-test.lisp
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

1. **CI red or unverified:** diagnose, capture actual workflow/job output, fix reproducibly; do not guess.
2. **Lisp end-to-end missing:** make a minimal self-contained SBCL custom model smoke test asserting that specialised CLOS dispatch actually runs and yields finite stresses.
3. **Exporter parity unverified:** run an exported `simulation.lisp` and compare its config/output to a normal Studio run, including enum and numeric type conversions. Check relative path to custom model.
4. **UI validation limited:** the editor's "check" is a lexical delimiter/string/comment check, **not** semantic Lisp compilation, API conformance or proof of safety. Syntax highlighting and completion do not yet exist.
5. **Custom scripting security:** source is arbitrary code; localhost + confirmation are only *operational safeguards*, not sandboxing. Harden CSRF/local service exposures and avoid persistent unintended sensitive output; do not present current code as secure against malicious local/network actors.
6. **Numerical model:** stress update and independent damage evolution are separate APIs; implement them distinctly if the user requests genuinely custom damage laws.
7. **Geometry:** no freeform polygon/imported profile yet; sampled SVG preview may differ from discretised geometry. Validate at actual resolution.
8. **Run bookkeeping:** current Studio uses fixed output directories; source run locks guard concurrency, but per-run output isolation/historical run management remains a future task.
9. **Validation:** no demonstrated benchmark reproducing paper Joss Bay collapse stages or fracture-energy sensitivity.
10. **Docs drift:** `docs/studio.md` and other top-level documentation may predate PR #2–#4; update them once features pass runtime tests. `studio/GEOMETRY.md`, `studio/MATERIAL.md` and `studio/CUSTOM_MODELS.md` describe current feature intent but are not proof of successful runs.

Report new discoveries as **confirmed by code**, **observed by tests**, or **hypotheses requiring investigation**. Do not hide unexpected errors.

## 8. Prioritised next work

### Priority 0 — establish a green baseline
- Inspect the currently checked-out branch and stacked PR bases.
- Resolve the GitHub Actions failure and capture logs; rerun Node checks.
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

### Useful navigation

- [PR #1](https://github.com/hadrianJavas12/MPM/pull/1)
- [PR #2](https://github.com/hadrianJavas12/MPM/pull/2)
- [PR #3](https://github.com/hadrianJavas12/MPM/pull/3)
- [PR #4](https://github.com/hadrianJavas12/MPM/pull/4)
- [CL-MPM Studio custom-model specification](../studio/CUSTOM_MODELS.md)
- [Geometry specification](../studio/GEOMETRY.md)
- [Material parameters](../studio/MATERIAL.md)
- [Developer setup](development.md)
