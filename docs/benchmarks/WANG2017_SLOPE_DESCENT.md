# Wang (2017) prescribed crest descent: Soil#1

This case studies prescribed descent of a 3 m crest patch using the existing MPM engine. It is a numerical comparison proposal based on Wang et al. (2017), [DOI](https://doi.org/10.1007/s11629-016-3951-1), Section 2, Table 1 and Figures 2–3. Source provenance is in [the reference record](../../research/references/wang2017/source.json). Current native benchmark evidence: **NOT_RUN**.

## Reference inputs and declared assumptions

| Quantity | Value | Basis |
| --- | --- | --- |
| Domain width; base thickness | 20 m; 5 m | Figure 2, printed p.179 |
| Crest before patch; patch | 7 m; 3 m, x = 7–10 m | Figure 2 |
| Slope angle | 60° | Figure 2 |
| Slope relief above base | **10 m assumption** | Height is not numerically specified in Figure 2 |
| Unit weight; Young's modulus | 20 kN/m³; 20 MPa | Soil#1, Table 1 |
| Poisson ratio; cohesion | 0.25; 30 kPa | Soil#1, Table 1 |
| Friction; dilation | 35°; 0° | Soil#1, Table 1 |
| Crest target descent speed | 0.0001 m/s | Section 2 and Figure 2 |
| Constitutive response | Elastic-perfectly plastic Mohr–Coulomb | Soil#1; no softening |

Mass density must be derived as rho = 20,000/g kg/m³ using the case's recorded gravity; unit weight is not density. Soil#2 in Table 1 softens cohesion from 30 to 15 kPa over paper kps = 0–0.02 at constant friction 35°. Soil#2 is deferred; its plastic invariant must be reconciled with native kappa before implementation.

## Procedure and comparison limits

1. Establish self-weight stress with gravity settling and assess residual motion/equilibrium.
2. Reset the displacement/time origin and velocities for the descent stage while preserving prestress and consistent constitutive internal state. The paper describes a strain reset; blindly clearing native stress-supporting elastic state is not equivalent.
3. Drive the crest patch downward; export target platen displacement/velocity separately from measured soil motion and reaction force. Penalty contact permits finite tracking error.
4. Compare the computed total vertical force per unit out-of-plane thickness against measured crest descent, with target descent retained as a separate diagnostic. Figure 3 supplies a graphical reference, not committed numeric observations.

The paper uses FEM local arc-length equilibrium tracking and compares it with modified Riks and implicit dynamics. This case uses explicit MPM with a penalty approximation to prescribed crest motion. It does not implement the paper's local arc-length algorithm. Boundary discretization, assumed relief, mesh, loading control and damping can change the curve; qualitative similarity does not establish quantitative reproduction or scientific validation.

Mass scaling is 1 and physical time is unchanged. At 1e-4 m/s, 0.1 m target descent requires **1,000 s of simulated physical time**, potentially millions of CFL-limited updates. A short pilot is operational evidence only; it cannot demonstrate the peak, post-peak path, or agreement with Figure 3. No complete-run flag, force curve or agreement percentage is inferred from setup or partial progress.

## Windows execution

Run from `D:\MPM` using the existing configured Windows toolchain and a new output directory for each command. The full case targets 0.1 m descent; the pilot is intentionally shorter.

```powershell
Set-Location D:\MPM
$pilotOutput = Join-Path 'D:\MPM\output' ('wang2017-pilot-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\benchmarks\wang2017-soil1-pilot.lisp $pilotOutput
if ($LASTEXITCODE -ne 0) { throw 'Pilot failed; retain and inspect its output.' }
```

```powershell
Set-Location D:\MPM
$fullOutput = Join-Path 'D:\MPM\output' ('wang2017-full-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\benchmarks\wang2017-soil1.lisp $fullOutput
if ($LASTEXITCODE -ne 0) { throw 'Run failed; retain and inspect its output.' }
```

Record actual process exit, completed updates, target and measured descent, simulation time, force history, finite state and mass diagnostics before upgrading **NOT_RUN**. A successful pilot and a full 0.1 m run are distinct evidence. A quantitative benchmark also needs a documented reference-curve extraction and declared geometry/control tolerances.
