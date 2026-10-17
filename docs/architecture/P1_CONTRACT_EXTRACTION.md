# P1: existing material and composition contracts

This is the first reviewed extraction after the full P0 inventory. It is an
ownership change, without a new registry, numerical law or particle class.
[Approvals](MIGRATION_APPROVALS.json) record exact source hashes and target forms.

| Starting source | Target | Preserved responsibility |
| --- | --- | --- |
| `framework/components/specifications.lisp` | `src/simulation/components/base.lisp` | `component`, `option`, `make-component` |
| Same | `materials/core/definition.lisp` | Existing `material` class and `make-material` profile selection |
| Same | `src/simulation/components/specifications.lisp` | Remaining geometry/boundary/loading/solver/simulation declarations |
| `framework/components/materials.lisp` | `materials/adapters/native.lisp` | Native class/initarg generic dispatch and particle factory |

All defining forms retain `cl-mpm/framework` symbols and exact bodies. The
existing `:native` extension point and specialized generic dispatch already
select native constitutive classes; a redundant mutable registry is unnecessary.
The native adapter includes particle construction through `cl-mpm/setup`; it is
an integration adapter, not a pure constitutive solver.

Load order is package -> base component -> material definition -> remaining
specifications -> native factory. Existing ASDF component IDs are preserved
where possible with explicit relative `:pathname` values. Historical source paths
remain forwarding loaders; ASDF loads the new definitions directly, once.
This first stage is not an independently loadable lower material ASDF system.
New system umbrellas/package aliases belong to the later orchestration stage.

The CLI snapshot must copy `src/simulation/` and `materials/` along with the
framework and validate the resolved path of every file component before load.
Record copied byte hashes and keep native engine/FASL/DLL provenance separate.
An ASDF system-directory check alone does not verify sibling material sources.

## Verification before acceptance

1. Compare the complete original defining forms with extracted forms, including
   declaration scopes; only package preambles/compatibility wrappers are new.
2. Run fresh-process Windows native ASDF loading and class/generic identity checks,
   old source-path compatibility, and existing framework/material/config contracts.
3. Run bounded actual VM and native MC triaxial and Joss controls, checking real
   VTK/CSV against the unchanged corresponding clocks and particle identities.
4. Keep Node compatibility checks green. Full deterministic VM 2D/3D and serial
   Joss acceptance on the migrated snapshot remains NOT_RUN until executed.
5. Record copied source/inputs, exact executed commit, native binary hashes,
   commands, exit status and retained outputs. No parameter/tolerance changes.

P1/G1 remains partial while diagnostics and deeper native contracts are still
owned at old locations. The new root material directory does not establish that
all models have migrated or that MC H/HS physical verification is complete.
