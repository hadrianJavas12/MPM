# Simulation composition contracts

P1 extracts existing generic component storage/validation and non-material
composition declarations into `components/`. Their public symbols remain in
`cl-mpm/framework`; the old source paths are compatibility loaders and ASDF
loads the new owners directly. Material definition/factory ownership is in
root `materials/`.

This is the first ownership extraction, not the completed orchestration
migration or a new independent ASDF API. Scenario lifecycle/configuration and
other framework modules transition under later gates. No solver or numerical
formula is implemented here. See `docs/architecture/P1_CONTRACT_EXTRACTION.md`.
