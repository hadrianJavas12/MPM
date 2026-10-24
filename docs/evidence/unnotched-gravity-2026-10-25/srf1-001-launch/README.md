# SRF1 sequential baseline: launch proof only

The predeclared unnotched SRF1 control uses the same recipe and production sources as completed SRF1.40. Only SRF, reduced cohesion and reduced friction differ. The exact baseline case matches all previous frozen input gates and the pre-launch hash matrix; the actual compiled configuration also matches its derived expectation.

All282 copied source/input/DLL files match pre-load manifest hashes and lengths, with actual mapped DLL proof retained. Only source/case.lisp differs from the paired SRF1.40 snapshot. Full immutable sources stay under output for terminal packaging.

The separate copied live helper checks PID/session/creation time and parent chain once. It preserves the established Process timestamp clock for wrapper/cmd/SBCL and CIM clock for the detached worker. Packaging does not query processes again. Mutable status/manifest copies are not falsely presented as simultaneous with the stored live check.

The pre-launch matrix JSON is retained byte for byte. Its original inline Python invocation was not saved as a separate script file; this packet does not invent an executed historical script. The executed live helper and packer are retained exactly.

This packet establishes a native launch, not completion or landslide. No additional solver/input test/replay/render ran for packaging, and no survival of sleep/logoff/reboot is guaranteed. Raw bytes are preserved by * -text.
