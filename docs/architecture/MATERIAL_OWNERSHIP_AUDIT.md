# Native material ownership audit

Date: 2026-10-16 (Asia/Jakarta). **P0 source audit only; no migration or runtime verification.**
Inspected working tree: `codex/reusable-simulation-framework`, HEAD
`7c399fb23de8e04871855c3911d73e583fdbcdc3`. Read the operational handover
and the downloaded architecture migration specification first. This document
uses actual source forms and ASDF declarations, rather than interpreting a
filename as ownership. Root `materials/` is the final material owner; engine
particle contracts, numerical primitives and MPM/nonlocal machinery remain in
`src/`. Proposed paths below are decisions for later checkpoints, not installed
systems or claims that a model works.

## Reading this map

Locations use `path:line` or inclusive line spans from the inspected source.
Groups cover executable definitions; package forms and compiler declarations
must accompany their definitions without changing symbol identity, declaration
scope or reader-time dependencies. Comments are preserved source, not active
implementations. A lexical top-level scan ignored strings/line comments and
found balanced parentheses in every scoped Lisp file; it did not load Lisp,
finalize classes, resolve every dynamic caller or establish scientific validity.

Ownership codes: **E** engine; **N** generic numerics; **M** root materials;
**S** scenario; **O** generic output. A mixed group requires the stated split,
not a whole-file move. Preserve existing packages and public/internal symbols
through compatibility systems; a physical relocation is not a package rename.

## `src/particle.lisp`: engine and multiple material families

| Verified forms / lines | Final owner and extraction boundary |
| --- | --- |
| Package 1–32; `node-cache`, `make-empty-node-cache`, `reset-mp-node-cache` 37–53; `particle` 67–369 | **E**, base point/cache contract. Preserve every slot/accessor/initarg, including existing stress/strain, pressure, p-modulus and damage slots; moving those slots into new superclasses would exceed a behavior-preserving source extraction. |
| `particle-elastic`, `particle-linear-elastic` 380–407; modulus aliases/computation, `update-p-modulus`, `update-elastic-matrix` 410–445; `(setf mp-E/mp-nu)` after methods 447–450; elastic initialization/approximation methods 485–491 | **M**, elastic state/initialization. Retain `:elastic-approxmation` spelling and `:plane-strain` default. Modulus arithmetic delegates to existing numerical utilities. |
| Domain setter, `initialize-instance`/`reinitialize-instance` specialized on `particle` 452–483; `make-particle` 570–583 | **E**, allocation/domain state. Do not move these with the surrounding elastic methods. |
| `particle-fluid` 493–507; `particle-viscoelastic` 509–515; `particle-viscoplastic` 517–531 | **M**, respective fluid/viscous state. |
| `particle-thermal` 533–551 | **E**, reusable thermal field contract; model-specific coupled subclasses below remain **M**. |
| `make-particle-elastic` 595–600; `estimate-stiffness-hencky`, elastic/linear specializations 605–615; `estimate-log-enhancement` 620–637 | **M**, elastic construction and stiffness response. `estimate-stiffness` generic 602–603 remains **E**. |
| `constitutive-model` generic 640–643 | **E**, solver-facing dispatch contract; exact arguments/return convention retained. |
| Elastic constitutive method 645–651; `particle-elastic-inc`, `-jaumann`, `-truesdale`, `-logspin` and their methods 654–749 | **M**, elastic formulations; retain class names and class precedence. |
| Fluid/viscoelastic/viscoplastic constitutive methods 751–812 | **M**, corresponding model implementations. |
| `post-stress-step` generic/default 814–818; `assemble-vorticity-matrix`, `objectify-stress*` 824–909; `matrix-sqrt` 913–923 | **E/N**, generic objective mechanics/tensor operations, callable by material implementations. |
| `particle-damage-fundemental` 932–933 | **E**, generic nonlocal communication marker; preserve historical spelling. |
| `particle-damage` 934–1035; `new-loadstep-mp` damage specialization 1090–1115 | **M**, legacy shared damage state/adapter. This class mixes nonlocal fields with initiation/critical-stress/rate parameters: relocate the intact definition initially, rather than redesigning its slots. Nonlocal engine code must consume a lower protocol or load its typed adapter after this class. |
| `reset-loadstep-mp`/`new-loadstep-mp` generics and `particle` methods 1039–1088; `compute-mp-energy-release` generic/default 1120–1122 | **E**, generic lifecycle/energy contracts. |

## `src/constitutive.lisp`: formulas versus numerical primitives

| Verified forms / lines | Final owner |
| --- | --- |
| `linear-elastic-matrix`, `-principal-matrix`, `-matrix-ps`, `linear-elastic-mat`, `linear-elastic` 20–77 | **M**, `materials/models/elastic/`; stiffness matrices are constitutive formulas, despite broad use. |
| `eos-cole`, `eos-ideal-gas`, `newtonian-fluid` 79–93 | **M**, fluid models. |
| `maxwell-linear`, `maxwell`, `maxwell-exp-inc`, `maxwell-damage` 95–135; `maxwell-exp`, `-v`, `-v-simd` 369–449; empty `maxwell-forwards-fs` 1452–1454 | **M**, viscoelastic laws; preserve empty compatibility symbol pending caller audit. |
| `tensile-projection-eig`, `-Q-mandel`, `-Q-cw-mandel`, `tensile-project-q`, `tensile-projection-A`, `tensile-project` 154–296; `apply-damage-constitutive` 307–309 | **M**, shared damage response, not generic tensor algebra. |
| Top-level `let` 298–306 defining `voigt-4th-to-mandel` and `mandel-to-voigt-4th` | **N**, tensor conversion. Move the enclosing closure intact, including its captured `mandel-constant`. |
| `elasto-glen`, `elasto-glen-damage` 312–340; `norton-hoff*`, `glen-flow`, `glen-stress` 451–511; `glen-viscosity` 526–539 and `glen-viscosity-{strain,stress,stretch}` 548–574 | **M**, viscous/ice-family laws. |
| `voight-eye`, `voight-trace` 344–357; `deviatoric`, `deviatoric-mat` 513–522; `effective-strain-rate` 541–545; `voigt-j2` 577–584; `b-norm` 610–612; `rotate-vector`, `swizzle-voigt->coombs`, `swizzle-coombs->voigt` 790–814; `Q-matrix` 1228–1264 | **N**, tensor operations/conventions; preserve shear weights and component ordering. `swizzle-*` has actual VM/MC/DP consumers; the rate invariant is used by viscous/ice code. `b-norm` has only VM callers but implements a six-component Euclidean norm. |
| `vm-yield-func`, `vm-derivatives` 587–608; `vm-plastic`, `plastic-vm-tangent` 613–780; `secant-hardening` 1458–1500 | **M**, VM implementation/evolution. |
| `mc-yield-func` 784–788; `fast-mc` 843–845; `mc-plastic`, `mc-plastic-terzaghi` 852–1224 | **M**, native MC legacy implementation. Existence of the Terzaghi routine does not validate a coupled CU scenario. |
| `dp-yield-mc-circumscribe`, `dp-yield-mc-dp2` 816–841; `plastic-dp` 1267–1449 | **M**, DP model, with explicit reuse of tensor/elastic primitives. |

## `src/cpp.lisp`: a mixed, load-time backend transaction

`cl-mpm/ext` package 1–12 is a compatibility namespace. The library-directory
mutation at **17** uses `(asdf:system-relative-pathname 'cl-mpm "./libs/")`.
It does **not** derive its path from `*load-truename*` in this snapshot;
`windows/init.lisp:18` does use that variable for launcher-root resolution.
Keep both roots correct after relocation; do not substitute a new path model
without testing fresh-process loading and the Windows DLL search path.

| Verified group | Final owner / constraint |
| --- | --- |
| `kirchoff-expt-step-lisp` 26–88; `kirchoff-update` 328–332 | **N**, native-bridge/generic finite-strain mechanics. |
| Single `handler-case` 94–325; library declaration/load 96–100; `Kirchoff_Strain_Update`, `MatrixSqrt`, DR/test bindings 103–106,154–173 | **N**, shared library lifecycle and generic bindings. Keep the DLL/ABI and boolean/error handling unchanged. |
| `CppDruckerPrager`, `CppMohrCoulomb`, `CppViscoelastic`, `CppVonMises`, `CppVonMisesTangent` bindings 108–152; `constitutive-drucker-prager`, `constitutive-vm`, `constitutive-vm-tangent`, `constitutive-mohr-coulomb`, `constitutive-viscoelastic` 182–282 | **M**, `materials/backends/cpp/`, split by family after a common library handle exists. Preserve argument order, mutation, static-vector lifetimes and all returned values. |
| Accelerated `kirchoff-expt-step` 175–180, `matrix-sqrt` 283–288; load-error branch 290–325 | Mixed **N/M**. Current fallback defines Kirchhoff/MC/DP/matrix routines, an empty viscoelastic function, and **no VM/VM-tangent fallback**. DP's fallback calls MC and its argument order differs from the accelerated wrapper. Record these limitations; fixing them is separate behavior-changing work. |

Do not physically split the handler into independent loaders in P1: success
currently installs one group of definitions, and `load-foreign-library-error`
installs another. Silent fallback repair or switching C++ calls to Lisp formulas
would violate a structural-only checkpoint.

## `src/models/`: family state and methods

| Source groups | Final owner / exact method boundaries |
| --- | --- |
| `plastic.lisp:11–44`, `421–437` | **M**, genuinely shared plastic state and reset/new-loadstep methods. The `mp-strain-plastic-vm*` accessor names are also used by MC; keep semantics and names without making MC a VM subclass. |
| `plastic.lisp:46–71`, `126–242`, `273–326` | **M**, VM classes `particle-vm`, `-implicit`, `-hardening`; constitutive methods 126,173,273. `diff-tangent` 244–270 is **N**, finite differences of a callable response; preserve its tensor ordering and tolerance rather than creating a new material abstraction. |
| `plastic.lisp:73–121`, `328–419` | **M**, MC class/state, native backend dispatch and existing exponential strength evolution. |
| `plastic.lisp:123–124`, `440–504` | **M**, `particle-dp` and DP constitutive method; retain existing MC superclass. |
| `damage.lisp:13–46` | **E**, `particle-damage-mpi` communication state, not a material law. |
| `damage.lisp:50–123`, `167–206` | **M**, fracture and damage-family state: `particle-fracture`, `particle-elastic-damage`, `-tcs`, `particle-damage-frictional`, `particle-porodamage`, delayed/creep/elastic-fracture, viscoelastic/viscoplastic, thermal combinations and viscoelastic-fracture. Keep each multiple-inheritance list intact. |
| `damage.lisp:126–165`, `216–667` | **M**, damage reset/new-step/setter, constitutive/degradation/evolution hooks. Specializers at 216,284,290,308,451,467,483,503,563,580,603,612,636,639,663 distinguish the elastic, creep, viscous, delayed, TCS, frictional and poro variants; move each method with its family. |
| `damage-frictional.lisp:2–193` | **M**, frictional-damage classes `particle-plastic-damage-frictional`, `particle-fpd-{isotropic,tcs,tcs-strain,spectral,spectral-strain}`; initialize after 20, constitutive 46, driving 131, post-damage methods 40,177,180,183,187,191. |
| `chalk.lisp:13–53`, `56–192`, `632–1211` | **M**, chalk classes `particle-chalk`, `-creep`, `-brittle`, `-delayed`, `-delayed-grassl`, `-delayed-linear`, `-anisotropic`; constitutive 56,135; post-damage 632; empty `delay-damage-update` 643; evolution 672,797,1032,1119; driving 939,986,1067,1181. Preserve both `cl-mpm/particle` and `cl-mpm/damage` package contexts. |
| `concrete.lisp:10–97` | **M**, `particle-concrete` and constitutive method 30; its driving/evolution methods are elsewhere (`src/damage/damage.lisp:1194,1229`). |
| `limestone.lisp:9–156` | **M**, limestone/delayed classes 9,26; constitutive 34, post-damage 55, evolution 58,102 and driving 86. |
| `ice.lisp:11–529` | **M**, `particle-glen`, `particle-m-ice`, `particle-visco-elasto-plastic-damage`, `particle-ice-linear`, `-brittle`, `-delayed`, `particle-glen-damage`; constitutive methods 60,156,287,307,367,385. |
| `ice.lisp:532–921` | **M**, setter 532, `damage-response-linear-ice` 538, evolution 551,680,739, driving 624, compute 651, degradation 809, post-damage 873 and energy-release 898. |
| `visco.lisp:6–92`, `108–138`, `184–324`, `328–692` | **M**, finite viscous/Glen formulas; finite-viscoelastic and ice classes 328,338; constitutive 345,624; viscosity/iterators 384,396,441,494. `voight-trace-2d`/`voigt-eye-2d` 95–106 are **N**, generic tensor primitives; no new material abstraction is justified. `test` 158–182 is a callable exploratory helper to preserve pending separate test-organization work, not evidence of a test run. |
| `elastic.lisp:1–8` | Package-only stub; not the elastic implementation and not listed by current ASDF. Preserve pending separate caller audit. |

## `src/damage/`: do not move the directory wholesale

| Source groups | Final owner |
| --- | --- |
| `package.lisp:14–51` simulation classes; `calculate-damage` generic 53; `solver.lisp:2–175` three `update-sim` methods | **E**, damage-enabled USF/USL/MUSL/aggregate scheduling and its exact operation ordering. |
| `package.lisp:55–61` compute/update/set/post-damage/driving generics | **E**, lower engine–material protocol. Typed material implementations load after both protocols and classes. |
| `damage.lisp:19–22`, `39`, `189–385`, `432–674`, `721–801`, `811–968`, `1125–1154`, `1316–1433` | **E**, reset simulation, default no-op hook, local-length/search lists/weights, neighbor reflection controls, nonlocal averaging, G2P and damage invocation, add/remove MPs, convergence reduction and nonlocal interaction assembly. Typed material-state adapters must load after the preserved material classes. |
| `damage.lisp:54–63`; enclosing `progn` 394–419 (`diff-squared-mat`, `test-simd-acc`, `diff-squared`) | **N/E**, principal values and distance primitives; retain the callable helper without declaring validation. |
| `damage.lisp:6–17`, `24–37`, `44–52`, `65–188`, `676–719`, `804–810`, `976–1010`, `1015–1053`, `1161–1272` | **M**, damage energy/setter/reset adapter, rate/profile/increment law, `apply-damage` (145) explicitly calling the chalk rate law, stress-dependent effective-length and damage-dependent `length-localisation` (804), `damage-model{,-creep,-rankine,-chalk}` state, default damage driving/evolution and concrete driving/evolution. `compute-damage` no-op on `particle-damage` 1157 belongs with material compatibility; `particle` no-ops 1013,1156,1159 remain lower protocol defaults. |
| `criteria.lisp:3–395`, `430–596` | **M**, VM/MC/DP/Rankine driving criteria, strength conversions, pressure/tensile energy laws and degradation factors. Principal-strain eigendecomposition 424–428 is **N**. `criterion-j2` 349 is a material diagnostic wrapper over generic J2, not a new solver primitive. |
| `softening.lisp:5–211` | **M**, shared exponential/residual/linear damage responses, inverse history, ductility/fracture-energy relations; concrete 140–161 and chalk 175–196 law groups go to their families. Shared exponential response has actual chalk/ice/limestone/damage consumers. |
| `delay-damage.lisp:248–273` | **M**, the specific delayed driving-rate derivative and Heun/forward updates. |
| `delay-damage.lisp:276–361` | **N** candidates: `integrate-substep`, `auto-refine-substepper`, `secant-solver` accept functions; preserve tolerances/iteration order and existing wrappers. Do not generalize the preceding physical derivative into a numerical primitive. |
| `degredation.lisp:3–398` | **M**, all `apply-*` stress/stiffness degradation laws and `est-shear-from-angle`; retain historical spellings. |
| `ekl.lisp:2–153` | **E**, nonlocal interaction weighting/delocalization, remapping and debug helper; no new material family. |
| `output.lisp:4–28` | **M** field descriptors in the damage simulation initialization adapter; generic writer remains **O**. Preserve field ordering/append behavior. Remaining apparent writers are commented source. |
| `mpi.lisp:1`; `nonlocal-stress-based.lisp` | Package-only stub and empty file respectively; neither is a component of current `cl-mpm/damage`. No deletion authorized; `src/mpi/damage.lisp` is a different file. |

Two existing order-sensitive hazards must survive a structural checkpoint:
`set-mp-damage(particle-damage)` at `damage/damage.lisp:14` is replaced by
`models/damage.lisp:158`; and loading ice defines
`cl-mpm/damage::apply-vol-pressure-degredation` at `models/ice.lisp:809`, replacing
the same global function from `damage/degredation.lisp:127`. Do not accidentally
change which definition wins or present eliminating that override as a pure move.

## Framework material/scenario boundaries

| Source groups | Final owner |
| --- | --- |
| `components/materials.lisp:5–6`, `32–64` | **M**, material construction protocol/native class and initargs mapping. Preserve `:elastic` mapping to a plasticity-disabled `particle-vm`; choosing `particle-elastic` would change identity. |
| `components/materials.lisp:8–30` | Split **M/E**: native metadata normalization in `material-value` is material logic; run-local config inheritance in `resolve-material` is composition. Retain wrapper and exact metadata conflict checks. |
| `components/materials.lisp:66–74` `make-particle-factory` | **E**, material assignment plus block geometry construction; depends on material constructor protocol, not constitutive equations. |
| `components/diagnostics.lisp:4–139` | **M**, diagnostic protocol, adapters/modes/conventions, VM legacy values, MC corrected Kirchhoff residual/field descriptors, read-only state and validation. Preserve explicit MC phi=0 rejection and unsupported mode gates. `material-state` 100 is not a transaction/rollback API. |
| `components/diagnostics.lisp:141–188` | Split **O/M**: output namespace expansion/reservation and registration mechanism (141,152,174) are generic output adapters; model descriptors/accessors remain materials. Preserve per-simulation ownership and VM byte behavior. |
| `materials/chalk.lisp:5–32` | **M**, `joss-reference-chalk` slots, initialization after method 13 and dedicated driving law 23. Keep its existing package/symbol identity, even after removing the scenario dependency. |
| `materials/chalk.lisp:34–36` | **S/E** adapter: Joss-specific `update-particle` selects existing Kirchhoff/domain update mechanics; not a constitutive law. Load this integration method after the model class and engine. |
| `materials/chalk.lisp:38–88` | Split **M/S**: native material initarg/reference parameter recipe versus particle block generation, gravity and config-unit conversion in `make-joss-chalk-mps`/`make-chalk-mps`. These functions currently depend on cliff `param`/`deg->rad`; whole-file relocation would retain a material→scenario dependency. |
| `scenarios/triaxial/material.lisp:4–11` | **M** construction adapter plus **S** legacy config translation; preserve the `rho=sqrt(8/3)*su` arithmetic and wrapper. |
| `scenarios/triaxial/material.lisp:13–25` | **S**, `initialize-prestress`: cell pressure and specimen stress/strain initial conditions, not a reusable material law. |
| `scenarios/joss/classes.lisp:5–9` | **S**, `joss-reference-sim` and aggregate stabilization subclass; neither is material state. |

`framework/components/specifications.lisp:4–7,26` currently owns `component`,
`material` and `make-material`. Those prerequisites must accompany a P1 contract
move or remain available through an explicit lower compatibility protocol;
relocating only `components/materials.lisp` does not create an independent registry.

## ASDF order, cycles and first safe checkpoints

The current lower chain is `utils/fastmaths → constitutive → ext → particle`
(arrows mean prerequisite before consumer). `cl-mpm.asd:97–126,245–254`
loads `particle.lisp → models/plastic.lisp → models/concrete.lisp` serially;
there is no separately declared `cl-mpm/models/plastic` system. Material class
definitions therefore live inside the existing particle system. Concrete's
`particle-elastic-damage` superclass is only defined later by the damage system:
retain/defer that forward reference carefully, rather than adding
`particle → damage → particle`.

`cl-mpm/damage` at `cl-mpm.asd:128–153` depends on particle, output, ghost and
aggregate; output depends on `cl-mpm`/core. Its serial order is package,
softening, criteria, EKL, damage, delay, degradation, output, solver, then
models/damage and models/damage-frictional. Chalk depends on particle and damage
(724–732); visco on `cl-mpm`/particle/ext (752–758); ice on particle/chalk/visco/damage
(735–742); limestone on particle/damage (744–749). Moving the entire damage
system under materials would make the constitutive layer depend on MPM solvers.

`framework/cl-mpm-framework.asd:3–31` loads specifications → materials →
diagnostics, then cliff settings → chalk → builders, then Joss simulation
classes/operations, then triaxial package/config/tensors/material/geometry/etc.
Studio depends on this framework (`studio/lisp/cl-mpm-studio.asd:7`); old system
names remain compatibility entry points until the migration gates pass.

**P1 recommendation:** extract package/base particle and generic lifecycle,
constitutive and damage protocols below both solvers and material modules;
move material definitions/construction contracts into root `materials/core/`
with old symbols re-exported or compatibility-loaded exactly once. A registry
must select existing native classes, not redefine them. Reject material→scenario,
numerics→model, and new family→legacy-particle-umbrella→same-family cycles. Use
explicit base systems; names alone do not establish acyclic dependencies.

**P2 first family recommendation:** elastic state/constructors/constitutive
methods and elastic formulas listed above, retaining all `cl-mpm/particle` and
`cl-mpm/constitutive` symbols. It has no damage-scenario coupling and supplies
the ancestors required by VM/MC. Keep generic objective/tensor routines below
it, leave the shared DLL loader and every native wrapper byte-identical, and
load elastic state before plastic subclasses. Preserve legacy umbrella ASDF
systems as aggregation/compatibility entry points without reloading old forms.
Next extract VM with the shared plastic state protocol and its existing DLL
backend, then MC/DP, then damage/chalk/ice integrations one family per checkpoint.

Before each actual move, freeze complete executed source and DLL hashes,
record class precedence/slots/initargs/method qualifiers and backend selection,
and test fresh-process ASDF/legacy loaders. Required acceptance includes native
class identity/construction, focused material contracts, actual Windows SBCL,
VTK/CSV comparison against unchanged deterministic references and the existing
parallel-Joss failure kept explicit. P0 documentation does not satisfy G1/G3.
No tests, solver jobs, DLL builds, production edits or numerical fixes were
performed for this audit.
