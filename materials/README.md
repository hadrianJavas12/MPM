# Material ownership

This root is introduced by architecture migration P1. It currently owns the
existing material component definition (`core/definition.lisp`) and native
particle factory integration (`adapters/native.lisp`). Defining forms and CLOS
symbols are preserved; these files are loaded by the compatibility system
`cl-mpm-framework` in their original dependency order.

The profile component selects an actual native constitutive class and parameters.
It is not a constitutive integrator. The native adapter also constructs particles
through `cl-mpm/setup`; it is an integration boundary, not pure material physics.
The legacy `:elastic` profile still uses native VM with plasticity disabled.
`:native` accepts a dedicated native class and does not force MC to inherit VM.

Constitutive implementations, model-specific state/evolution and diagnostics
have **not all migrated** yet. They move in later reviewed stages without
changing equations, defaults, DLL behavior or package/class identity. A model's
evolution belongs inside its model directory; shared utilities require real
cross-model reuse. Experimental H/HS physics remains a separate gate/branch.

See [folder ownership](../docs/architecture/FOLDER_OWNERSHIP.md),
[per-file matrix](../docs/architecture/FILE_MIGRATION_MATRIX.json) and
[migration execution log](../docs/architecture/MIGRATION_EXECUTION_LOG.md).
