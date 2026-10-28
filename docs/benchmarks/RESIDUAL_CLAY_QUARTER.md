# Peak-initial residual clay slope, positive quarter residual strength

Human explicitly selected: use prior3D triaxial clay parameters, finer mesh,
start at peak strength then soften to one quarter. Main RUN NOW requested.
Native source82bce9b49642f919151f3f65904ded47e696c60e, branch
codex/resende-slope-material. Started28October08:44:10.788599WIB.
RUN output/residual-clay-quarter-2026-10-28/main-h05-001.
Native22h budget until29Oct06:44:10WIB plus<=2h saved export, not completion ETA.

## Inputs and explicit adaptation

E20MPa,nu.2,rho2000kg/m3,c0,psi0 from actual T-100-H/HS case settings.
Source PDF calls residualsoil; human identifies clay. Actual density differs
from source PDF gamma16.83kN/m3 and is intentionally the prior numerical value.
40deg/H10/crest24/base8/domain72x24; h.5m/PPC2x2 gives14010actualMP.
0.5m is the selected resolution, not a universal mesh-size standard.

Initial stress0/Fidentity/kappa0; HUMAN-APPROVED initial phi33.99deg, so original
phi0 hardening segment is explicitly replaced, not silently preloaded/reset.
Plateau untilkappa.037; phi25.353762870428053atkappa.1; phi9.568041272839212
atkappa.2 and beyond. This retains source postpeak coordinates and rescales
its loss fractions in tanphi so residual tau/peak tau=.25 at SAME POSITIVE
normal effective stress (c0). Not a fourfold division of angle or triaxial q.
At zero normal stress cohesionless strength can still be zero; no fake tensile
strength introduced. D_phi=1-tan(phi)/tan(phi_peak), max.75, is strength-loss
visualization, NOT stiffness/crack/cohesion damage. Urmi40500cohesion formula
and drained-to-undrained material switch are NOT used. Laboratory100kPa cell
confinement is NOT applied to the slope; not a coupled CU/pore-pressure model.

Gravity ramp2s from zero stress; every actual motion/softening frame during
ramp is saved. No stablegeostatic/preparationPASS claim, no force gate hiding
initialcollapse on40deg slope with c0/peakphi33.99. Native local damping.75
ramp/.02after; mass1/USF/FLIP/CFL.2/oneworker. Published volume-based cpGIMP
l_i=l_i0 sqrt(J) as prior optionalnumericalprofile, positiveJ/domainguards
and native strictMCroot/tolerances retained. No field/history reset/notch/
actuator/additional weakseed. Target20native seconds INCLUDINGramp,41states.

## Execution/evidence scope

ActualWindowsSBCL compiled newnative modules, created14010MP and saved actual
frame0; main process NATIVE_RUNNING. New source parameter/algebra/lexical
checks done; no claim of scientific or terminal nativePASS. Studio check+
36testsPASS, no old material/Urmi/failed-native suites repeated. No new
material-return acceptance tolerances or root preference. Source snapshots
were automatic BEFORE any main project load; native provenance/DLL bound.

Native worker45936/wrapper11732/cmd22224/SBCL34936,Session11; exactcreation
and parent proof saved once. WMI mediawatcher46344 created separately with
hidden window. WMI session NOT proven sleep/logoff/reboot immune.

Four observer/helper files frozen AFTERnative launch BEFOREfirst savedobserver;
analysis-freeze.json states timing honestly. New observerPythonAST/PowerShell
watcherAST checked; full savedworkflow NOTEXECUTED yet. Watcher automatically
runs terminal savedobserver (not another solver), snapshots announced CSV/VTK
prefix, checks IDs/FJ/originalV0/mass/law/quarterfloor/yield/work/coherentupper
motion/KE/runout and renders allF-convected materialpatches/equalmetres/no
interpolation/filtering. Output RUN/filled-review-001/soil-motion.mp4 and
strength-damage.mp4, proper-motion-result.png/proper-damage-result.png.
Native complete/colours are not calibratedvalidation. Onfailure preserveall
logs/frozenoriginals and repair savedanalysis/media only; no identicalrestart.
Native wallcap may leave manifestrunning; stoppedwrapperproof required before
partialprefix inspection. Frame0 is initialization only, not slide evidence.

Hourly quiet monitor pantau-clay-mesh-0-5-m, no healthyactivepoll/PIDqueries/
retests/rerenders/research/archives. On meaningful terminal inspect BOTH actual
PNGs and deliver bothactualmovies honestly. Archive this source/raw/runtime/
preparation/media onceATTERMINAL and Gitblobverify, not whilewriting. No
UI/mainmerge/private/raw/settings change. No automatic further escalation.
