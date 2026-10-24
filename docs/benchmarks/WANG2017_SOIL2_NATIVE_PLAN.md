# Wang Soil2: native integration and prospective landslide evidence

Current objective: continue until the MPM simulation shows a real landslide.
Branch `codex/wang2017-soil2-landslide` starts from4036087. This is not permission
to force particle trajectories or tune parameters for a collapse. Completed
Soil1 fast010 remains a negative control, with immutable native/source evidence.

**24October result:** first full Soil2 trial exited1 at08:26:52WIB, before its
wall budget. Last saved state5.7s/57mm has19608loading updates; manifest19820
includes later unsaved work. Exact failure time/displacement is not recorded.
Actual captured point has no admissible coupled signed-history return, not a
history-decrease or multi-root rejection. The old-strength apex bound exceeds
trial mean by0.40894Pa; the relevant issue to audit is the bound after coupled
softening. Preserve this negative experiment; no identical restart or hidden
constitutive/tolerance change is permitted.
[Full failure and next-gate review](WANG2017_SOIL2_FAILURE.md).

**Subsequent gate,24October12WIB:** a separate explicit volumetric apex-flow
material now passes its native/input/regression and two-step output gates.
See [the apex-flow contract](WANG2017_APEX_FLOW.md). Strict class/defaults remain
unchanged. A prospective paired full slope changes only this declared material
convention; all numerical paper/loading/geometry settings remain the same.
This extension is not uniquely prescribed by Wang and does not guarantee failure.
Fresh paired trial apex-fast-010-001 on55bc85d completed13:33:43WIB without
error,6s60mm. Saved-state review finds no coherent landslide; reaction rises
and cohesion remains above residual. [Actual result and100mm endpoint study](WANG2017_APEX_TRIAL.md)
preserve this negative physical outcome without changing strength or rate.

## Material contract before enabling a slope run

Keep Table1 Soil2 inputs: E20MPa,nu.25,gamma20kN/m3,phi35/psi0; Cauchy cohesion
30→15kPa over paperkps0→.02. Paper Eq5–6 uses the norm of the accumulated signed
deviatoric plastic tensor, not an accumulated increment norm. Keep the existing
point projector, including every-root and admissibility checks. No apex clamp,
cohesion shortcut, fitted force curve or invisible irreversible maximum.

The paper does not fully specify finite-strain transport. The explicit MPM
adaptation here transports ONLY committed plastic tensor history by the proper
polar rotation of the same incremental deformation gradient that produces the
engine's elastic trial: Ep_rot=R_delta Ep_committed R_delta^T. The coupled
projector then adds its current-frame plastic increment. It does not rotate the
trial eigenbasis twice, stretch plastic history elastically, or use totalF polar
rotation. This is an objective corotated accumulator, not a claim that Ep=logFp
or that Wang uniquely prescribed this finite-strain law.

The need to rotate plastic tensor state is documented in official
[ROTSIG](https://docs.software.vt.edu/abaqusv2025/English/SIMACAESUBRefMap/simasub-c-tensor.htm).
Finite shear can distinguish objective-rate choices; see official
[stress rates](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-stressrates.htm).
The isolated signed norm can decrease under reversal. The native monotonic-scope
policy rejects a decrease beyond1e-13 rather than silently allowing healing or
replacing the history by max/summed increments. This guard is a declared model
scope, not a numerical remedy for softening or a guarantee the run will finish.
Positive plastic work does not guarantee increasing signed tensor norm on a
nonproportional path. Such a rejection is an unsupported interpretation/path,
not proof the physical path is invalid. The point projector still rejects
multiple admissible signed roots; no monotonic branch preference is added.

Current and committed tensor/rotation/history fields must be included in native
snapshot/restore/copy/reinitialize/load-step operations. No mutable snapshot
sharing; repeated trials use the committed history and must not double accumulate.
Native VM reporting remains an independent incremental-J2 quantity; never set it
to1.5times paperkps. Engine owns the Kirchhoff-to-Cauchy division by J.

Before a slope run, execute native point/rotation/transaction controls, old-MC
regression after the additive transaction hook, and a bounded actual MPM smoke.
Preserve failed controls and exact executed sources; report only their tested
scope. Existing model default behavior and Soil1 compiled configuration stay
unchanged. No long run while these checks fail.

## First physical comparison and evidence

Start Soil2 with the approved fast input0.01m/s to60mm/6s, same geometry/mesh/
solver/loading as completed Soil1. Keep actual Soil2 plastic state formed during
gravity equilibrium; resetting reporting origin does not reset its strength.
Save its changed settled state rather than manufacturing an identical baseline.

Record by particle ID: fullF9,positiveJ,initial volume,Ep6 in the declared frame,
increment rotation9,kps/cohesion and current/committed state. Record every strip
contact's reference/current centre/domain-top, width, gap and spring energy.
The added audit is read-only, optional and absent for legacy Soil1 runs.

Verify prospective landslide evidence using particles originally above the base,
excluding the six driven contacts: connected groups translating together,
horizontal/vertical motion and mass fractions, sustained localization/strength
loss, and reaction evolution against actual contact-surface descent. A colour
change, largest speed, vertical settlement or reaction drop alone is insufficient.
Run-out uses originally upper-slope particles crossing the original toe; base
particles already to the right are excluded. Check right-wall contamination.

If60mm does not produce failure, retain that negative result. An additional
predeclared candidate is drive60mm then hold3s, paired for both materials; it is
an extra experiment, not identical paper loading. A stationary bilateral strip
still restrains the soil and can release spring energy, so zero command work
does not establish zero loading or a closed energy balance. Do not start such
an extension until the first comparison identifies a physical reason.

Local softening is mesh dependent without a length scale; completion cannot
establish mesh-independent run-out. Height10m, bottom restraint, paper curve,
speed100x reference and unknown friend-FEM deformation magnification remain
separate limitations. Preserve all failures, bounded attempts and raw sources.

## Windows native commands

The completed point/transaction control is retained as frozen native003 in
`docs/evidence/wang2017-soil2-2026-10-24/native-integration-controls/`.
Actual frozen output002 now passes8groups,2genuineUSFupdates/25MPs/2VTKs.
It verifies real F/CSV/contact observations without gravity equilibration or
plastic flow. Failed001 fixture and exact source proofs are retained. This gate
permits starting the fresh first slope:

```powershell
Set-Location D:\MPM
pwsh -NoProfile -File .\scripts\start-wang2017-detached.ps1 `
  -Case cases/benchmarks/wang2017-soil2-fast-010.lisp `
  -OutputDirectory output/wang2017-soil2-2026-10-24/fast-010-001 `
  -MaxWallHours 2
```

This exact first run started24October07:03:31WIB on621146b and FAILED_NATIVE1
at08:26:52WIB, before2h budget09:03:31. Do not reuse the attempt directory or
repeat it without a diagnosed, tested reason. The tested
worker freezes sources/DLL before loading and retains actual process identities.
The2h budget bounds this first experiment; it is not predicted physical completion.
Soil1 took about45min, but Soil2 adds tensor transport/root searches and may reject
an unsupported path. Keep Windows awake and logged in; the worker does not prove
survival through logoff/sleep/reboot. Never overwrite or silently restart an attempt.
