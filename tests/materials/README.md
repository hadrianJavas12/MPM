# Material Tests

Constitutive, ownership, and diagnostic contracts.

Wang2017 preparation (Windows launcher, fresh JSON output):

```powershell
.\windows\cl-mpm.cmd tests\materials\wang2017-history.lisp output\FRESH-history.json
.\windows\cl-mpm.cmd tests\materials\mc-failure-capture.lisp output\FRESH-capture.json
```

History controls cover fixed-frame Eq5–6 and Soil2 cohesion, not a coupled particle
adapter. MC capture controls intentionally reject synthetic states, retaining exact
return inputs and testing JSON replay/rollback; these are not the old Wang run.
