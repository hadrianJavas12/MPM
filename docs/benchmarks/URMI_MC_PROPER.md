# Urmi-inspired MC: h1/PPC2 measured-preparation trial

Human authorized the main run:40deg, extended left12m, foundation8m, mesh1m,
2x2 MPs/cell (3503 actual MPs), two filled-colour videos, less than24h wall.
Branch `codex/urmi-proper-mesh1`. Native budget22h, media reserve2h; a time cap
is not a promise that equilibrium and20 dynamic seconds will complete.

The soil law/strengths, E/nu, phi/psi, mass1, CFL.2, FLIP/USF, geometry and
atomic material transfer remain explicit. Local strain softening is mesh
sensitive; beta105 originated at h.5. This is not mesh convergence or calibrated
physical validation.20 dynamic seconds/101 actual states at.2s are requested.

Preparation uses native Cundall local damping.75, measured RF<1e-4/RK<1e-8
for50checks and1s, followed by100undamped checks and1s, all passing. No switch
if this fails. Caps60000updates/60native seconds. Dynamics local damping.02.
These local damping values and drained-to-undrained trigger follow Urmi et al.
2024 (doi10.1016/j.enggeo.2024.107669), but the numerical adaptation is explicit.
No field/history/F reset, notch, displacement driver or extra strength change.

Prior demo failed signed particle-domain Y while J and physical volume were
positive. This profile explicitly selects volume-based cpGIMP domains
l_i=l_i0*sqrt(detF), with strict positive-J/domain checks. Existing implementation
`update-domain-det` is used; original default polar update is unchanged. This
volume-based alternative is described in Wyser et al.2020, section2.2,
https://gmd.copernicus.org/articles/13/6265/2020/ . It is a numerical integration
domain choice, not a clamp, absolute-value repair or a physical deformation reset.
The opt-in flag is process-global so native worker threads receive the mode.
Serial diagnostic BC masks union the actual overlapping prescribed constraints.

NEW Windows SBCL controls002:6groups PASS,3503MP,24drained+24undrained USF
updates, worker domain=initialDomain*sqrt(J) asserted. Controls001 used a dynamic
binding invisible to workers; its coupled part did NOT prove the new mode,
although its direct mathematical domain probes passed. Retained, superseded by002.
Profile controls002:4groups PASS,0MPM: exact case compile, Cundall force,
default-hook delegation, actual initial CSV/VTK.001 failed a test-helper arity
before that check; source/error retained. No native production attempt yet here.
Studio check+36tests PASS. No prior material/transfer/oldrun gates repeated.

Filled rendering convects each original .5m square by actual physical F, checks
quad area=J*V0 and shows all patches, equal metres/common bounds, no scatter,
no state interpolation or outlier removal. Overlaps/gaps are retained, not a
fracture surface. Motion colours original depth; damage shows Ds=1-c/40500
on fixed0..1 scale. Initial-only renderer002 actually encoded/decoded both
movies;001 retained an environment import failure after producing PNGs. Full
terminal saved observer remains NOT EXECUTED before production completion.

Detached pipeline will invoke the frozen saved observer after native exit,
including honest partial output on failure/wallcap; no solver restart. Output
folder `output/urmi-proper-2026-10-28/main-001/filled-review-001/` will hold
`soil-motion.mp4` and `strength-damage.mp4`. WMI avoids caller parentage but
is not proven immune to sleep/logoff/reboot. Keep the machine awake.
