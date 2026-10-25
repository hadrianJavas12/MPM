# Composite SRF1.6 h0.5 launch-helper checkpoint

Status: **SOURCE ONLY — NOT_READY / NOT_RUN**, 26 October 2026 WIB.

The archived `capture-composite-h05-launch.py.txt` is an unfinished launch-glue
draft. It refuses both modes before any preparation or capture. It is not a
shipped CLI and is not evidence of a launched solver, passing gate or live proof.

Restore its bytes to `D:/MPM/.tmp/capture-gravity-composite-h05-launch.py` before
continuing. Its ROOT calculation assumes that exact `.tmp` placement. The draft
imports definitions from the existing `.tmp/capture-gravity-composite-apex-launch.py`
and reuses its copy/hash/clock helpers without changing the historical helper.
Do not execute the old prepare/capture functions: their h1 counts and one-hour
budget are incompatible with this study.

The pending native gate is `tests/benchmarks/gravity-composite-apex-refinement-controls.lisp`,
intended output `output/mc-composite-apex-2026-10-26/fine-controls-001`.
The case is `cases/benchmarks/gravity-slope-mc-composite-apex-srf-1p6-h05.lisp`;
the protocol is `research/references/unnotched-mc-ssr/composite-apex-srf1p6-h05-contract.json`.
Both the gate and its saved-output/binding controls remain unexecuted here.

Finish the numbered TODOs in the draft only after the reset and root review.
Expected genuine pilot counters are 3520 MPs, two USF updates, 7040 accepted
constitutive calls and three saved VTK states. The full proposed trial is six
physical seconds with a three-hour wall budget. Its only physical input change
from completed coarse SRF1.6/composite is mesh size 1 to 0.5 m; the resulting
stable timestep also changes. This is a resolution study, not a convergence or
landslide claim. Root owns all launch authorization and quiet monitoring.

No helper preparation, capture, native update, test, process query or automation
operation was executed to create this source checkpoint. Historical evidence
and immutable helper copies remain unchanged.
