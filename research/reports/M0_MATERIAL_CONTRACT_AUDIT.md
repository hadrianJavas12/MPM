# M0 material and diagnostic contract audit

Date: 2026-10-16. Inspected baseline: `909fddf31420d61fdea70ea720098ec457a0249e`,
branch `codex/reusable-simulation-framework`. Read-only source audit before the
framework changes described in the later implementation record. This is neither
a solver test nor scientific validation. Root refreshed live GitHub topology;
native serial regression results are recorded separately by root.

## Findings and priorities

| Priority | Baseline evidence | Consequence |
| --- | --- | --- |
| P0 | `framework/components/materials.lisp:32–74` already selects a native particle class and constructor arguments; `framework/scenarios/triaxial/adapter.lisp:45–46` and `geometry.lisp:47–49` require VM inheritance. | A real native MC factory exists, but general triaxial construction rejects it. Relax these guards only alongside a compatible measurement adapter. |
| P0 | `framework/scenarios/triaxial/measurements.lisp:44–49` reads the shared plastic accumulator and VM-only `mp-rho`, calculating normalized VM yield excess. | That formula must never diagnose MC. `qJ2`, projected axial-minus-mean-lateral q, mass, volume and finite stress checks remain useful for either law. |
| P0 | `framework/scenarios/triaxial/runner.lisp:33–46` labels every run VM and writes VM plastic/yield conventions. | Record actual native identity and each adapter's stress, state and availability conventions. Missing VM fields need blank/unavailable values for MC. |
| P0 | `framework/scenarios/triaxial/homogeneous.lisp:5–17,65–70` restores/copies selected VM state; `runner.lisp:15–18` sends controls to `run-controls` without the supplied factory/filter. | Non-VM homogeneous/controls must fail explicitly until complete state snapshot/restore/copy contracts exist. Reject unsupported controls callbacks rather than silently running default VM. |
| P1 | `src/output.lisp:443–480` installs per-simulation scalar/vector/Voigt output lists. Legacy scalar fields substitute zero when state is absent. | Preserve legacy VM exports. Configure only a new run's output list for MC, replacing misleading plastic/yield aliases with explicit MC names; no global writer override is necessary. |

## Native MC mechanics that must stay separate from framework refactoring

`particle-mc` inherits `particle-elastic` and `particle-plastic`, **not** VM
(`src/models/plastic.lisp:73`). The shared accumulator has a historical VM name
(`:17–27`), so its presence does not imply VM mechanics. Native MC invokes the
existing C++/Lisp return map (`:371–396`). Its increment is
`sqrt(0.5*((d1-d2)^2+(d2-d3)^2+(d3-d1)^2))`, where `d` is the principal
elastic-strain correction (`libs/src/constitutive.h:283–288`); this is
`sqrt(3 J2(dev Δεp))`, or **1.5 times** conventional equivalent plastic strain.
It is not automatically the PDF's strain definition or a strain multiplied by 20.

Both C++ (`libs/src/constitutive.h:230–234`) and Lisp
(`src/constitutive.lisp:890–895`) form the apex as `sigc/(k-1)`, with
`k=(1+sin(phi))/(1-sin(phi))`. At `phi=0`, this divides by zero; at `c=0`
the expression is `0/0`. This is a source-level failure risk whenever yielding
enters that branch, not an executed test result. Do not silently alter source
table values. A dedicated future MC implementation needs a tested zero-friction
limit, corners/apex, non-associated flow and independently recomputed final yield.

The C++ return stores **trial** `f` (`constitutive.h:227,305`); Lisp returns
`initial-f` (`src/constitutive.lisp:879–880,1006–1033`). Therefore the stored
`mp-yield-func` is not the corrected yield residual. Recompute
`k*tau_max-tau_min-2*c*sqrt(k)` from `tau=J*sigma_Cauchy` and current strength,
using the native tension-positive convention. Keep the signed residual in Pa
separate from VM's normalized positive excess. There is no pore-pressure field.

Legacy exponential softening changes cohesion and friction **after** return
(`src/models/plastic.lisp:404–415`), with only one outer iteration (`:358`);
`reset-loadstep-mp` restores only the scalar accumulator before its base method
(`:421–438`). This does not establish coupled hardening/softening consistency or
rollback of strength. Preserve legacy equations; new H/HS classes must own complete
trial/commit/rollback state. `src/cpp.lisp:244–271,290–314` selects native acceleration
or a Lisp fallback; retain binary/backend provenance when later testing either.

## Minimal M0 implementation boundary

1. Keep material class/initargs dispatch. Add a run-local diagnostics adapter with
   explicit compatible particle type, supported modes, read-only state fields,
   conventions and per-simulation export fields. No new constitutive equations.
2. Retain the existing default VM CSV ordering, formatting, arithmetic and VTK
   fields. For MC, leave VM-only columns blank and emit named MC state/yield
   fields in a companion CSV and native VTK; mark unavailable fields in metadata.
3. Permit spatial MC and linear elastic construction with compatible adapters;
   preserve common stress/kinematics/mass checks. Reject unsupported material and
   mode combinations before output, especially custom controls and non-VM
   homogeneous evaluation. Complete constitutive snapshot hooks remain M2 work.
4. Verify independent residual values for known stress states, MC class identity,
   unavailable fields, per-run output isolation, explicit rejection and unchanged
   VM serialization. Run only bounded native integration before broad regression.

Canonical config currently reads `studio/schema.json`; moving that contract needs
a compatibility migration and is an explicit follow-up, not a reason to change UI
or Studio files during this bounded adapter change. Local softening, mesh/timestep
sensitivity, physical calibration and true CU behavior remain outside M0 acceptance.
