# First native boundary-mask diagnostic,27October2026

This is a new bounded investigation after full001 failed its declared20s
drained preparation cap. Native/worker exit1 is not constitutive failure.
The last retained manifest says RF0.00013149719037753823 and RK9.1103e-12;
there is no invented last nodal state. Do not change1e-4 RF or any physical
input, restart the slope, or repeat the completed worker benchmark.

Freeze this plan, the executed diagnostic, original full001 manifest/source
manifest, and all selected runtime/source/DLL bytes before execution.

The first diagnostic constructs the exact unchanged6714MP recipe and its
actual mesh/BC vector. It performs ONE initial P2G mass mapping, with no
force/stress/constitutive update or time advance. This is an initial mass
fixture, not the final full001 state. Native MPM/material counters must stay0.

Independently derive the union of constrained directions from every actual
fixed BC on each node. Compare that union with cached node-bcs masks and
physical constrained velocities. Apply the two actual bottom-corner BCs in
both serial orders to test mask first-writer behaviour; test whether native
reset-node retains that mask. These are prescribed initial-node fixtures.

Use exactly16 cold-mask scheduler passes at1worker and exactly16 at4workers,
always the actual BC vector and unchanged boundary methods. Record every
cached/union mismatch, its initial mapped mass, and all physical constraint
violations. Do not repeat until a desired interleaving appears. Correct
physical velocities and incorrect cached diagnostic masks are distinct.

Finally use one actual corner node and one interior node with explicit
synthetic raw pre-essential forces/velocities to quantify RF, free nodal
mass and RK under cached versus union masks. This tests classification only;
these are NOT recorded forces or velocities from the failed simulation.

The scheduler waits for all parts before returning; counters/hash tables are
aggregated serially. No production source is patched. Source review and this
test can establish a boundary-mask defect but cannot prove that it caused
serial20s equilibrium failure without the absent final nodal records.
