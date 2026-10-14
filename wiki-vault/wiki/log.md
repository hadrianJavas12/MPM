# Log

## [2026-10-13] setup | Vault created


## [2026-10-14] ingest | cl-mpm repository + Windows port refactor

Created pages: cl-mpm, cl-mpm-architecture, windows-port, serial-mpi-standin, magicl-patches, cl-mpm-studio, refactor-2026-10-14. Source material: workspace docs/ folder.

## [2026-10-14] ingest | Studio custom-model hardening and verified handover

Read repository handover, live PR stack, code, tests and public CI annotations.
Recorded immutable [[studio-hardening-2026-10-14]]; added [[studio-custom-models]],
[[studio-geometry-material]], [[studio-verification-2026-10-14]]; updated Studio,
project and architecture cross-links and index. Kept historical Windows-port
claims attributed; superseded unknown CI cause with the confirmed billing lock.
Recorded 33 passing Node/SBCL contract tests and explicitly open full-engine,
browser and scientific gates. Normalized wikilink sources as YAML strings.

## [2026-10-14] ingest | Modular Lisp I/O and full preset portability

User requested import/export of individual parts, multiple selected parts and
complete simulation presets in addition to the GUI workflow. Wrote design
spec `docs/MODULAR_LISP_IO.md`, opened GitHub issue #5, updated AI handover,
Studio docs and agent guidance; added [[studio-modular-lisp-io]] and indexed
it. Status remains proposed, not implemented. Existing custom source import
and generated simulation runner export stay separate. Raw archive unchanged.

## [2026-10-14] ingest | Modular Lisp preset MVP implementation

Reviewed the earlier [[studio-modular-lisp-io]] requirement and updated
repo docs, AI handover and execution plan. New feature branch
`feat/studio-modular-lisp-presets` implements strictly declarative
geometry/material/solver/output/constitutive source modules, selected or
whole-preset .lisp I/O, inert source restoration, staged preview, merge/replace
and atomic Apply/Cancel. Updated [[studio-modular-lisp-io]] and wiki index.
Eight new Node regression cases authored; isolated V8 checks, not full hosted
CI/Windows SBCL/browser physics tests. Kept vault raw sources immutable.
