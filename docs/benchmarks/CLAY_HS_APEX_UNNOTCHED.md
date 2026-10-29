# Cohesionless clay HS with explicit volumetric apex flow

29 October 2026. Human authorizes continued work toward an actual unnotched
slide. Branch `codex/clay-hs-apex-unnotched`; prior failures remain immutable.

The new OPTIONAL material adds g_A=p, grad(g_A)=I/3 at the zero-stress apex.
Regular shear remains the original strict evolving MC, psi=0. This changes
tensile/apex constitutive response explicitly; it is not a root/tolerance
repair, stress clipping, fracture or exact Urmi/Wang reproduction.

Scope is restricted: HS, Cauchy, c=0 at every coordinate, psi=0, positive phi
throughout. The apex is always zero regardless of evolving phi. Existing
perfect-apex analytic flow, compliance/energy/work checks and stable
principal-difference algebra are reused. Kappa accumulates the SAME J2
increment, then phi is evaluated at updated kappa. Zero returned stress
satisfies all six evolved planes; apex plastic work is zero. Existing elastic
screen preserved. Analytic branch only above stressTolerance/(2 sin(min phi))
in positive mean trial stress; the rest delegates unchanged strict HS,
including rejection. No exception fallback/tolerance/history/strength tweak.

Inputs retained: E20MPa, nu.2, rho2000, c0, regular psi0, peak phi33.99deg,
residual tan(phi)/tan(peak)=.25 (phi9.568041272839212deg), D_phi<=.75.
40deg/H10/crest24/base8/domain72x24, h.5/PPC2x2/14010MP, one worker,
volume-cpGIMP/mass1/CFL.2, gravity ramp2s, local damping.75 then.02.
Target20native seconds/41states;22h wall budget plus at most2h saved media.
No notch, crest actuator, reset, initial preload or undrained material switch.
This c0 slope may move during gravity application; no geostatic equilibrium
claim. Stable initialization cannot be assumed for40deg>peakphi. Test gravity
first; any later load-triggered adaptation must be declared separately.

New gates:28accepted pure returns including actual captured failed trial,
permutations/scales/knot crossings/residual states and exact strict delegation;
two unsupported laws rejected. Six actual native tensor constitutive calls,
evolved phi/plastic volume and loadstep commits PASS. These are not full MPM
or scientific validation. First native-control invocation had test-reader EOF
before material calls; retained log, corrected invocation002 passes.
Studio check and36Node tests PASS.

Fresh run `output/clay-hs-apex-2026-10-29/apex-h05-001`, NOT VTK continuation.
Automatic terminal saved-only observer uses prelaunch frozen helpers and
produces `filled-review-001/soil-motion.mp4` and `strength-damage.mp4`.
All actual material patches/F/equal metres, no filtering/interpolation.
Inspect both summary PNGs/review JSON before claiming coherent motion.
Completion/colour alone is insufficient. Repair media from saved data only.

Actual launch29Oct16:03:11WIB, source8c62e3b6; frame0/14010MP saved, native running. Worker33708/wrapper35116/cmd33564/SBCL5520 Session3, mediawatcher33448. ONE identity proof recorded. Finite monitor pantau-longsor-clay-tanpa-notch ACTIVE15min; no initial-state landslide claim.
