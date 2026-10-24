---
title: Unnotched MC gravity scenario and native gates
type: synthesis
tags: [mpm, unnotched, gravity, strength-reduction, windows-native]
sources: [docs/benchmarks/UNNOTCHED_MC_GRAVITY.md, research/references/unnotched-mc-ssr/contract.json, docs/testing.md]
updated: 2026-10-24
---

# Unnotched MC gravity scenario and native gates

Implements [[unnotched-landslide-method-selection]] on branch
`codex/unnotched-gravity-benchmark`, first source2308a1e. Six short scenario
owners compose the unchanged native perfect MC material/solver with unnotched
D1-inspired polygon, independent SRFs1/1.40, smoothstep gravity ramp0–2s and
constant gravity2–6s. No driver, initial weak seed, notch, elastic release or
state reset is hidden. Fixed grid bottom is not Coulomb runout contact.

Frozen001 passes five input/geometry/BC/ramp groups then fails a caller-local
counter fixture. It still executes two real updates.002 uses shared synchronized
counters, skips the five passed groups and closes runner/CSV/VTK/read-only:
1760material calls,880MPs,two updates,three states/2640CSV rows. Both285file
snapshots match before/after, actual copied DLL is verified, and all three VTKs
plus two CSVs are byte-identical between attempts. Production numerics unchanged.

Independent002 audit passes with frozen source constants and actual scale1 PNG
inspection;001 fallback/provenance limitations remain recorded. The states are
tiny elastic motion, not landslide proof. Native wall cost and initial stable dt
justify a bounded first6s reduced trial, without guaranteeing plastic runtime.
Baseline follows sequentially. Detection conventions were fixed before results.

Thirteen synthetic supervision assertions and9+2gravity-alias detachment/default
checks pass with zeroMPM; delayed001fixture expiry/exit8 is preserved. Raw/settings
remain intact. [[wang2017-residual-history-scope]] remains a separate tested repair
checkpoint, not an automatic full rerun or an achieved-landslide claim.
