# Independent static diagnostic for the unnotched adaptation

25 October 2026. This is a dry simplified-Bishop diagnostic, separate from the
native MPM solver. It does not change soil parameters, constitutive code or
the saved simulations. See the [primary audit](../../research/notes/unnotched-landslide-2026-10-24/static-reference-audit.md)
for the official USACE equations and their limitations.

## Reproduce

From `D:\MPM`, using a fresh output directory:

```powershell
.\toolchain\analysis-venv\Scripts\python.exe -m unittest discover -s tests/analysis -p test_slope_stability.py -v
.\toolchain\analysis-venv\Scripts\python.exe scripts/check-slope-static.py --contract research/references/unnotched-mc-ssr/statics-contract.json --output output/unnotched-statics-2026-10-25/search-FRESH
```

The command copies its source, mathematical backend and preregistered contract
before the search, then executes the copied backend. It saves every candidate
factor or rejection reason, search-boundary flags and raw negative base-normal
counts/stresses. Existing results must not be overwritten or repeated merely
to check status. The five independent controls passed once: zero-friction
continuous circle-moment reference, strength-reduction identity, unit/length
similarity, geometry/driving sign/rejections and a valid vertical endpoint.
The controls execute no MPM updates.

## Actual results

The unchanged D1-inspired polygon has height10m, crest12m and face projection20m,
with gamma20kN/m3, c10kPa, phi20degrees. Both strengths use the same restricted
circle family. Search/slice choices were frozen before numerical results.

| Search | Slices | Formal minimum SRF1 | Formal minimum SRF1.4 |
| --- | ---: | ---: | ---: |
| Coarse family | 200 | 1.400293719 | 1.000209799 |
| Same coarse family | 400 | 1.400314189 | 1.000224421 |
| Fine family | 400 | 1.383870236 | 0.988478740 |

All36,006 candidate outcomes are retained. The fine minimum is interior to
the declared family: entryx9.75m, exitx31.390625m, rho0.793700526. Its arc
minimum is only0.0840671m above the fixed base. Slice refinement is small, but
family refinement changes the minimum: no global optimum is certified.

The fine minimum includes six negative slice normals (minimum approximately
-7.171kPa). These are reported without clamping or a tension-crack assumption.
Formal Bishop equilibrium is not a physical-admissibility PASS. The source
figure/foundation correspondence remains incomplete, and the native engine
uses nonassociated finite-strain MC rather than a circular equilibrium model.

The diagnostic suggests a near-critical reduced-strength problem while coarse
MPM settles. That motivates a resolution/locking study; it does not establish
that the MPM must collapse or validate either method. The fine static arc is
near the base relative to both proposed mesh sizes, so basal resolution remains
a particular limitation. Calibrated runout or a converged FoS is not claimed.

## Evidence and next experiment

[The static packet](../evidence/unnotched-gravity-2026-10-25/static-diagnostic/README.md)
retains19 indexed artifacts/20 independently verified staged Git blobs,
including exact controls, source snapshots, contract, full candidate CSV and
all six summaries. Both completed native cases and their negative motion
results remain unchanged.

The [refinement contract](../../research/references/unnotched-mc-ssr/refinement-contract.json)
predeclares mesh1m to0.5m, with the same strength, geometry, gravity schedule,
PPC, dtScale, duration and output cadence. This changes spatial and actual time
resolution together. A common physical-metre observer is frozen for both
meshes; original h-scaled diagnostics stay separate. New native grid/count/
mass/boundary and bounded-update gates must pass before the full refined run.
