# User-requested bounded CPU worker study,27October2026

Human asks whether the active40degree run can be accelerated. The laptop
reports AMD Ryzen9 6900HS,8physical cores/16logical processors. Full001 uses
one custom MPM worker, BLAS/OMP1, fullprocessor affinity and normalpriority.
Keep full001 healthy and untouched during this study; its frozen native bytes
remain3acf468f. No change to physical geometry/strength/damage law/timestep/
convergence requirements, no weakseed or driver, no GPU speed claim.

The engine already routes MPs/nodes through custom bpdotimes/omp. A source
review finds local MC/Eigen scratch, per-node P2G mutexes and serial owned
force/KE diagnostics, but no global parallel safety claim. Scheduler globals
are non-reentrant; dynamic caller bindings/handlers are not inherited by
custom workers. Object-pool main/worker0 sharing requires barriers. LAPACK
dependency safety needs actual tests. Summation order may differ.

Execute only a NEW bounded1vs4worker benchmark in separate fresh processes,
source/input/DLL frozen before execution. Full6714MP physical geometry is
unchanged. Per process:2warmup+8timed drained USF, actual atomic transfer,
then2warmup+8timed undrained USF; two timed4stepblocks perphase. Separate
startup/compilation/build/transfer/I/O from update timing and recordGC/CPU/
allocation. All accepted native material calls counted perID with no shared
concurrenthash increments. Benchmark ends with owned synthetic plastic
face/both-edge/currentJ scheduling equivalence, rollback and errorcapsule
propagation; this is not a slope failure experiment or oldsuite rerun.

Compare all saved MP IDs/mass/F9/J/globalV0/stress/elastic and plastic strain/
kappa/cohesion/Ds/plasticvolume/work plus RF/KE using existing state
absolute+relative1e-11, time1e-10 and actual frozen native stress tolerances.
No relaxation to pass parallel data. Synthetic failure must run LAST or the
pool must be rebuilt: current omp leaves nesting set when rethrowing errors.
Retain all failures and timings. Two short processes run sequentially while
the existing serial job continues; that backgroundCPU and thermal effects
limit extrapolation to an isolated fullrun. No linear4x promise.

Production configuration and runner currently require1worker. Any future4
worker case needs explicit reviewed computational variant and relevant gates;
do not hotpatch the current process. There is NO complete native restart:
save-sim/load-sim are stubs and VTK/CSV are not restart checkpoints. Switching
requires a freshinitial-state attempt, preserving full001 as superseded rather
than falsely labeling it material failure. Decide only after measured speed,
parity and nettime benefit; no interruption of healthyfull001 yet.
