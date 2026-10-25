# Default dispatch compatibility: corrected evidence layout

The actual native results are unchanged: 34 existing strict groups and four bounded output groups passed on ac767e1; two genuine USF updates accepted 1760 material calls. Three VTK states and two CSVs were already compared byte for byte to the retained strict baseline. No test, solver, replay, numerical comparison, renderer or scientific audit was repeated for this packet.

The initial packet placed both complete run manifests in one ZIP. Root's existing verifier correctly rejected that layout with its one-manifest-per-ZIP assertion. This is a packaging failure, not a native test or byte mismatch. The original packet and failed root copy remain untouched under output; their indices, original archive hash, original packaging code/metadata and actual root failure record are retained or referenced in packaging-failure/. The original combined ZIP is not copied into this packet.

The first repack helper stopped before its first ZIP write because its archive parent directory had already been copied with the result files. That helper and partial packet were preserved under output; the observed filesystem failure and exact helper are included here. Allowing that already existing parent directory changes packaging only and repeats no native or numerical work.

Each corrected ZIP contains exactly one complete executed source manifest and payload, with the same actual raw outputs, runtime/DLL proofs, logs, commands and exits. All 612 original archive members are partitioned exactly once, CRC-tested and decoded against both the original ZIP and immutable raw files. Source counts are 287 and 289. No missing standalone old34 hash proof is invented; its actual source manifest/runtime provenance and existing post-run verification remain authoritative.

Default optional composite loading remains false. Copying optional sources into a snapshot is not loading that model. This packet demonstrates default compatibility within the retained controls, not a complete slope run, landslide, calibrated runout or scientific validation. Root owns independent verification and staging with the unchanged verifier.
