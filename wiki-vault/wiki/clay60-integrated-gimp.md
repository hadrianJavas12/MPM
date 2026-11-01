---
title: Clay60 integrated GIMP
type: synthesis
tags: [cl-mpm, clay, gimp, numerical-evidence]
sources: [docs/evidence/clay60-integrated-2026-11-02/EVALUATION.md]
updated: 2026-11-02
---

# Clay60 integrated GIMP

Related: [[clay60-adaptive-kinematics]], [[clay60-worker-domain]].

## 2 November 2026 - integrated GIMP trial, tested before launch

User requested evaluation against the earlier Urmi result and an immediate corrected run. The actual Urmi slope_65_h manifest completed 80 frames/3200 updates/15182MP at 8.8579733295s, but its final maximum speed was 1294.0501619717m/s. Completion alone does not establish a valid landslide. Its executed MC-H law (E5.25MPa/rho1917.07/phi15..20/c5..7kPa), 65degree H12 geometry and 220-step plasticity-off settling/reset differ from this gravity-ramped 60degree clay case. Do not transplant that initialization or weaken this material merely to reproduce completion. Actual executed case, manifest and timeseries are preserved under docs/evidence/clay60-integrated-2026-11-02/controls/urmi-reference; generic effective-config strength defaults are not the executed law.

Proven numerical defect: native small-box GIMP formula loses partition of unity for some enlarged volume-based particle domains. Actual saved adaptive MP7926 at5s (x54.259935747605425,y8.57012360477069,J4.526118952734468) gives native cached sum1.0012582399841963 versus exact integrated sum1.0000000000000002. This is not proven the sole cause of MP7699 ejection. New opt-in clay-integrated-gimp-sim installs exact box-averaged linear-grid weights/gradients when half-domain>h/2; retains native arithmetic for small domains. Existing volume-based rectangular domain is retained, not physical-F CPDI. Exact domain integration follows Bardenhagen/Kober2004 Eqs19/20/23: https://www.sci.utah.edu/~guilkey/MPMPubs/BardenhagenKober%20copy.pdf . No renormalization, abs/clamp, F/material/force/guard relaxation, retry, domain enlargement or default-engine change.

Windows SBCL integrated-003 PASS:147phase/domain cases, partition/zero-gradient/linear reproduction/nonnegative weights, independent quadrature; actual saved native-cache defect reproduction/correction; native large-domain P2G mass/momentum/internal-force balance; 4 paired USF updates/all13517MP exact small-domain position/kappa/time parity; force-stage/ring trace and synthetic center/native-force failure capsules. Synthetic capsules are controls, not main-run failure evidence. Earlier001/002 retained. Studio check and36Node tests PASS. This is implementation evidence, not full-slope convergence or scientific validation.

New case clay-single-slope60-integrated.lisp retains adaptive timestep, ONE60/H10/crest24/base8/domain72x24/h.5/PPC2x2/13517MP, same quarter-clay law/USF/FLIP/noFbar/mass1/CFL.2/oneworker/2sgravity ramp. Target8s/17states/max80000updates,34h wall+<=2h automatic media is a budget, not ETA. Per-step actual pre/postforce extrema and last10step MP7699 tuple are captured; center/support rejection occurs without deleting/clamping particles. step-trace.json every100steps/final; actual-step-failure.json on error. Late F distortion and eventual finite-grid support loss remain possible. Do not identically restart or escalate mesh/time/material/weakening automatically.

Frozen saved-only observer will export three actual-F filled/allMP/equal-metre movies; motion and plastic use accumulated equivalent J2 kappa on one global scale, damage uses Dphi separately. Inspect actual failure/trace, all3PNGs/reviewJSON/source/DLL/finite/FJ/V0/mass/IDs/law/floor/work/yield/motion/KE/boundaries/distortion at terminal; deliver honest partial/full movies and archive actual source/runtime/raw/adjacent/detached/preparation/media ONCE. Old archives remain CLOSED.

## LIVE2Nov05:15WIB - integrated GIMP clay60 RUNNING, startup proof PASS

RUN output/clay60-integrated-2026-11-02/integrated-h05-001/sourceeea21e935fbbe44e72468c43f6b2db6f145da9d4 started2Nov05:11:53.909WIB;34h wall deadline3Nov15:11:53.909WIB/08:11:53UTC plus<=2h automaticmedia,budgetNOTETA. Worker44524/wrapper32976/nativecmd19044/SBCL46672 Session4,exact creations in adjacentstatus. Media47736 WMI WAITING_NATIVE return0. Initial watcher attempts failed BEFORE process creation (ShowWindow type mismatch then nonexistent ProgramFiles pwsh path); corrected uint16 and actual host pwsh path,zero duplicate media/native runs.

Actual frame0/13517uniqueMP/initialJ1/kappa0/VTK POINTS13517/317frozen source/actualmappedDLL PASS;new integrated-gimp.lisp actual firstparty ASDF load verified. Startup only,not full8s or physicalvalidation. Evidence docs/evidence/clay60-integrated-2026-11-02/launch and launch-index.json. Finite heartbeat pantau-clay60-gimp-terintegrasi ACTIVE15min;healthy narrow status/manifest/adaptiveStep/ONEstdouttail only,nohealthyPIDqueries/activepoll/tests/research/render/archive. Frozen4helpers automatically export3actual-Ffilled/equalmetre/allMP movies after actualexit;motion/plastic actual accumulatedJ2kappa globalfixedscale,damageDphi separate. Preserve step-trace.json and actual-step-failure.json with allactual raw/runtime/preparation/detached/adjacent/media atterminal. Inspect actualfailure/trace/all3PNGs/reviewJSON/sourceDLL/finite/FJ/V0/mass/IDs/law/floor/work/yield/motion/KE/boundaries/Fdistortion;completion alone notscientificPASS. Deliver partial/full scope honestly,archive ONCE/force-trackindexedmedia/rootGitblobverify/updateguide/testing/handover/wiki/index/appendlog/commitpush/deletefinite monitor afterclosure. No identicalrestart or material/mesh/time/weakening escalation. Oldarchives CLOSED.
