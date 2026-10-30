# Toe initiation: distinguish plastic strain from strength loss

30 October 2026. Human explicitly asks to check Urmi/Wang, correct the case and
run again without a notch. Branch `codex/clay-toe-profile`.

## Actual old-run evidence

Original saved data are unchanged. New read-only onset queries:
`output/toe-initiation-2026-10-30/old-run-plastic-strain-onset.json` and
`old-run-onset.json`. At the first nonzero saved state0.5s, maxkappa
0.000417832891 occurs at initial(34.125,9.375)m, near toe(35.9175,8)m;
345MP in the declared +/-3m toe box have kappa>1e-8. This is evidence of
EARLY TOE PLASTICITY, not yet strength loss. At1.5s toe maxkappa.01327 remains
below the unchanged peak plateau endpoint.037. At2s the first saved Dphi>1e-6
has235MP near crest/upper face and0in the toe box; maxD.1674 at initial
(23.875,17.875)m. Toe plasticity therefore precedes crest strength-damage.
The old statement that all failure initiation was from crest is too broad.

Urmi's plotted deviatoric shear strain is NOT our friction-loss Dphi. New
third movie shows accumulated J2-equivalent plastic kappa, a related but
not identical strain convention. A zero Dphi colour does not mean no yielding.

## Primary reference check

- Urmi et al.2024, DOI[10.1016/j.enggeo.2024.107669](https://doi.org/10.1016/j.enggeo.2024.107669),
  local PDF `docs/Prediction of retrogressive landslide in sensitive clays.pdf`,
  SHA2563f6aa9f5ba914564df3031aa8d6853ffef91b045a433446126e49316c150785a.
  Pages4-9/text and actual geometry/strain figures5/11 inspected. Saint-Jude
  has a40degree toe, upper12-20degrees, layered crust/clay/strongerbase,
  drained elastoplastic gravity equilibrium then undrained softening.
  Paper describes circular shear surface originating at toe. Its site height,
  strength layers, initialization and calibrated strain law differ from ours.
- Wang et al.2017, DOI[10.1007/s11629-016-3951-1](https://doi.org/10.1007/s11629-016-3951-1),
  [author PDF](https://www.researchgate.net/profile/Qiguo-Rong/publication/312201146_Stability_analysis_of_slope_in_strain-softening_soils_using_local_arc-length_solution_scheme/links/59cdde08aca272b0ec164432/Stability-analysis-of-slope-in-strain-softening-soils-using-local-arc-length-solution-scheme.pdf),
  printedpp179/181/184-186 checked. Separate homogeneous benchmark applies
  displacement at crest after gravity initialization. The field example's
  toe-originating slip follows staged excavation. Do not imply that this
  excavation protocol satisfies our no-notch/no-removal request.

## Declared new comparison

Retain prior triaxial clay E20MPa/nu.2/rho2000/c0/regularpsi0 and exact
human-approved peakphi33.99/plateau kappa.037/quarter residual tanphi
(residualphi9.56804127,Dphi<=.75). Retain explicit opt-in HS gA=p apex extension,
not paper-specified, strict regular shear. No new weakzone, notch, driver,
preload, field reset, material switch or regional strength change.

Change ONLY slope profile: totalH10; upper7m height at20degrees, lower3m at
40degrees; crest24/base8/domain72x24; kinkx43.23234194,toex46.80760271m.
The3m lower-face height is an explicit adaptation, NOT a dimension from Urmi.
Mesh.5m/PPC2x2 ->15143actual center-clipped MPs (independent Python grid agrees).
Same volume-cpGIMP, mass1, one worker, CFL.2, FLIP, noFbar, localdamping.75
during2s smooth gravity ramp then.02. Zero initial stress/history; record
all motion. NO measured-geostatic-equilibrium or faithful Urmi reproduction
claim. Geometry is a finite hypothesis for localization, not a toe guarantee.

Focused target8native seconds/17states,22h wallcap plus<=2h automatic saved
media (budget NOT ETA). This does not complete the previous20s target.
RUN `output/clay-toe-profile-2026-10-30/profile-h05-001` is freshinitialstate.
Three saved-only filledpatch videos: `filled-review-001/soil-motion.mp4`,
`strength-damage.mp4`, `plastic-shear-strain.mp4`; allMP/F/equalmetres/no
filter/interpolation. Kappa colour0..0.2 with visible saturation label,
actual values retained. Dphi0..1. Observe firstplastic and firstdamage
separately using full saved fields and explicit toe box, never paint onset.

New per-particle guard observer captures actualdF/F0/F/stretch/dt/id/position
before original `ERROR-DF-NEGATIVE` propagates. NO retry/clamp/tolerance change.
Old failedincrement remains missing; synthetic control is never its replay.

## New verification scope

Nativecontrol001 failed harness `no workers` before updates. Control002 then
passed577surface samples,actual15143MP/twoUSFupdates/positiveJ/IDs/lawfloor,
saved actual0/.0002s CSV/VTK, but its synthetic capture assertion failed because
the test subfolder was absent. All negatives retained. Capture-only003 after
IO-directory fix PASS atsyntheticdetDF=-1/id42,originalcondition propagates,
0MPMupdates; no repeat of successful two-update native stage. Actual002saved
geometry independently matches fullPython clip. Three-channel renderer-only
control PASS,2realstates each/encode+full decode; actualmotion/strainPNGs
inspected. NOT full terminalreview/mainrun/landslide validation. Studio check
and36Node tests PASS. No old longnative/gates/renders/replays repeated.

## Actual launch
30Oct10:30:13WIB/sourceef695faf,actual15143MP/frame0,NATIVE_RUNNING. Wallcap31Oct08:30:13WIB then<=2h savedmedia. Worker27036/wrapper14324/cmd19120/SBCL27868/media2660 Session4,oneidentityproof. Threefrozenhelperschannels autoexport atterminal, no duplicates. New15minquietmonitor active. No toeinitiation/maincompletion claim yet. Prelaunch7exactGitblobs/54ZIPmembers verified.

## Superseded by human: one constant angle
30Oct10:37WIB human requests ONE face. Two-angle initial-only native andwatcher explicitly stopped withexactcreation checks, no materialfailure inferred from wrapperexit-1. No dynamics/no export needed. Replacementuses originalsingle40deg geometry, samequarterclay/capture/threechannels/8starget. New577surface matches and14010nativeinitialchecksPASS0updates; no claimlateDFrepair. Olddataarchivedonce, monitor deleted.

### Actual single-angle replacement launch
RUN output/clay-single-slope40-2026-10-30/main-h05-001/source080d535a,30Oct10:40:41WIB. Actual14010MP/frame0,NATIVE_RUNNING; one40degface with no upper/loweranglekeys.22hwallcap31Oct08:40:41WIB plus<=2hmedia. Frozen4helpers/3movies/watchermedia30172,worker20576/wrapper39212 Session4, oneidentityproof. Newquiet15minmonitoractive. Initializationonly; no newslide/fullreviewPASS or lateDFfix claimed.
