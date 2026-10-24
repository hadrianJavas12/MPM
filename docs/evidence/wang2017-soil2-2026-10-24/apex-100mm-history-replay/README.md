# Actual100mm-run composite-apex history rejection

One Windows-native actual NEW capsule replay, exit0: exactly1 replay call,
1 variant dispatch and0 MPM updates. Source3caa6bea5d447be34c8bd1104311f1aa34b57986.
No old actual capsule or previous test suite was rerun. The test-only around
method captures the pure result during that same production replay call.

[Diagnosis and next scope gate](diagnosis.md), [exact result](replay-result.json)
and [all-candidate report](candidate-admissibility.json) distinguish admissible
point return from the later native monotonic-history guard rejection. There is
one hydrostatic-apex root and0 admissible regular roots. Old/new kps exceed0.02
and decrease by1.169825285252113e−9; old/new cohesion/friction/dilation values are
EXACTLY unchanged [15000Pa,35deg,0deg]. This transition does not heal strength.
Plastic work+0.004953389208998423Pa, volume+2.2883033921443711e−7 and independent
J2 increment+3.5276291130274547e−7 remain positive; history residual0 and maximum
MC residual3.63798e−12Pa. These are local constitutive checks, not slope validity.

275 failed-run frozen sources plus1 new driver are in executed-sources.zip,
along with their full276-record replay source manifest (277ZIP members).
Every decoded member was verified byte-for-byte against retained raw output;
member hashes are in archive-member-verification.json. The original failed-run
preload manifest is separate. Runtime proof before/after verifies exact loaded
copied sources and actual copied DLL via GetModuleHandleW/GetModuleFileNameW,
SHA25657c4c9a6cedb1ade1202914074dab942afc2f15abb114637619ca3cb5d9f074f.
Compiler caches are retained only in raw output, not bundled as source files.

The source verification refers to the immutable failed-run/replay copies, NOT
the workspace after parent begins a separately authorized residual-scope change.
Production was not changed by this replay. Full-particle/full-MPM rollback is
NOT_EXECUTED: the capsule lacks complete particle state and exact rejected-step
time/ID. Static commit ordering and prior synthetic rollback controls remain
separate evidence. Last SAVED9s/90mm is not the exact failure coordinate.

Raw output remains at output/wang2017-soil2-2026-10-24/apex-history-failure-replay-001.
The focused diagnostic source is tests/benchmarks/wang2017-apex-history-failure-replay.lisp.
No tolerance, max-history, cohesion, dilation, rate or solver update was changed.

Post-collection packaging note: packet attributes now disable text newline
normalization for every member, preserving the recorded byte hashes in Git and
on clone. Only this note, .gitattributes and their manifest entries were changed;
raw output, source archives and executed collector/driver bytes are unchanged.
