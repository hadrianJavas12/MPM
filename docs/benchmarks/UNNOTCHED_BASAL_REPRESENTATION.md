# Basal interpolation diagnostic and finite next study

26 October 2026, `codex/unnotched-mc-composite-apex`. The completed6s
[composite trial](UNNOTCHED_MC_COMPOSITE_APEX.md) has transient plastic motion
that arrests. This diagnostic tests its numerical representation without
altering the material, fixed physical base or loading.

## Actual diagnostic result

Source4eeb2fe9 executes the first frozen native fixture once, exit0:
`output/mc-composite-apex-2026-10-26/basal-representation-001`. Six new groups
pass, with **zero constitutive calls and zero MPM updates**. Actual initial
particles are unchanged. Constant/affine reproduction on full support and
independent analytic floor-crossing limits pass for the native GIMP weights
and non-Fbar gradients. No old slope run, test or static search is repeated.

| Saved initial-grid diagnostic | h=1m | h=0.5m |
| --- | ---: | ---: |
| Actual particles | 880 | 3520 |
| Actual particles with positive basal-node weight | 124 (14.09%) | 252 (7.16%) |
| Highest actual centre with positive basal weight | 0.75m | 0.375m |
| Maximum partition / summed-gradient error | 0 / 0 | 0 / 0 |
| Prescribed-cap actual samples | 265 | 1056 |
| Sample RMS prescribed-field interpolation error | 0.227301m/s | 0.127857m/s |

The RMS quantities use different particle samplings. They are not a matched-
point convergence estimate, best approximation or measured velocity error in
the simulation. The test field is prescribed on nodes and never assigned to
native velocities. Its raw-minus-masked difference is zero because it already
vanishes at the fixed base; this cannot rule out smearing or constitutive
locking. Hypothetical probes can sample inactive grid nodes.

The retained formal circle minimum is y=0.0840671m. A hypothetical MP centred
there crosses the floor at **both** tested domain sizes; it is not an admissible
actual initial MP. Its raw partition values0.972466/0.993298 do not diagnose an
engine defect. Actual initial MP partitions remain complete. The old circle's
six negative normal forces still prohibit treating its formal factor as a
physical/global FoS. No new circle search or normal-force clamp is introduced.

The[native packet](../evidence/mc-composite-apex-2026-10-26/basal-representation-diagnostic/README.md)
is root verified:22 indexed artifacts/23 Git blobs, one ZIP/302 members,
290 archived and290 actual source/input/DLL files. The first collector makes
an incorrect invocation-schema assumption before packet creation; exact failed
collector/error are preserved. Corrected collection does not repeat the native
diagnostic. A separate[first saved-CSV summary](../evidence/mc-composite-apex-2026-10-26/basal-representation-summary/README.md)
exits0 with three input hashes matching before/after;7 indexed artifacts/8 Git
blobs verify. It runs only copied Python aggregation, no kernel or time steps.

## Decision before further time integration

No kernel defect is established to repair. Root and an independent reviewer
select **one same SRF1.6/composite-law h=0.5m,6s resolution study** for the
declared anchored-base problem. The measurable change in basal support region
gives a concrete resolution question. This does not resolve the hypothetical
0.084m arc or reproduce an unverified paper foundation.

The[new audit contract](../../research/references/unnotched-mc-ssr/composite-apex-srf1p6-h05-contract.json)
changes the grid to0.5m and expected count to3520; all material, physical BC,
geometry, gravity ramp/duration, damping, mass and solver assignments stay
fixed. Same CFL with smaller h changes stable dt and MP sampling, so this is
**coupled resolution sensitivity**, not isolated mesh convergence or confirmation
of a detected coarse slide.

The[comparison protocol](../../research/references/unnotched-mc-ssr/composite-apex-refinement-contract.json)
freezes the existing observer in physical metres for both grids, separate from
native h-scaled reports. Particle IDs do not correspond across meshes. Require
new focused input/output gates and provenance before launch;3h wall budget,
about2h6m planning estimate from the actual coarse work, not an ETA. At this
checkpoint the fine study is **NOT_RUN**. Its new case/focused gate and CSV-only
comparison wrapper are saved as source for continuation; static checks are not
native execution. Review those sources and run only new controls after reset.

**Finite stop rule:** after this pair, no automatic h0.25, SRF increase or time
extension. A negative pair requires resolving the physical foundation/base/
reference definition before another collapse-seeking experiment. Positive fine
motion would be a resolution-sensitive result requiring honest integrity and
spatial review, not validated paper failure or calibrated run-out.
