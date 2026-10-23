# Windows native Soil2 integration control evidence

Date: 24 October 2026, Asia/Jakarta. This packet preserves the failed harness
attempts as well as the completed integration controls. Packaging executes no
solver or numerical tests and leaves the original output intact.

| Attempt | Actual result | Evidence and interpretation |
| --- | --- | --- |
| `native-controls-001` | Process exit1; zero controls executed | Test bootstrap loaded its helper inside the form that compiled the context binding. The context was lexical, the native proof encountered NIL, and execution stopped before controls. Copied source files/manifest and raw log remain; no verified frozen execution or PASS is claimed. |
| `native-controls-002` |18 material groups PASS,0 FAIL,0 NOT_RUN; overall process exit1 | Frozen execution and before proof succeeded. After controls completed, the harness attempted to write the fresh-only `source-provenance.json` twice and failed. Result/before proof/raw failure log remain. No successful overall process exit is claimed. |
| `native-controls-003` | Windows native process exit0;18 PASS,0 FAIL,0 NOT_RUN;28 constitutive calls; zero MPM updates | Corrected harness preserves separate before/after provenance. All271 selected frozen source bytes match the before/after SHA256 records and retained files. Actual copied `kirchoff.dll` mapping verified using `GetModuleHandleW/GetModuleFileNameW`. |
| `integration-controls-001` | Three actual Windows native commands exit0:34 existing MC controls,10 framework contracts and3 Soil2 input controls | Raw logs, status/input JSON and the three executed-test source copies are retained. This root suite did **not** use the full first-party source freeze; the271-file frozen-source claim applies only to `native-controls-003`. |

## Scope of the18 native Soil2 groups

The completed adapter checks cover fixed material inputs and owned state,
elastic/analytical plastic return and residual tail, tensor history versus summed
increment history, stress/engineering shear factors, Cauchy/Kirchhoff scaling,
proper polar recovery, nonzero-history rigid rotation, time-varying observer
covariance, noncommuting elastic-rotation refinement, repeated trials, apex and
history-decrease rejection, and snapshot/copy/reinitialize/loadstep transactions.
Committed tensor and embedded baseline arrays are deliberately mutated to test
independent ownership. The outer stress transaction is exercised by production
`:around` dispatch with a test-only primary method that mutates fields then
fails. It is **not** an actual mesh/grid or solver step.

The declared model is an experimental signed-tensor Soil2 accumulator with
incremental polar corotation and a monotonic loading scope gate. There is no
hidden maximum-history or apex adjustment. These controls do not establish a
landslide, paper/FEM curve agreement, irreversible behavior for arbitrary paths,
mesh objectivity, or experimental validation.

## Archive contents and verification

Each attempt has its own ZIP. Retained contents include all available copied
sources and manifests, native DLL, before/after source and runtime proofs,
result/status JSON and raw logs. `native.log` inside each native ZIP is the
unaltered adjacent launcher log. Source snapshots in failed attempts are retained
as historical evidence, not represented as a completed execution proof.

Private `.native-cache` files and any `.fasl` files are excluded to keep the
packet practical. Their original raw folders remain on disk; exclusion paths and
sizes are enumerated per archive. Available runtime provenance still records its
ASDF/FASL references, but these omitted compiled binaries cannot be recovered
from this packet. Third-party dependencies remain external and are outside the
first-party frozen-source claim.

`archive-member-manifests/*.json` records every included member's byte length and
SHA256. The collector decodes every member and verifies both, checks ZIP CRCs,
and checks the complete name inventory. `archive-verification.json` records the
result and confirms inputs were unchanged during packaging. `evidence-manifest.json`
and `SHA256SUMS` index all packet artifacts except those two self-referential
index files. Exact packaging source is under `analysis-support/`.
