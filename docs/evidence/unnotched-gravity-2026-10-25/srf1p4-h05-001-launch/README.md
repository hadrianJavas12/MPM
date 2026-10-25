# h0.5 same-physics refinement: launch proof only

The refined native run starts25October14:53:10WIB, source1a9f29a, with3h wall budget to17:53:10WIB. All282 immutable source/input/DLL files match their manifest and actual mapped backend proof. Only the exact case file differs from completed coarse SRF1.40: meshSize1m becomes0.5m. The actual compiled configuration differs only in meshSize;3520 particles are present. Stable timestep consequently changes, so this is coupled space/time refinement, not isolated mesh convergence.

The original copied live helper's run-path replacement is the only helper change. Its successful full PID/session/original-clock/parent-chain capture is retained. One earlier helper invocation encountered unpopulated nativeCommand/SBCL identities and failed on Id=null; its error is retained and did not restart the solver. Packaging does not query processes again. Status/manifest/log snapshots have separate capture times.

Study, refinement and fine-audit contracts match launch commit bytes exactly. The physical metre observer is a frozen protocol only at capture: its implementation/tests were still pending, and no fabricated observer PASS is included. Native h-scaled diagnostics remain separately identified. Pre-launch native mesh/input/bounded-output gate summaries and their index/root verification are included.

No full source ZIP is made at launch; immutable originals remain under output for terminal packaging. This is not completed native, coherent-slide, runout or scientific validation evidence. No sleep/logoff/reboot immunity is proved; * -text preserves artifact bytes.
