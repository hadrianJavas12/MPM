# Wang2017 accelerated trial: failed, incomplete

Frozen source52f9367; native exit1, started12:32 and ended13:30 WIB on2026-10-22. Gravity converged; the last saved loading state is15.4s, command77mm, measured76.518656mm out of target100mm. There are78 loading VTK states (frames0..77), plus gravity/mesh VTKs. Mass error at last saved state is0; that is not a full run audit.

Material integration rejected an update: no admissible coupled active-set solution after10evaluations. The trial principal stresses and old kappa are recorded verbatim in manifest/stderr; full failed-update state is not captured. The root cause and whether a slower rate avoids it remain unproven.

force-displacement.csv and energy-history.csv are absent after abnormal exit; no missing history was reconstructed and no consistency/energy/curve PASS is claimed. Raw remaining VTK/CSV, source snapshot except private compiled cache, logs and launch/status are retained. Next: isolate the constitutive failure and preserve histories on exceptions before another expensive full run.
