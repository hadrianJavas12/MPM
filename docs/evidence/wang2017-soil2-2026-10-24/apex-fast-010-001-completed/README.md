# Completed opt-in Soil2 composite-apex trial

**Configured run complete:** native exit0,6s physical loading,60mm commanded
descent at0.01m/s (100times paper rate); audit/render and detached worker exit0.
This is not the600s paper-rate run and collection does not establish a landslide.

This run intentionally uses the NEW optional composite-apex material. It adds
positive hydrostatic volumetric plastic flow at the MC apex (gA=p), while retaining
the stated shear/strength inputs. It is different constitutive physics from the
retained strict zero-dilation run, whose failure evidence remains separate. It
must not be described as an unchanged or paper-exact material model.

The trusted collector executed once after native completion. Its unmodified
original summary/README/index are retained as `collector-*-original` and
`collector-evidence-manifest.json`; this collection-only review adds the explicit
model scope and media/source checks. Production source, solver, renderer and
original run outputs were not modified or rerun.

All native raw CSV/VTK/deformation-gradient files, original audit/manifest/runtime
proof and exact selected executed sources are archived. Detached request, worker
start/exit and adjacent native/wrapper logs are in `control-logs.tar.gz`. The raw
rendered PNG sequence and private compiled cache/FASLs are omitted; their original
folders remain intact. Overview/energy PNGs and the exact MP4 are retained here.
Every archive member is reopened and checked for size/SHA256 and full inventory.

`collection-review.json` records completion/status, source/DLL checks, archive
counts/hashes and media metadata. It performs no physical interpretation, solver,
rendering, numerical test or replay; physical analysis is handled separately.

## Unmodified generic collector context

# Wang2017 prescribed descent evidence

Real Windows MPM accelerated-rate trial; loading velocity 0.01 m/s (100x reference), target 0.06 m over 6 s. The configured target run is COMPLETE: actual time 6 s, commanded descent 0.06 m. The historical project 0.1m full-benchmark status is NOT_RUN; the reference-rate full-target status is NOT_RUN. That historical endpoint is not newly verified from the paper. Relief height 10 m and bottom tangential fixity are assumptions; finite penalty compliance is measured separately. Exact executed source (except private compiled cache) and raw VTK/CSV are archived. Every archive member was reopened and checked against collected input bytes. The collector in support/ was executed after native completion and may differ from the collector hash recorded at native launch; it is not part of the native-executed source claim. Renderer/reader hashes are checked separately in collection-source-proof.json. Control logs are attributed separately; an expected negative control is not a successful physical run. No FEM local-arc solver equivalence, peak-load reproduction or laboratory validation is claimed.
