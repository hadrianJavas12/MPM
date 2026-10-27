---
title: Urmi inspired MC strength damage at 40 degrees
type: synthesis
tags: [mpm, soil, mohr-coulomb, strength-damage, urmi]
sources: [docs/benchmarks/URMI_MC_DAMAGE40.md, research/notes/urmi-mc-damage40-2026-10-26/constitutive-plan.md, research/notes/urmi-mc-damage40-2026-10-26/recipe-plan.md]
updated: 2026-10-27
---

# Urmi inspired MC strength damage at40degrees

Human retains soil MC, requests40degrees/no notch/longer run and damage.
Branchcodex/urmi-mc-damage-slope40 fromc2cd4069. Provisional Joss prototype
is preserved but not the requested material. [[urmi-legacy-comparison]] and
[[unnotched-mc-gravity]] distinguish historical experiments.

S1 undrained phi=psi0 uses sup40.5kPa, intermediate3.8475kPa, residual1kPa,
G4.05MPa and nu.45. D_s=1-su/sup is actual constitutive strength loss with
unchanged elastic stiffness; it is not crack opening. A declared continuous
normalization and elastic unloading map total DSS shear to native equivalent
plastic history. This is Urmi-inspired, not literal field calibration or a
pore-pressure solution. Local softening remains mesh dependent.

FIRST native point961c17a8 passes5groups/84pureprojectorentries/3nativeattempts/
2accepted/0MPM, including both edges/sixpermutations/currentJ and rollback.
Actual26segments have certifiedchordbound81.900697Pa/sample75.428741Pa.
FIRST transfer946dbce7 passes4groups/6nativeattempts/6accepted/0MPM. It prepares
owned clones, preserves globalF/history/nativeclock and swaps only after all
candidates pass. New compliance and native dt0 material release are explicit
distinct events; energy proxies are not an energy balance. Nodecheck/36pass.

FIRST recipe96f0c7d6 pipeline PASS4groups/4USF/6714MP(3840soilfoundation),
13428drained+6714instantaneous transfer+13428undrained accepted calls,
3VTK/20142CSVrows. Independent saved002audit/source302/DLLPASS, root actual
scale1geometry inspected. Python8unchangedhelpers+1selectivefixture repair
PASS; initial incorrectfixture and initial missingorigin audit harness failure
retained. No solver repeat. Full60s slope remains NOT_RUN. Actual benign timing
suggests~23.3h dynamics, not ETA; prelaunch wallcap48h instead of initial12h.
Stable drained
ELASTOPLASTIC gravity initialization needs measured free-force/free-KE
convergence and undamped persistence. No elastic-only initialization/reset,
notch, driver, root preference, clamp or postfailure parameter tuning.

## LIVE27October10:33WIB

Full001 source3acf468f now ACTIVE,48hwallcap/notETA; still drainedpreparation atcapture, not equilibrium/full60sPASS. Exact300native source/DLL/prelaunchbinding/liveidentity proof archived27indexed/483members. First clockprovider helper rejection retained, no nativecode change. Quietautomation urmi-mc-40-native-trial15min; terminal ONEprepared savedreview, no solverrerun for media/readerfailure. Initial drained-to-undrained change is declared; subsequent plasticdeformation drives Ds softening, no imposeddisplacement/porepressure/rainfall claim.
