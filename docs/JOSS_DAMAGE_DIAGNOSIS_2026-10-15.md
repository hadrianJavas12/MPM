# Joss damage diagnosis and physical result — 2026-10-15

The actual native Drucker–Prager (DP) pilot develops lower-face damage, collapse
and run-out. **The user accepted this as the requested visual collapse result**
after viewing its video and the later 40 kPa final image. The user said they were
satisfied and requested a commit recording successful collapse; no further
calibration is requested. The measured
reference comparison still shows excessive retreat/run-out, so this acceptance
does not establish a numerical match or scientific validation.

Evidence below is relative to `output/reference-reproduction-2026-10-15/`.
The active checkout is `D:\MPM`, branch
`feat/studio-custom-constitutive-lisp-export`, based on `f70e410` before the
authorized acceptance commit. Ordinary Studio/chalk defaults were not changed by the
reference-specific criterion, aggregation and protected-foundation adaptation.
The selected media, configs, metadata, CSVs, audits, replay sources and actual
validation logs are preserved in
[the commit evidence bundle](evidence/joss-collapse-2026-10-15/README.md).

## What the diagnosis established

The exact recovered legacy native DR adapter was run for **one trial update**.
`legacy-probe/trial-1/initial.json` and `after-trials.json` show that native
simulation time remains 0, solver dt becomes 1, committed positions stay fixed
and trial positions change. The old timeline assigned its own clock without
native physical finalization. Replaying that timeline cannot establish a physical
collapse trajectory. The recovered runner's identity with the WhatsApp damage
clip remains unproved; the clip really does show damage, as recorded in
[the history correction](ANTIGRAVITY_NATIVE_HISTORY.md).

The independent aggregate equilibrium preparation converged in **1,658 updates**:
energy ratio `5.06817e-9`, projected OOBF `9.96668e-5`, 4,155 particles and mass
`425664.0625 kg/m`. A frozen-state comparison used the same full six-component
undamaged stresses and native nonlocal quadrature for both criteria:

| Nonlocal driving stress | Lower region, y ≤ 4 m | Upper region, y ≥ 9 m |
| --- | ---: | ---: |
| Author Joss DP | 50.409 kPa | 33.937 kPa |
| Previous reference MC | 16.076 kPa | 20.232 kPa |

The correctly converted initiation threshold is **18.926 kPa**. The MC lower
maximum is below it, explaining why that criterion does not initiate the desired
lower-face damage in this prepared state. The legacy angle/helper convention
instead yielded 51.214 kPa and the recovered runner used a 62 s delay; those
settings are not silently imported. The frozen-state probe integrates no damage
and proves no collapse. See `criterion-probe/summary.json`.

The dedicated production reference material now uses the author Joss DP driving
criterion with stored **radian** friction. Material index 1 identifies the elastic
base/beach, whose damage and plasticity stay disabled. Initial relaxation also
disables both mechanisms in the cliff; only the converged cliff is subsequently
enabled. Aggregate statistics use independent constrained force/energy degrees
of freedom; they are an author-code adaptation, not a literal Eq.(67) claim.

## Accepted actual physical pilot and its limit

`dp-physical-pilot/` starts from the strict prepared state and advances the
physical solver clock, without assigning a failure timeline. It uses h=0.5 m,
two MPs per axis, Gf=4.8 J/m², initiation 18.926 kPa, derived ductility 53.599755,
delay 10 s, and 496 protected base particles.

- The first saved damaged frame is at **t=4 s**, maximum damage **0.333589** at
  approximately `(13.125, 3.625) m`; upper-region damage remains 0.
- A native pause at t=4.3552376 s has maximum damage 0.386528, all 496 base
  particles at zero damage and finite fields (`pause-1-audit.json`).
- The completed bounded pilot reaches **40 s / 174 frames**, retains 4,155 MPs
  and the same total mass, and has finite audited fields. Final mass-weighted
  damage is **0.493673** (`damage-location-audit.json`).
- Its comparison against the main video's final **221.14 s** image gives
  occupancy IoU **0.699825**, right edge **+7.8 m**, and remaining plateau edge
  **−5.2 m** relative to that reference (`final-shape-comparison.json`). This
  deliberately compares outcome shapes at different times; it is not a timing
  match, a percentage of physical accuracy, or proof of validation.

See `damage-t4.png`, `damage-t40.png`, `timesteps.csv`, `transitions.csv` and
`reference-metadata.json`. Metadata `complete=true` means only that this pilot's
40 s target was reached; scientific validation remains `unverified`. Native
gnuplot was disabled for this pilot (`plottedFrames=0`); the saved damage PNGs
were rendered separately from actual particle VTK.

The accepted deliverables are
[the native DP collapse video](evidence/joss-collapse-2026-10-15/accepted-collapse.mp4)
and [its t=40 s damage image](evidence/joss-collapse-2026-10-15/accepted-collapse-t40.png).
This pilot started from a saved strict equilibrium state; its historical warm
start and continuation sources are preserved as provenance. It used the isolated
`joss-probe-dp-chalk` subclass, while production now uses its dedicated reference
class; identical production replay is unproved. A fresh production
replay must be identified separately from this captured pilot, rather than
claiming an identical warm-start replay from the generic CLI alone.

## Completed integration checks

`validation/validation-summary.json` records actual `npm run check`, **36/36 Node
tests with no skips**, including three real Windows SBCL contract tests, and one
bounded native reference smoke. That smoke converged in 179 preparation steps,
has 1,092 MPs/124 protected base MPs, four finite VTKs, two nonempty PNGs, and
zero base damage. Its frame cap stops at 0.02 s of a requested 0.03 s; it is not
a fracture result. The one-step failed-equilibrium guard also passed. These are
integration/field-integrity checks, separate from scientific or shape validation.

## Completed 40 kPa calibration and stopping point

The later candidate in `strength-40k-run/` **completed normally at 221.14 s /
111 frames**, with `complete=true` and final phase `accelerate`. Its old running
PID 29416/pending status is superseded. The production CLI launch is recorded in
`strength-40k-provenance.json`; config and log are
`strength-40k-config.json` and `strength-40k-run.log`.

The damage initiation is **40 kPa**, between the measured upper/lower DP maxima.
Consistent damage cohesion is **54,949.548389 Pa** and ductility **12**, with
Gf=4.8 J/m², delay=10 s, h=0.5 m, two MPs per axis and four workers retained.
The raw config requested 5,000 frames; canonical schema normalization reduced
the effective cap to **2,000**, as the actual log's `Step 111/2000` confirms.
The target duration was reached before that cap. This is an explicit
**unverified calibration**, not the literal paper parameter set or a parameter
sweep. Its final maximum damage is **0.49062952033** and mass-weighted damage
**0.008064637675**. The final image shows localized damage without collapse:
[40 kPa result at t=221.14 s](evidence/joss-collapse-2026-10-15/latest-40k-t221.png).
Do not attribute the accepted pilot's collapse to this later run.

The user is satisfied with the actual DP pilot's collapse and requested the
local commit. Heartbeat `mpm-lanjut-setelah-reset` is confirmed **PAUSED**; no
further simulations, calibration or UI work are requested. The commit description
should say that actual collapse/run-out succeeded and was visually accepted,
while retaining the reference mismatch and unverified scientific status.
No push, merge or PR change is requested.
