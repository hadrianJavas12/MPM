# Incomplete post-start capture

The capture began after the native process had already exited1. Verification
correctly rejected missing live PID50220; no live-process proof was produced.
The capture script then retained two existing status/launch JSON files before
stopping on the missing live-verification input. This directory is an incomplete
capture attempt, not proof of running/complete/valid physics. Do not relabel it
PASS, remove it, or infer missing source/runtime evidence from it.

Authoritative terminal status and originals remain at
`output/unnotched-gravity-2026-10-24/srf1p4-001*`. The full saved-data review is
in the native run's `review-001/`, with explicit incomplete scope. A dedicated
failed-result archive will retain the actual sources, capsule, raw outputs,
native/runtime/worker exit and analysis/media. No solver restart occurred.
