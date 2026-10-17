# Native model catalog

Checkpoint: P2 A–D and P4D, 2026-10-16. These are installed source owners and
existing class identities; availability does not establish calibration,
convergence or experimental agreement.

Names below retain the `cl-mpm/particle` package unless qualified otherwise.
Paths are relative to root `materials/`; families share the unchanged base
particle and `core/plastic-state.lisp` contracts.

| Class / selection | State and constitutive owner | Evolution / backend |
| --- | --- | --- |
| `particle-elastic`, `particle-linear-elastic`, objective elastic variants | `models/elastic/{particle,constitutive}.lisp` | Generic objective mechanics in `src/numerics/tensors/particle-objectivity.lisp` |
| `particle-fluid` | `models/fluid/{particle,constitutive}.lisp` | Existing EOS/Newtonian laws |
| `particle-viscoelastic` | `models/viscoelastic/particle.lisp`, `models/viscoelastic/maxwell/constitutive.lisp` | Existing Maxwell response |
| `particle-viscoplastic` / Glen laws | `models/viscoplastic/particle.lisp`, `models/viscoplastic/glen/constitutive.lisp` | Existing rate laws |
| `particle-vm`, `-implicit`, `-hardening` | `models/plastic/von-mises/{particle,constitutive}.lisp` | Legacy `evolution/secant-hardening.lisp`; native VM/tangent wrappers |
| `particle-mc` | `models/plastic/mohr-coulomb/{particle,constitutive}.lisp` | Existing legacy strength evolution in `particle.lisp`; native MC wrapper |
| `particle-dp` | `models/plastic/drucker-prager/{particle,constitutive}.lisp` | Original MC superclass and DP backend behavior |
| `particle-damage` and elastic/creep/poro/thermal combinations | `models/damage/{particle,legacy-particles,legacy-state-evolution,constitutive,criteria}.lisp` | `models/damage/evolution/{responses,delayed-rate,degradation}.lisp` |
| `particle-plastic-damage-frictional`, `particle-fpd-*` | `models/frictional-damage/legacy.lisp` | Existing driving/post-damage methods |
| `particle-chalk*`, `cl-mpm/framework/cliff::joss-reference-chalk` | `models/chalk/{legacy,joss-reference}.lisp` | `models/chalk/evolution/softening.lisp`; construction in `adapters/chalk.lisp` |
| `particle-concrete` | `models/concrete/legacy.lisp` | `models/concrete/evolution/{softening,native-hooks}.lisp` |
| Finite viscoelastic / `particle-finite-viscoelastic-ice` | `models/viscoelastic/finite-strain/legacy.lisp` | Original exploratory helper retained; generic 2D tensors in `src/numerics/tensors/voigt-2d.lisp` |
| `particle-glen`, `particle-ice-*`, coupled ice variants | `models/ice/legacy.lisp` | Original ice evolution, including its inherited global override |
| `particle-limestone`, `particle-limestone-delayed` | `models/limestone/legacy.lisp` | Original limestone response/evolution |

Native wrappers share `backends/cpp/legacy-transaction.lisp`. Kernels and the
distributed DLL remain `libs/src/constitutive.h` and `libs/kirchoff.dll`.
Lisp fallback availability is unchanged; relocation added no fallback or model.

## Units, identities and modes

| Quantity | Convention |
| --- | --- |
| Component lengths, density, time | m, kg/m³, s; adapters preserve explicit legacy mm/% conversions |
| E, cohesion, undrained strength, stress | Pa; Poisson ratio and strain fractions are dimensionless |
| Native MC `:phi`, `:psi` | Radians; diagnostics retain angle/cohesion checks and native phi=0 rejection |
| MC diagnostic residual | Signed Kirchhoff Pa, `tau = J * sigma_Cauchy`, tension-positive |
| Accumulated plastic strain | Existing native measure; diagnostics describe its 1.5 factor relative to conventional VM equivalent increments; history measures require model-specific interpretation |

`:von-mises` selects VM; legacy `:elastic` selects VM with plasticity disabled.
`:native :particle-class 'cl-mpm/particle::particle-elastic` selects actual native elasticity.
MC stays independent of VM; DP retains MC ancestry. `adapters/native.lisp`
checks explicit metadata against native initargs. `material-state` provides
read-only diagnostics, not a rollback snapshot. Homogeneous/control modes remain
capability-gated. Dedicated MC H/HS integration and universal transactional state
are not supplied by this migration.

## Evidence and retained exceptions

P2 A/B/C/D each passed five fresh native catalogs: 20 exits 0 and all `.sexp`
files byte-identical to `p2-baseline-002`, with source/DLL hashes unchanged.
Final catalogs executed `f9ba947`; local evidence is
`output/architecture-migration-2026-10-16/p2-d/catalogs/`.
This establishes class/slot/CPL and constitutive-method metadata compatibility.
Solver/G3 acceptance remains separately tracked. The cancelled full Joss serial
run is not a PASS and must not restart.

- The atomic C++ handler cohosts generic ABI/Kirchhoff/matrix operations and
  material wrappers. Its asymmetric/partial fallback behavior is preserved.
- The later damage-model `set-mp-damage(particle-damage)` method remains the winner.
  Optional ice still replaces `apply-vol-pressure-degredation` when loaded.
- Concrete's forward reference to the later elastic-damage superclass remains;
  no particle-to-damage dependency cycle was introduced to conceal it.
- Common stress/strain slots remain engine-owned. Shared legacy damage state
  retains its intact mixed slot definition rather than new superclasses.

See [compact form map](P2_COMPACT_MIGRATION.json),
[material API](../../materials/README.md) and [ownership](FOLDER_OWNERSHIP.md).
