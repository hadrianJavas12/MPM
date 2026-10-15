# CL-MPM documentation

| Document | Read it to... |
|---|---|
| **[AI_HANDOVER.md](AI_HANDOVER.md)** | **Start or hand over a coding-agent session: goals, PR stack, architecture, constraints, verified tests, risks and next actions** |
| [windows-setup.md](windows-setup.md) | Install the toolchain and verify it on native Windows |
| [usage.md](usage.md) | Run simulations from the REPL, scripts and examples; read the output |
| [studio.md](studio.md) | Use CL-MPM Studio (web UI), its parameters and HTTP API |
| **[MODULAR_LISP_IO.md](MODULAR_LISP_IO.md)** | **Planned:** selective .lisp module import/export, merge/replace preview and complete preset portability ([issue #5](https://github.com/hadrianJavas12/MPM/issues/5)) |
| [architecture.md](architecture.md) | Understand how the code base and the MPM algorithm are organised |
| [development.md](development.md) | Change the code, run the checks, troubleshoot, see what the Windows port patched |
| [testing.md](testing.md) | Repeat automated checks; distinguish SBCL contract tests, full-engine checks and CI blockers |
| [windows-verification-2026-10-14.md](windows-verification-2026-10-14.md) | Review the native Windows evidence, observed fixes, tool versions and remaining limits |
| [REFERENCE_REPRODUCTION.md](REFERENCE_REPRODUCTION.md) | Run the experimental Joss Bay geometry/material/phases adapted from the author example; inspect provenance and result limits |
| [RUN_ACCEPTED_COLLAPSE_WINDOWS.md](RUN_ACCEPTED_COLLAPSE_WINDOWS.md) | Run the visually accepted Joss collapse parameter set through the Windows native launcher, render VTK and inspect evidence |
| [SCIENTIFIC_AUDIT_2026-10-15.md](SCIENTIFIC_AUDIT_2026-10-15.md) | Inspect the independent output-authenticity audit, native numerical controls and remaining scientific-validity gaps |
| [UPSTREAM_CHANGE_REPORT.md](UPSTREAM_CHANGE_REPORT.md) | Read the professional comparison against the original CL-MPM repository, with Git provenance and retained evidence |
| [TRIAXIAL_CALIBRATION.md](TRIAXIAL_CALIBRATION.md) | Follow the clay triaxial calibration method, assumptions, native results, strain conventions and limitations |
| [Calibration launcher guide](../calibration/README.md) | Run the 70 mm × 140 mm native specimen, generate adjacent stress-strain plots/video, and initialize parameters from CSV |

New to coding on this project as an AI agent? Read root [AGENTS.md](../AGENTS.md) and [AI_HANDOVER.md](AI_HANDOVER.md) first. For running the software, follow [windows-setup.md](windows-setup.md), then run the smoke test and open Studio.
