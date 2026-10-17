# P1 bounded migration verification

Production implementation **3cd172e** was committed/pushed before testing.
P0 inventory **6f15148** preceded every production move. No constitutive
equation, numerical parameter/tolerance, class ancestry or native DLL changed.

| Actual Windows native check | Result |
| --- | --- |
| Framework / configuration / material diagnostics | 10 / 10 / 9 PASS |
| Compatibility: normal ASDF / legacy source loaders | 7 / 7 PASS |
| Source snapshot and escape rejection | 3 PASS |
| Node suite and syntax checks | 36 PASS, zero skipped; syntax PASS |
| VM triaxial: 480 MPs, 27 updates | Strict PASS, two states, position/CSV differences zero |
| Native MC triaxial: 32 MPs, two updates | Strict PASS, two states, position/CSV differences zero |
| Native MC cliff: 70 initial MPs, two updates | Both saved VTK files byte-identical to the prior control; native splitting preserved |
| Form/source extraction | 16 defining forms byte-identical; native adapter file byte-identical |

`manifest.json` verifies 32 retained artifacts. Run archives include the actual
frozen framework, root material/simulation owners, case and JSON inputs. The CLI
verifies copied bytes and component containment before loading; SHA-256 values
in this retained evidence were computed by the external collector. Focused
unit tests loaded committed production code from the working tree, with that
scope distinguished from the copied-source CLI controls.

Two failed **test fixtures** are retained. The first assumed a complete CLOS
precedence tail without SBCL's `SLOT-OBJECT`; the original source control confirms
that class already existed. Only the test assumption changed. The first escape
fixture still preferred the frozen ASDF registry; correcting the fixture makes
the unchanged guard reject a real checkout escape. Neither failure was repaired
by changing numerical physics or loosening a regression tolerance.

The cliff control exited 0 with exact VTKs but its native gnuplot PNG was
unavailable. The warning is retained; plotting is not marked PASS. Full VM
2D/3D and serial Joss G3 runs are a separate pending gate. The previous parallel
Joss strict failure also remains open. P1 is **PROVISIONAL**, G1 is **PARTIAL**;
this is not all-material migration, experimental calibration or true CU validation.

Reproduce focused checks with `windows\cl-mpm.cmd` and the scripts in
`tests/`: `framework-components.lisp`, `config-contracts.lisp`,
`material-diagnostics.lisp FRESH_OUTPUT`, `material-ownership-compat.lisp`
(also `legacy`), and `case-snapshot-contracts.lisp FRESH_OUTPUT`.
The original/native numerical comparison criteria are unchanged.
