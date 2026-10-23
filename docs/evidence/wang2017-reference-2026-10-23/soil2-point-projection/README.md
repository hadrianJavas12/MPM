# Wang2017 Soil2 fixed-frame point projection evidence

Archived 2026-10-23, Asia/Jakarta. Original native output:
`output/wang2017-reference-2026-10-23/soil2-point-001/`.

- `attempt-001/`: initial Windows SBCL result, 16/16 controls PASS, exit 0.
- `attempt-002/`: final Windows SBCL result, 19/19 controls PASS, exit 0.
- `asdf-smoke.*`: optional `cl-mpm/models/wang2017-point` ASDF load and one
  elastic pure point call, exit 0. This separate smoke used workspace ASDF
  loading; copied ASDF/source identities were checked afterward.
- `validation.json`: final scope and unchanged-existing-implementation check.
- `packaging-verification.json`: every copied file was verified byte-for-byte
  against the retained output; both pre-load source manifests and the final
  after-load source proof were checked against their archived source copies.
- `SHA256SUMS.txt`: SHA-256 of every artifact in this directory except the
  manifest itself. `.gitattributes` disables text/line-ending conversion.

Each attempt retains eight explicitly loaded module source files, the executed
control script, and the ASDF definition for review. Native logs identify every
explicit loaded module path. The ASDF file was not loaded by those frozen
point-control attempts. Initial attempt has a pre-load proof; final attempt has
both before-load and after-load proofs. Packaging additionally verified all
20 source-manifest records. Third-party Quicklisp/yason/CFFI/bootstrap remain
external dependencies; this archive does not claim to snapshot that environment.

The final controls cover the independent analytic pure-shear equation, both
2-plane MC edges, Cauchy/Kirchhoff J scaling, monotonic and nonproportional
history, reversal including return from the residual branch, rotated frames,
all six principal permutations, input/result ownership, rollback, captured
zero-dilation tensile-apex rejection, stable/linear/repeated quadratic roots,
actual three-admissible-root ambiguity rejection, and conservative handling of
history-identity branches. The checked unsquared history residual is 1e-13.

This is an isolated **small-strain, fixed-frame material-point prototype** with
paper constants phi35/psi0 and Cauchy cohesion30->15kPa over literal paper
kps0->.02. The main controls use E20MPa/nu.25. An explicitly synthetic low-E
fixture tests multiple-root rejection; it does not change paper case inputs.

Literal signed-tensor Eq5-6 norm can decrease under reversal and cohesion can
therefore increase. No irreversible maximum/healing convention is approved or
silently inserted. There is no particle adapter, finite-strain tensor transport,
MPM timestep, slope simulation, completed force curve, or scientific validation
in these controls. No old MC numerical function/default system was modified.
The actual captured infeasible tensile-apex trial still rejects without a clamp.
No native tests were repeated during evidence packaging.
