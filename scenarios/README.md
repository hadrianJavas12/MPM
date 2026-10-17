# Reusable scenarios

`cases/` contains short trusted experiment compositions. This directory owns
assembly, geometry construction, boundary/loading procedures, measurements and
run stages. Constitutive updates, material state and evolution belong to
[`materials/`](../materials/README.md); generic lifecycle/configuration belongs
to `src/simulation/`. Public packages retain their historical names for CLOS
and source compatibility.

| Scenario | Entry implementation | Scope |
| --- | --- | --- |
| Triaxial | `triaxial/adapter.lisp`, `triaxial/runner.lisp` | Spatial rectangle/cylinder and the explicitly homogeneous comparator |
| Cliff | `cliff/adapter.lisp`, `cliff/build.lisp`, `cliff/run.lisp` | Generic chalk cliff construction and explicit solver |
| Joss | `joss/build.lisp`, `joss/phases.lisp`, `joss/run.lisp` | Retained staged reference procedure with protected foundation |

Use the [Windows composition guide](../docs/REUSABLE_FRAMEWORK.md) to run or
modify a case. Supported substitutions are checked by the scenario; an
unsupported material/control combination must fail explicitly. The Joss recipe
has additional constraints and does not promise arbitrary material replacement.

The 2D triaxial case is plane strain with unit thickness, not axisymmetric.
The clay parameters are an assumed undrained-strength demonstration. There is
no pore-pressure solution or claim of laboratory calibration. Homogeneous
output applies affine kinematics deliberately and is identified separately
from spatial MPM output.

Historical files under `framework/scenarios/` remain source loaders, with no
scenario implementation ownership. Preserve these tested compatibility paths
until their removal has an explicit compatibility decision. See
[`STATUS.md`](../docs/architecture/STATUS.md) for current evidence and exceptions.
