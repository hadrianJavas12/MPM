# User-authorized rough visual demonstration,27October2026

The human explicitly prioritizes seeing whether the simulation can slide in
1–2 wall hours and does not require accuracy. This supersedes the old mission's
strict equilibrium/refinement prerequisites for this SEPARATE demonstration.
Branch: codex/urmi-mc-damage40-rapid. The failed full001 remains untouched.

Use the same40-degree/no-notch slope, H10m/crest12m,4m active soil foundation,
60x20m domain and Urmi-inspired MC strength-degradation law. No driver, weak
seed, extra strength reduction, field reset or constitutive tolerance change.
Keep native positivity/finiteness/material rejection: an error is not a slide.

Deliberate approximations: mesh2m/PPC1 gives105MP (60foundation/45upper),
sampled area420m2 versus previous419.625m2. Same density, E/nu, c/phi/psi,
beta/table, mass1 and timeStepScale.2. Preparation damping uses the same
alpha.4 with the new mesh, about15.76646/s. Fixed3native seconds preparation
(2s smooth gravity ramp +1s damped relaxation), NO equilibrium acceptance
claim, followed by damping0 and the real atomic drained-to-undrained material
switch. Preserve F, history, velocities, geometry and native clock; no resets.

Request20dynamic seconds,41actual frames at.5s cadence, cap20000dynamic
updates. Wall cap1.5h leaves time for a saved-data video within the requested
1–2h window. Initial dt estimates .00417s drained/.00250s undrained; roughly
8000dynamic updates. A rough all-plastic point-cost extrapolation is about
46min, not a runtime or collapse promise. If wallcap/material failure occurs,
show only actual saved states and report the stop honestly.

Use one worker: prior parallel saved parity failed and is unnecessary here.
All particle data, force/KE diagnostics and native source/DLL bytes retained.
Fresh output streams close without abort deletion. Do not silently modify the
old strict configuration or transfer's material/transaction checks.

Visual result: all105particles, actual metre coordinates at equal scale,
strength loss D_s=1-c/40500 shown on fixed0–1 colour scale, no interpolation
or removed outliers. New rough observer graph radius2.02m reflects2m initial
particle spacing; this is declared before the result. Report actual coherent
motion/KE/displacement/runout, but do not call the coarse result calibrated,
converged, fracture/crack opening, a literal Urmi reproduction or proof that
the corresponding physical slope must fail. A negative result applies only
to this coarse approximate experiment.

Run the new optional case directly after source review/checkpoint. Do not
delay it with old gate reruns, research, static searches or refinement studies.
Automatic source snapshot precedes native project loading. Freeze the new
observer bytes before saved-data execution; if authored after launch, say so.
