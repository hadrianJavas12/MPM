# Explicit residual history controls

Thirteen distinct groups passed across **two separate Windows SBCL processes**.
This is not one 13-PASS process. Attempt001 exited1 with12 groups passing and
one constructor assertion failing because the test expected friction in degrees;
`law-values` correctly returns radians. Its failure, executed test and raw log
are retained unchanged. The corrected constructor-only attempt002 exited0 with
one group passing and all12 previously passed groups skipped. No passed group
was rerun for this repair.

Actual aggregate work: **one new-model point call and nine new-class native
constitutive calls**, zero original-variant capsule replays and zero MPM updates.
The old composite-apex capsule was not replayed. Its captured numerical inputs
were used only as explicit controls of `composite-apex-residual`.

The new native control retains the literal smaller signed tensor norm:
old kps0.03187108863369348, new kps0.03187108746386819, cohesion exactly15000Pa,
positive plastic volume2.2883033921470997e-7 and positive work
0.004902053892468305Pa. Full compliance, exact residual strength, signed tensor
closure, independent J2, 3D observer covariance and repeated uncommitted trials
pass. A separate regular residual reversal retains kps0.029 from0.030 rather
than an irreversible maximum. Softening/boundary recovery rejects; original
strict, original apex and unknown synthetic policy guards retain1e-13 behavior.
Native softening and distinct-root ambiguity reject without changing owned
state. Snapshot reuse, copy, no-argument reinitialize, commit/reset and inherited
outer rollback pass. The outer probe is a test method, not a mesh update.

Each attempt has277 frozen source/fixture files whose hashes match its pre-load
manifest and identical before/after source proof. Both actual mapped copied
`kirchoff.dll` modules were verified with Windows GetModuleHandleW and
GetModuleFileNameW, hash
`57c4c9a6cedb1ade1202914074dab942afc2f15abb114637619ca3cb5d9f074f`.
The exact failed and corrected test versions, capsule fixture, source payloads,
DLLs, runtime provenance, results, raw logs and actual exit observations are
retained. Attempt002's exact executed test remains frozen; the repository test
has only an EOF whitespace cleanup after execution, with no test forms changed.

The ZIP is decoded member by member and checked for complete inventory, CRC,
size and SHA256. Private `.native-cache`/FASL files are excluded and listed in
`archive-member-manifest.json`; original output directories remain. Exact
collector source is in `analysis-support/collect.py`. Packaging executes no
Lisp tests, point projections or solver updates.

These are controls of an explicit residual-only history scope extension with
unchanged numerical strength law and unchanged composite apex projector. They
do not establish a landslide, paper agreement, scientific validation or all-path
uniqueness. Third-party dependencies and arbitrary non-ASDF loads remain outside
the frozen first-party source claim.

Post-collection note: this folder uses `* -text` to preserve evidence bytes
through Git checkout. Only this README and `.gitattributes` plus their manifest
and checksum entries changed for that packaging correction. Raw attempts, ZIP,
collector and executed test snapshots were not changed or rerun.
