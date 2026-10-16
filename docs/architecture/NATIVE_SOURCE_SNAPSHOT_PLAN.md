# Native source snapshots for P2a — bounded design

2026-10-16, Asia/Jakarta. **DESIGN ONLY; no implementation or test run.**
The latest user direction permits architecture work to continue and cancels the
current full serial Joss run. Retain its user-cancelled status and saved 4.2 s
evidence; do not restart it or turn cancellation into PASS. The earlier P2 plan's
full-Joss prerequisite is superseded as an authorization barrier. Pending full
regressions remain NOT_RUN/RUNNING/CANCELLED as actually recorded, not accepted
because a source snapshot exists. The root reports current full VM 2D complete
with native/comparison/audit exit 0 and VM 3D still running; this design does not
independently re-audit those results.

## Actual gap and unchanged dependency chain

`scripts/run-case.lisp` currently copies framework, materials and src/simulation
sources, case and bundled JSON. It checks only the framework's child components.
Its provenance correctly excludes native engine/dependency/FASL/DLL identity.
That scope is insufficient once P2a puts native constitutive formulas in materials:
`cl-mpm/constitutive` could still load definitions or FASLs from the working tree.
Copying materials alone does not select the copied native ASDF system.

Keep existing ASDF topology: utils/fastmaths → constitutive → ext → particle →
core/solvers; framework consumes these systems. Register the copied root ASD,
not a new materials system depending on the full particle umbrella. P2a's exact
formula ordering remains package → elastic formulas → legacy constitutive tail.
Do not introduce particle→damage or material→framework dependencies.

## Minimal complete first-party payload

Preserve repository-relative layout beneath each fresh `OUTPUT/source/`:

| Payload | Purpose |
| --- | --- |
| `cl-mpm.asd` | Defines the selected native systems and their source root. |
| Full `src/` source tree, including settings, cpp, models, damage and future fragments | Freeze native definitions together; exclude generated working-tree FASLs. |
| `materials/`, `framework/` source/ASD trees | Existing migrated owners and framework entry point. |
| `libs/kirchoff.dll` unchanged | Preserve Windows native backend binary at the path resolved by copied cl-mpm. |
| `config/git-commit-version.txt` unchanged | Required at compile/load time by `src/core.lisp:9–20`; absence must fail explicitly, not be replaced with an invented hash. |
| Existing copied case, run-case script, schema and bundled JSON | Retain current input-root and case semantics. |

Hash original and copied bytes before load, including ASD/DLL/config inputs;
write an immutable manifest before compilation, then verify copies after loading.
Do not regenerate the git-version file inside the snapshot. Record its stored
value separately from the actual executed source commit and working-tree hashes.
Preserve bootstrap Windows scripts as provenance; third-party Quicklisp/vendored
dependencies and OpenBLAS can remain installed dependencies with paths, versions
and binary hashes recorded separately. Copying all optional examples/deps is not
necessary to freeze the selected first-party runtime.

## Startup sequence and compilation policy

Use a fresh Windows SBCL process bootstrapped by the existing windows/init.lisp,
which loads CFFI and registers paths but does not quickload the engine. Reject
an already-loaded first-party native runtime; clearing ASDF definitions cannot
unload classes, generic methods or an already-loaded DLL safely.
1. Parse arguments and copy/hash the payload using only bootstrap ASDF/UIOP.
2. Remove working first-party registry entries and invalidate registered system
   definitions owned by replaced root/framework ASDs. Keep external dependencies.
3. Explicitly load `source/cl-mpm.asd` and `source/framework/cl-mpm-framework.asd`;
   place their directories first in project resolution. Check canonical ASD roots.
4. Quickload **copied** cl-mpm/settings, then set its existing effective policy to
   `(optimize (speed 3) (safety 1) (debug 1) (compilation-speed 0))`, matching the
   current CLI. Move the current pre-snapshot settings quickload to this point.
   `src/settings.lisp:19` otherwise defaults to the debug policy; many native
   files read `#.cl-mpm/settings:*optimise-setting*` while being compiled/read.
5. Compile/load selected copied first-party components into a fresh run-private
   FASL cache covering src, materials and framework. Do not reuse the CLI's old
   working-src→fast-cache-safe translation or force-recompile all Quicklisp deps.
6. Preserve literal per-file optimization declarations, feature flags, workers,
   OPENBLAS_NUM_THREADS and OMP_NUM_THREADS. Record actual values; do not change
   numerical/runtime policy as a side effect of source freezing.

## Verify the selected execution plan, not every optional ASD path

Before loading native systems, obtain the actual selected ASDF load-op plan under
the recorded Windows/features state. Include the separate settings bootstrap
plan and the requested framework/case dependency closure, including activated
system connections; settings may disappear from a later plan after it is loaded.
For every selected first-party source action, resolve canonical path, require
containment under source/, existence and manifest byte identity. Include all
selected native dependency systems, not only framework's immediate children.
Record external selected actions separately. Recheck any later case-selected
system before it loads; arbitrary explicit source LOADs need their own recorded
inputs and cannot silently inherit an exact-native-snapshot claim.

Do not traverse every registered/optional system and require every component to
exist: cl-mpm.asd contains unrelated examples and two already-recorded absent
legacy paths. A selected missing/escaping source is a real failure; an unselected
optional path is not a blocker. Definition metadata alone is not execution proof:
retain selected source→FASL mappings/load records and source/cache paths.

## Keep the actual DLL backend and disclose limits

`src/cpp.lisp:17` derives libs/ from ASDF's **cl-mpm** root, so selecting the copied
root naturally points to source/libs/. Keep cpp.lisp and its 94–325 handler-case
unchanged. Preserve the same available DLL, CFFI entry points and fallback choice.
The bootstrap/env currently adds working libs/ to CFFI directories and PATH;
ensure the copied DLL is selected and verify its actual loaded module path/hash
externally. Directory-list ordering or a copied-file hash alone is insufficient
proof. Reject a provenance mismatch instead of silently switching backend.
Record actual OpenBLAS/dependent module paths/hashes; do not rebuild DLLs or fix
the existing incomplete Lisp fallbacks in this provenance change.

Acceptance is bounded: fresh-process path/manifest and cache checks, negative
controls for a selected escape/missing DLL, ownership normal/legacy contracts,
then existing bounded native VM/MC/Joss controls with explicit executed sources.
Keep ongoing/cancelled full-run records intact; schedule no new full Joss here.
Native-freeze implementation and all acceptance checks above remain **NOT_RUN**.
