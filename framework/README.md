# Historical source-loader compatibility

Implementation owners are now `materials/`, `src/simulation/` and `scenarios/`.
The canonical ASDF declaration is the root `cl-mpm-framework.asd`; public package
and system names remain unchanged. This tree retains tested historical LOAD
paths and an ASDF forwarder. It contains no production implementation owners.

Use the [Windows case guide](../docs/REUSABLE_FRAMEWORK.md),
[scenario guide](../scenarios/README.md), [material API](../materials/README.md)
and [diagnostic contract](../materials/DIAGNOSTICS.md). Current results and
exceptions are in [architecture status](../docs/architecture/STATUS.md).

Wrappers are retained for compatibility, not as a second architecture layer.
Do not delete them without a reviewed source-path compatibility decision.
Historical regression/evidence has been preserved under docs/evidence/ and
research/reports/; current numerical and scientific acceptance are separate.
