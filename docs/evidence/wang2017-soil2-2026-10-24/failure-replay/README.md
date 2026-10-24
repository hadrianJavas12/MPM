# Actual Soil2 failure replay evidence

The first full Soil2 slope run `fast-010-001` failed natively with exit1 on source
`621146b`. Its exact failure capsule is retained here unchanged. The last saved
loading state was5.7s/57mm, which is not the exact rejected-substep time.

| Diagnostic attempt | Actual result | Meaning |
| --- | --- | --- |
| `failure-replay-001` | Native exit1; zero actual capsule-replay calls; zero physical updates | A diagnostic helper named BOOLEAN collided with the inherited COMMON-LISP symbol/package lock. The harness failed before replay. Raw log, failure record, exact driver/source and before-runtime proof remain intact. |
| `failure-replay-002` | Native exit0; exactly one actual capsule-replay call; zero physical updates | Renamed diagnostic helper only. The expected rejection was reproduced using the actual failed input. This is a successful diagnostic replay, **not** a successful slope simulation or scientific PASS. |

All271 source files/DLL from the actual failed run match its pre-load manifest.
Each diagnostic archive retains those exact271 files plus its own new driver,
for272 hashed source files per attempt. Current
`tests/benchmarks/wang2017-soil2-failure-replay.lisp` is byte-identical to the
executed002 driver. No EOF trimming or source changes were performed by packaging.
The002 actual mapped copied DLL and its hash match the before/after Windows API
proof. Third-party dependencies remain external to the first-party source claim.

The exact original capsule SHA256 is
`05835d5429292da0b95190232c0d3fb4d6228d6fd08d975ee1346434ba99242d`.
`diagnosis.md` and `candidate-admissibility.json` are readable copies of the
existing002 diagnosis and candidate tables. They explain why the captured
coupled cohesion-softening/zero-dilation return has no admissible solution. The
expected rejection is neither a monotonic-history violation nor an ambiguity
silently resolved by choosing a root. No material parameter, production equation,
tolerance, apex convention or solver trajectory was altered to obtain this result.
It does not prove every smaller-step trajectory or the paper FEM must fail.

The two ZIPs preserve all available diagnostic raw logs, execution/failure/result
records, candidate tables, source manifests/copied sources, capsule and runtime
proofs. Private `.native-cache` and `.fasl` files are excluded and listed by path
and size in each member manifest; their original raw directories remain intact.
Their references in runtime provenance do not mean omitted compiled files are
included. This packet does not archive the full failed run's VTK/CSV/media; that
evidence is collected separately. Packaging reads no raw VTK or process/PID state.

Every archived member is decoded and checked for byte length/SHA256, complete
name inventory and ZIP CRC. All original input bytes were checked unchanged.
`archive-member-manifests/`, `archive-verification.json`,
`source-integrity-verification.json`, `evidence-manifest.json` and `SHA256SUMS`
retain these checks. The final two self-referential index files are excluded
from their own artifact list. Exact collector source is under `analysis-support/`.
No replay, numerical test or solver was executed during packaging.
