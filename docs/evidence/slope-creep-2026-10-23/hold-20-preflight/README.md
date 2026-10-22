# 20s hold-extension preparation

Actual Windows preflight on ebfa5e5 passes three controls without timesteps: only duration10->20,frames101->201 and computational maxUpdates30000->60000 differ. All physical configuration values and0.1s cadence agree.

Comparator controls on b6f499b use genuine saved data: historical gravity pair PASS, contact/work self-comparison PASS, different loading correctly rejected (expected exit1). Optional --allow-increased-update-budget declares the cap exception; raw budgets and validity are reported. Every physical field/cadence and VTK/material/contact/work CSV prefix still require exact agreement. The actual10s->20s numerical regression is PENDING, not proven by these preparation controls.
