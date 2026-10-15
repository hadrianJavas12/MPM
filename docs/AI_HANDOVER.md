# AI Engineering Handover — CL-MPM Studio

> **Read this at the start of a new AI session.** Open PR topology refreshed through the public GitHub API on **2026-10-15**; older checks below retain their dates. This is a **handover**, not a claim that the software has passed numerical validation. Check live branches, PRs, code and CI status before acting; this document can become stale. Keep it updated when significant decisions or statuses change.

**Latest user work, 2026-10-15:** branch `codex/triaxial-clay-calibration` adds
[the upstream change report](UPSTREAM_CHANGE_REPORT.md), professional PDF
exports, and [native clay triaxial calibration](TRIAXIAL_CALIBRATION.md).
User confirmed no laboratory data and requested an undrained example. Fixed
comparison `d8e65543` upstream → `f7fb2a3` fork shows 273 added/5 modified files,
308/313 original files identical; core/models/damage/aggregate code is retained.
Report section 9 separately records the new calibration module after that snapshot.

Native 3D MPM completed 780 MPs, 17,443 updates, 51 frames to prescribed platen
strain 10% (specimen extent 9.89852%), q 50.00844 kPa and lateral 50.02246 kPa.
Homogeneous native constitutive comparator completed 1,000 increments/51 frames,
q 50.01000 kPa. E 5 MPa, nu .49, su scale 25 kPa, cell pressure 50 kPa are
explicit demonstration assumptions. No pore-pressure, damage, Fbar, aggregation
or mass scaling is used in this experiment. It is not calibrated real clay.
All VTK/CSV consistency audits passed, native elastic/yield/lateral/hydrostatic
controls passed, estimator 4/4 tests passed, Node 36/36 passed with no skips.
Evidence: `docs/evidence/triaxial-clay-2026-10-15/`. Plots/videos read actual VTK
and CSV; solid curve uses specimen extent strain, dashed curve uses platen strain.

Limits: coarse MPM volume bias +3.4507%; normal end springs are bilateral,
frictionless displacement constraints; volume drift max .020016%; peak KE/elastic
3.9556% at startup and .7122% final, no closed energy/convergence study. Raw
`effective-config.json` plus retained source records defaults; it is not a fully
resolved configuration by itself. Production runs predate exact pre-load harness
snapshots (explicit provenance false); future launcher snapshots and executes the
harness, tested by final native controls. Existing chalk/Joss/Studio defaults and
the accepted collapse artifacts are untouched. Do not rerun long pilots or claim
scientific clay validation from this demonstration. Use `calibration/README.md`.

**Latest scientific/authenticity audit, 2026-10-15:** the requested native rerun
guide/config were committed and pushed first as `8549c32`. Audit now completed:
[SCIENTIFIC_AUDIT_2026-10-15.md](SCIENTIFIC_AUDIT_2026-10-15.md), with
[retained evidence](evidence/scientific-audit-2026-10-15/README.md). All174 physical
VTKs have finite36 arrays and constantmass; all174 saved PNGs regenerate exactly,
and video matches within compression error. No prescribed failure trajectory or
painted damage found in inspected code/artifacts. Historical constructor/class/
environment hooks are disclosed. **Authenticity is supported; scientific
validation is not established.** Native controls reproduced asymmetric damaged
pair-radius kernel and a separate polynomial difference from Eq33, aggregation
support across8m emptygap, and an Fbar volume/stored-gradient distinction that
needs a validated kinematic contract. These controls do not quantify incidence
or error in the accepted run. Energy budget, mesh/timestep/phase sensitivity and
material/field validation remain open. Do not hide these findings or mark output
validated based on acceptance, mass conservation or finite-field checks.

One bounded fresh native production CLI replay to4s completed (exit0,1658 settling
updates,2frames,4155MPs,496protectedbase), without historical constructor/class/
environment-function replacement. At4s maxdamage.333589398 is again lower-face;
maximum difference from historical4s is9.30e-10m position and1.18e-7damage. It used
the retained compiler/cache `run-fast.lisp` entry and current production main.
This supports fresh initiation, not a full40s replay or unscaled physical-time
validation. No production algorithm, accepted config or pilot artifact was
changed by the audit. No further visual calibration/UI work is requested.
Auto-continuation remains PAUSED. Current guide:
[RUN_ACCEPTED_COLLAPSE_WINDOWS.md](RUN_ACCEPTED_COLLAPSE_WINDOWS.md).

**Accepted result, 2026-10-15:** after viewing the actual
native DP collapse/run-out video and the later 40 kPa result, the user said they
were satisfied and asked for a commit recording successful collapse. The
**40 s DP physical pilot is accepted as the requested visual
collapse result**; the user requested a commit and no further calibration.
This accepts the observed collapse sequence, not numerical identity or scientific
validation. Its approximate comparison against reference final t=221.14 s remains
IoU 0.699825, run-out edge +7.8 m and plateau edge −5.2 m: it loses more cliff and
runs out farther. The pilot completed 174 frames, 4,155 MPs, constant mass
425664.0625 kg/m and finite audited fields. First saved damage is lower-face at
t=4 s, max 0.333589; 496 protected base MPs remain undamaged in the pause audit.
The preserved accepted video/final image, later result, metadata, audits and
replay provenance are indexed in
[the commit evidence bundle](evidence/joss-collapse-2026-10-15/README.md).
Full diagnosis: [JOSS_DAMAGE_DIAGNOSIS_2026-10-15.md](JOSS_DAMAGE_DIAGNOSIS_2026-10-15.md).

The reference-only production path now uses author Joss DP driving with radian
friction, native aggregate stabilization/statistics and an elastic protected
index-1 base; ordinary Studio/chalk defaults remain unchanged. The strict frozen
probe converged in 1658 updates (energy 5.068e-9/OOBF 9.9667e-5). Same-state
nonlocal lower DP 50.409 kPa versus MC 16.076 kPa explains the former basal
initiation failure at the correct 18.926 kPa threshold. Exact legacy DR one-trial
evidence has native time 0/dt 1 and changes trial positions only: do not replay
its assigned timeline as physical evidence. Clip/source identity is still unproved.
Actual validation recorded in `output/reference-reproduction-2026-10-15/validation/`:
Node 36/36 (three real SBCL contracts), native reference smoke with 179 settling
steps, four finite VTKs/two PNGs and 124 protected base MPs, plus failed-equilibrium
guard. This is integration evidence, not scientific validation.

**Completed later calibration:** `strength-40k-run` reached **221.14 s / 111
frames**, ending normally in accelerate with `complete=true`. It uses 40 kPa
initiation (between measured lower/upper DP drives), derived cohesion
54949.548389 Pa/ductility 12, unchanged Gf 4.8 J/m² and delay 10 s, h=0.5 m/two
MPs per axis/four workers. The raw request was 5000 frames; canonical schema
normalization made the effective cap **2000**, as the actual run log confirms.
Final max damage is **0.49062952033**, mass-weighted damage **0.008064637675**;
it did **not** collapse. Do not describe this later case as the accepted collapse
or keep the stale PID 29416/pending status. It is an unverified calibration,
not literal paper inputs. The accepted pilot used a saved equilibrium warm start;
the later candidate exercised the production CLI path. The historical pilot's
isolated `joss-probe-dp-chalk` subclass and current production reference class
have separate evidence; identical production replay is unproved. Keep that
provenance distinction. Heartbeat `mpm-lanjut-setelah-reset` is
confirmed **PAUSED** following user acceptance. Do not resume simulations,
calibration or UI work without a new user request. The user authorized a local
commit on `feat/studio-custom-constitutive-lisp-export`; no push or merge was
requested.

**Local workspace update, 2026-10-15:** the active checkout is now directly
`D:\MPM`, branch `feat/studio-custom-constitutive-lisp-export`, with migration
baseline `f70e410` (subsequent accepted checkpoint `cd5e07f`; see git log for HEAD).
The former `D:\MPM\MPM-test` directory is gone. The old root checkout, including
its `main` history, local changes and artifacts, is preserved in
`D:\MPM\.workspace-backup\before-flatten-20261015-0432` (ignored by the active repo).
All 41 changed/untracked source files matched their pre-move SHA-256 hashes;
the recovery stash is retained. The relocated Windows launcher actually loaded
Studio, its schema and local libraries successfully. Existing evidence paths
under `output/` now resolve relative to `D:\MPM`; old absolute paths in historical
logs remain historical. Obsidian preferences were preserved.

The earlier physics pilot was stopped for relocation; this historical candidate
did not match basal crack/collapse/run-out. It was stopped at t=111 s after
localized upper-face damage; a bounded native-aggregation preparation check
converged in 1658 updates, but this does not prove correct fracture. User requested
less repeated testing/token use, results first, and no UI work. Commit `8fba2b7`
was inspected: its runner uses a 100 m chalk example with default **stress** coloring
and no toe notch. A 100-update compatibility run did not establish basal damage;
see `output/reference-reproduction-2026-10-14/commit-8fba2b7-check/damage-audit.json`.
The supplied-folder `joss.lisp` matches the repository file after newline normalization.
Do not repeat the earlier broad investigations; use these saved results.

**Antigravity history recovered, 2026-10-15:** the exact conversation
**Clone and Run CL-MPM** was read from its local database, read-only. Before the
UI request, the runner used `examples/chalk/chalk.lisp`. After the user's blue
frame complaint, it switched from damage coloring to **Von Mises stress**;
the assistant then reported red at the base. The recorded patch supports a
stress-color explanation for the remembered red base, but does not establish
basal fracture or a validated Joss Bay collapse. The UI request comes immediately
after this explanation. See [ANTIGRAVITY_NATIVE_HISTORY.md](ANTIGRAVITY_NATIVE_HISTORY.md)
and `output/antigravity-history-2026-10-15/`. No additional simulation was run
for this audit. Keep stress and damage evidence separate and continue to defer UI.

**User-supplied damage video correction, 2026-10-15:** the subsequent WhatsApp
clip genuinely labels damage0–1 and shows a 31 m Joss-shaped case, not the 100 m
chalk example. A clear lower-face colored patch is visible at title t=15.87 s,
red by19.83 s, and spreading upward through39.67 s; the clip does not show a
completed run-out. The remembered result must not be dismissed as stress based
on the other runner's color change. `D:\model\render_video.py` closely matches
the clip and selects the VTK damage field. `run_joss_simulation.lisp` is an
earlier candidate (DR quasi-static/aggregation, Gf4.8, delay62), with WSL paths;
its exact identity with the clip is unproved, and later VTK/PNG outputs may have
been overwritten/cached. The clip's position before the blue-frame complaint
is also unproved. See the correction in
[ANTIGRAVITY_NATIVE_HISTORY.md](ANTIGRAVITY_NATIVE_HISTORY.md) and the extracted
frames/inspection under `output/antigravity-history-2026-10-15/whatsapp-video/`.
Next diagnosis should recover this Joss run rather than assume the 8fba2b7
100 m chalk default produced the supplied clip. No new solver runs were made.

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
7. **Reference-shaped Joss Bay experiment:** use the supplied paper/video and
   `examples/chalk/joss.lisp` for cliff geometry, crack growth, collapse and
   debris run-out. The user clarified that numerical identity is unnecessary
   and the research dataset is not required. See [REFERENCE_REPRODUCTION.md](REFERENCE_REPRODUCTION.md).
   The latest instruction prioritizes actual results and defers reference UI work;
   its draft is preserved in `output/reference-reproduction-2026-10-14/ui-draft.patch`.

**Critical distinction:** the user explicitly said this project is **not related to their thesis**. Never redirect the project to an unrelated thesis, machine-learning project, or geotechnical sensor optimisation. Keep the user's intended focus on this MPM simulator.

**Engineering values / shared approach:** preserve the established CL-MPM solver wherever possible; extend it through modular interfaces, not one-off hacks; keep the Windows workflow simple; maintain compatibility with existing configurations and upstream examples; make the output scientifically auditable; and mark experimental functionality honestly. The browser is a workbench/controller, **not** an alternative physics engine.

## 2. Current development topology (PR topology refreshed 2026-10-15)

The original four **open DRAFT stacked PRs** remain unmerged, with the same bases.

| Order | PR | Working branch | PR base | Change |
| --- | --- | --- | --- | --- |
| 1 | [#1](https://github.com/hadrianJavas12/MPM/pull/1) | `fix/studio-run-lifecycle-and-validation` | `main` | API lifecycle locks, video race protection, input controls, basic Node tests |
| 2 | [#2](https://github.com/hadrianJavas12/MPM/pull/2) | `feat/studio-notch-geometry-preview` | `fix/studio-run-lifecycle-and-validation` | Notch shapes, triangle-tip control, geometry preview, geometry tests and CI workflow |
| 3 | [#3](https://github.com/hadrianJavas12/MPM/pull/3) | `feat/studio-material-parameter-controls` | `feat/studio-notch-geometry-preview` | Cohesion, dilatancy, plasticity, nonlocal-length controls, elastic preset |
| 4 | [#4](https://github.com/hadrianJavas12/MPM/pull/4) | `feat/studio-custom-constitutive-lisp-export` | `feat/studio-material-parameter-controls` | Custom CLOS material model, Lisp editor/import/export, default-deny local execution |

Live refresh also found open draft [#6](https://github.com/hadrianJavas12/MPM/pull/6),
`feat/studio-modular-lisp-presets` → `feat/studio-custom-constitutive-lisp-export`.
It is separate background work; it is not checked out or imported into this
results task. Do not attach, rebase, merge or imply that its feature is shipped
locally. CI/billing evidence below remains dated rather than newly verified.

**Recommended starting branch for the next AI:** `feat/studio-custom-constitutive-lisp-export`. It contains the implementation of the current series, including the geometry fix inherited through an equivalent material-branch commit. The reviewed baseline before this hardening session was `95ded55b9fee22d9e5871d12d5bd09174a8a401f`. The implementation and synchronized docs/wiki are in commit [`52c5ed7`](https://github.com/hadrianJavas12/MPM/commit/52c5ed7c68985703f845b1331d389aab36664124); a subsequent documentation commit records this provenance. Query the branch for its current HEAD before continuing.

The earlier native Windows continuation cloned this branch into `D:\MPM\MPM-test`
at `a2e615712b14154a776dba6839041d34be9465cf`. PRs #1–#4 and their bases were
checked again and remain as shown above. The setup/output/UI fixes and new
verification evidence are local working-tree changes; no commit, push, PR edit
or merge was made in this session. Inspect that checkout's diff before continuing.

Ancestry check for that earlier `a2e6157` baseline: 41 commits ahead of `main`, zero behind;
the checked `main`, lifecycle and material heads are ancestors. Latest geometry
head `98eff24` is **not** a literal ancestor. Its fix is already present through
material commit `648ceca` with the same patch ID
`ba608523e5f0068a9e05f23465ce0caccbc60721`, and the actual app retains that geometry
update. No cherry-pick is needed. See captured `branch-ancestry.json`; do not
equate stacked PR bases with literal ancestry of every subsequently updated head.

**Current reference continuation:** the requested branch was subsequently
fast-forwarded to `f70e41080d46d33e46448a91e4bbb9e73c0e5318` after preserving
the prior dirty work. The saved recovery stash is
`afb61677825e76b8b28fea141eb5b66885c48c42`, recorded in
`output/reference-reproduction-2026-10-14/pre-sync-stash.txt`, alongside
`pre-sync-working-tree.patch`. Prior Windows fixes were reapplied. Keep those
recovery records/stash until the user decides to remove them. The local checkpoint
`feat(mpm): berhasil runtuh sesuai hasil visual yang disetujui` records the
accepted reference work and Windows fixes; inspect `git log` for its exact hash
rather than assuming the pre-checkpoint baseline is still HEAD.

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
| Joss Bay reference adaptation | `studio/lisp/reference-joss.lisp`; `studio/reference-presets.json`; `docs/REFERENCE_REPRODUCTION.md` |
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

Exported scripts are **NOT standalone**. They need SBCL, Quicklisp, CL-MPM and other repository dependencies. `public/config.js` shares API/export normalization and exports every schema setting with numeric limits/defaults/zero/false preserved. Lisp coercion matches decimal strings and positive half-up integer rounding. Reader/config/adjacent-source parity passed SBCL tests with dependency stubs. The subsequent full Windows trusted-delegate case also passed: all 28 config settings and exact source bytes matched, and mesh + three particle VTK + three PNG files were byte-identical between the browser and unchanged exported script. This covers that short configuration, not arbitrary laws or calibrated physics. Do not make export invoke arbitrary code silently.

## 4. Extremely important scientific distinction

The ordinary `studio-cliff` scenario in `studio/lisp/scenario.lisp` is a
**simplified chalk-cliff setup** derived from `examples/chalk/chalk.lisp`. A
separate experimental `joss-bay` path now adapts `examples/chalk/joss.lisp`
into geometry/material/equilibrium/accelerate/collapse stages. It remains under
native verification and is not a proven full reproduction of the published results.

The Studio runner currently loops `substeps` calls to `cl-mpm:update-sim` per output frame; defaults use fixed `*mass-scale* = 1d4` in scenario configuration. The original Joss example/paper involves specialised damage / relaxation / acceleration / dynamic collapse logic. Full reproduction requires separate implementation, tests and comparison to reference results.

That fixed loop describes the ordinary scenario. The dedicated reference path
uses a physical-time target, CFL-limited stepping and adaptive mass scale after
bounded initial elastic equilibrium. It writes time/phase/criteria/mass/damage
CSV and termination metadata; a frame cap or unconverged equilibrium must not
be reported as a complete collapse. The schema/profile exposes the paper's
conflicting 1 GPa prose and 100 MPa table moduli explicitly. Geometry details
not dimensioned in the paper are attributed to the author example/video.

**Never** call Studio results "validated Joss Bay results" or interpret damage contours / debris motion as physically predictive without establishing material calibration, time stepping, boundary conditions, mesh convergence and reference-case comparison. Do not invent or silently infer parameters from the original paper.

## 5. What has actually been verified — and what has not

Verified evidence from the earlier native Windows continuation (before the new reference changes):

- All PRs #1–#4 remain open drafts; their bases match the table above. The current Windows checkout started at `a2e6157`; older hardening baseline #4 was `95ded55`, ahead of `main` by 39 commits and behind by zero.
- Final Windows JavaScript syntax checks and **33 tests passed, zero failed/skipped**, with Node 24.13.0 and SBCL 2.6.9. Historical Linux hardening also passed 33 tests on Node 24.19.0/SBCL 2.2.9; its scope remains separately attributed.
- Three tests invoke a real SBCL reader/compiler/CLOS and compile the production `config.lisp` and `custom-model.lisp`. Their JSON/matrix/Quicklisp/runner dependencies are explicitly stubbed. This is **not** an ASDF/full-engine simulation or physical benchmark.
- API tests exercise both disabled and opted-in local policy, confirmation/size/NUL/Host/origin checks, exact source writes and concurrent-run locks; child launch is mocked.
- **CI cause confirmed again:** Actions run `38512874136`, check `115685122821`, has no executed steps. The public check annotation says the job was not started because the account is locked due to a billing issue. Hosted CI remains blocked until the account owner resolves that lock. Do not invent a code-based workaround or call it a passing run.
- The workflow now pins Ubuntu 24.04, uses Node 22, installs SBCL, and requires the contract tests. Its hosted execution is still blocked.
- Native toolchain ready: SBCL 2.6.9, Quicklisp client 2021-02-13/dist 2026-01-01, OpenBLAS 0.3.34, gnuplot 6.0 pl1, ffmpeg 9.0.1. Existing executables were reused; checkout-local Quicklisp/OpenBLAS were copied from `D:\MPM`. Setup passed and the corrected Quicklisp function independently installed fresh into a path containing spaces on Windows PowerShell 5.1.
- `scripts/smoke-test.lisp` ran through the Windows launcher: 100 particles, 50 updates, all positions/velocities/stresses finite, positive finite timestep and downward mean y (0.25 → 0.24322331 m).
- `scripts/studio-custom-smoke.lisp` ran with the complete engine: 64 final particles, two updates, 80 custom calls, maximum position/stress difference zero. Both VTK files passed readback of 36 finite scalar arrays and point/mass equality with the simulation. Plasticity/damage were disabled for this delegate comparison.
- Actual browser custom delegate run passed through API → Windows launcher → full engine: default plasticity/damage on, three frames/five updates per frame, status Finished/100%, exit 0, all three PNGs displayed. Unchanged downloaded `simulation.lisp` from a path containing spaces exited 0. All 28 config settings and exact source bytes matched; all seven VTK/PNG files were byte/hash identical. Particle output counts were 1120, 1120 and 1309 after splitting, with 36 finite scalar arrays each.
- Found and fixed fresh-Quicklisp quoting/init failures, malformed binary VTK from two Windows append handles, silent/missing/partial PNG completion and oversized button SVGs. The full-engine plot smoke passed success and failure paths. Independent output-parser review accepted fresh files and rejected seven corruptions, including preserved malformed baseline output. Solver numerical updates were preserved.
- **NOT VERIFIED:** arbitrary custom laws, the experimental custom elastic template under the full engine, long-run stability, full Joss Bay reproduction, calibration, mesh-independent predictions. The specialized particle-output parser is not a general VTK interoperability test.
- Historical wiki [[refactor-2026-10-14]] and immutable hardening evidence remain attributed historical reports. They are distinct from the new captured native Windows evidence.

See [testing.md](testing.md), [the Windows evidence report](windows-verification-2026-10-14.md) and `wiki-vault/wiki/studio-verification-2026-10-14.md` for exact scope. Evidence is locally preserved in `output/windows-verification-2026-10-14/` (git-ignored). Next: restore hosted Actions through the account owner, test the custom elastic law under the full engine and establish physical reference cases before predictive claims.
The temporary opted-in Studio server was stopped after testing. A normal new
launch retains default-deny custom execution; opt in intentionally for trusted
custom source as shown below. The evidence includes preserved `ui-run/` and
`export-run/` output copies.

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
windows\cl-mpm.cmd scripts\studio-plot-smoke.lisp
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
2. **Full-engine scope remains limited:** Windows elastic-block and custom delegate integration passed. The custom elastic template still needs full-engine analytical/reference comparison; arbitrary custom laws and long-run stability remain unverified.
3. **Exporter parity established for one short case:** all config/source and seven output files matched for the recorded delegate run. Add representative configurations/model laws and repeated-run cases before broader reproducibility claims. Preserve the local evidence before removing the checkout.
4. **UI validation limited:** the editor's "check" is a lexical delimiter/string/comment check, **not** semantic Lisp compilation, API conformance or proof of safety. Syntax highlighting and completion do not yet exist.
5. **Custom scripting security:** source is arbitrary code; localhost + confirmation are only *operational safeguards*, not sandboxing. Harden CSRF/local service exposures and avoid persistent unintended sensitive output; do not present current code as secure against malicious local/network actors.
6. **Numerical model:** stress update and independent damage evolution are separate APIs; implement them distinctly if the user requests genuinely custom damage laws.
7. **Geometry:** no freeform polygon/imported profile yet; sampled SVG preview may differ from discretised geometry. Validate at actual resolution.
8. **Run bookkeeping:** current Studio uses fixed output directories; source run locks guard concurrency, but per-run output isolation/historical run management remains a future task.
9. **Validation:** no demonstrated benchmark reproducing paper Joss Bay collapse stages or fracture-energy sensitivity.
10. **Documentation now synchronized:** the handover, setup/development/testing/custom contract, native Windows report and wiki describe the new full-engine/browser/export evidence. Historical reports remain attributed; keep scope and current evidence separate.

Report new discoveries as **confirmed by code**, **observed by tests**, or **hypotheses requiring investigation**. Do not hide unexpected errors.

## 8. Prioritised next work

**Current user priority overrides the backlog below:** the user accepted the
actual 40 s DP collapse/run-out visually and requested that it be committed with
an accurate success description. Preserve the accepted evidence and quantitative
limits; the later 40 kPa case completed without collapse. No further calibration
or simulations are requested, and the continuation heartbeat is PAUSED. Reuse
the completed validation; repeat checks only after a relevant change or failure.
Defer UI and the separate modular-preset branch.
The following priorities preserve the wider Studio backlog, not instructions
to restart completed smoke tests during this results task.

### Priority 0 — establish a green baseline
- Inspect the currently checked-out branch and stacked PR bases.
- Ask the account owner to resolve the confirmed GitHub billing lock; inspect a fresh Actions run. Do not repeatedly retry jobs while locked. Local Node/SBCL contract tests already pass.
- Repeat the captured Windows smoke, custom delegate, PNG and UI/export comparisons after relevant changes. The current local baseline passes; use [testing.md](testing.md).
- Establish a full-engine analytical/reference test of the custom elastic template and expand export comparison to representative configurations. Keep the existing contract/API denial/finite-output regressions required.

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

- **2026-10-14 native Windows continuation:** Cloned the requested branch at `a2e6157` into `D:\MPM\MPM-test`; refreshed the unchanged draft PR stack and CI billing lock (`38512874136` / `115685122821`). Completed checkout-local dependencies and verified fresh Quicklisp installation with spaces/PowerShell 5.1. Fixed Quicklisp quoting/init, Windows VTK text/binary stream corruption, silent PNG completion and button SVG sizing. Final Node checks/33 tests passed with zero skips. Actual launcher elastic smoke (100 particles/50 updates), delegate smoke (64 particles/two updates/80 custom calls, zero position/stress differences, 36 finite VTK scalar arrays) and PNG positive/negative smoke passed. Browser delegate finished 3/3 with damage/plasticity on; unchanged downloaded export ran from a spaced path. Independent comparison passed all 28 config settings, exact custom source and seven byte-identical VTK/PNG files; parser rejected seven corruptions. Saved evidence in `output/windows-verification-2026-10-14/`; updated this handover, documentation and linked wiki without changing immutable raw sources or prior log entries. Local changes remain uncommitted; no push, PR edit or merge. Numerical solver updates remain unchanged; physical calibration/Joss/mesh convergence and full-engine custom elastic validation remain open.

- **2026-10-15 visual acceptance and commit request:** after viewing the native
  DP collapse video and the completed 40 kPa image, the user accepted the actual
  40 s pilot as the requested visual result and requested a commit recording
  successful collapse. Preserved the measured mismatch (IoU 0.699825, run-out
  +7.8 m, plateau −5.2 m against reference t=221.14 s), warm-start provenance and
  unverified scientific status. The later 40 kPa production candidate completed
  221.14 s/111 frames without collapse (max damage 0.49062952033, mass-weighted
  0.008064637675); raw cap 5000 normalized to effective 2000. Continuation
  heartbeat `mpm-lanjut-setelah-reset` is confirmed PAUSED. No further
  calibration/simulation is requested. Updated diagnosis/reference docs and
  linked wiki, preserving immutable raw sources and append-only history.
  Actual Node 36/36 and native smoke/guard evidence remain distinct from
  scientific validation. Evidence is indexed under
  `docs/evidence/joss-collapse-2026-10-15/README.md`; no push/merge was requested.

### Useful navigation

- [Verification guide](testing.md)
- [Native Windows evidence](windows-verification-2026-10-14.md)
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
