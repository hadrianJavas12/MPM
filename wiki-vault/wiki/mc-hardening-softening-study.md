---
title: Native Mohr-Coulomb hardening and softening study
type: synthesis
tags: [cl-mpm, mohr-coulomb, research, native-windows, verification]
sources: [research/README.md, research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md, research/references/PROVENANCE.md, research/reports/M0_SERIAL_REGRESSION.md]
updated: 2026-10-16
---

# Native Mohr-Coulomb hardening and softening study

The user authorized the M0–M6 master plan, stage commits/pushes and economical
automatic continuation. This is an independently maintained native software and
numerical-comparison project, with no UI work or thesis framing.

## Verified checkpoint

[[reusable-simulation-framework]] has an exact serial Joss control: 191 physical
states through 40 s, all 193 particle VTKs per run and complete CSVs identical.
The source audit identifies original `c749d32` and executed after `41403f4`.
Completion status `909fddf` is HEAD at exit, not the loaded source snapshot.
All fields are finite, mass is constant and protected-base damage is zero.
The four-worker strict failure (176/191 states) remains preserved.

M0 remains **PROVISIONAL**: `64f47cc` passes 9 material, 10 configuration,
10 framework contracts and 36 Node tests. Its current full 2D regression has
51 byte-identical VTKs and zero CSV differences; the independent available-field
audit passes. The original 3D baseline finished; its matched after run is still
running. The four-worker exception remains open. Legacy
VM-specific yield formulas must not be used for an MC particle. Unsupported
history/rollback capabilities require explicit rejection.

## M1 reference preparation

The supplied plan was copied byte-identically; the local 28-page residual-soil
PDF matches its declared SHA-256. Pages 3, 6, 7, 11 and 17 were visually audited.
Structured values preserve source pages, model family, units, missing entries,
assumptions and SI conversions. Nine data-only integrity tests passed.

Four H/HS proposals remain **execution disabled**. Residual-soil H and HS share
the raw prepeak knots and zero cohesion. H plateaus at 33.99 degrees; HS reaches
16.34 degrees at source strain 0.2. This source coordinate has not been equated
to CL-MPM's internal accumulator. The source's 20× FLAC input adjustment is
inactive, and its half-strain footnote is explicit.

The separate Zhan/Zang reference has no supplied prepeak initial strength;
that initialization remains unresolved. The source naming discrepancy, page-3
height/sketch mismatch and unspecified water-modulus unit remain recorded.
[[triaxial-clay-calibration]] is prior VM demonstration context, not evidence
that MC H/HS or true pore-pressure CU has been implemented.

## Next gates and maintenance

An isolated, uninstalled MC prototype passes 32 native material-point tests.
Its design is `research/reports/M2_RETURN_MAPPING_DESIGN.md`; staged sources,
log and hashes are in `.tmp/mc-evolution-stage/`. Root isolation is sampled,
without a completeness proof or adaptive continuation. This is provisional
point evidence, not full MPM, M2 acceptance or physical validation. Integrate
only on the separate experimental branch after the framework checkpoint.

After M0, dedicated H/HS mechanics need strain/state, corner/apex, yield and
return-map tests before paired 3D cylinders at 100/200 kPa and a separate soil
cliff experiment. No fitting to slide images or invented lab data is allowed.
Mesh dependence, missing calibration and [[scientific-authenticity-audit-2026-10-15]]
remain explicit limits. M2–M6 are not completed by the data-preparation tests.

The cleanup inventory found no proven safe deletion candidate. Compatibility
loaders, failed evidence, immutable raw sources and personal settings stay intact.
The active handover was shortened and its complete earlier text archived to
reduce repeated context loading. The existing heartbeat is active every five
hours, aligned to the observed reset; read current handover/status before work.
