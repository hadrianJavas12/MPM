# Opt-in composite-apex slope: LAUNCH-ONLY provenance

This packet captures the opt-in composite-apex Soil2 slope launch on24October2026,
source `3caa6bea5d447be34c8bd1104311f1aa34b57986`. It verifies launch identity and selected frozen input bytes only.
**It does not establish simulation completion, a landslide or scientific PASS.**

The case is accelerated0.01m/s loading (100times paper rate), targeting0.1m
over10s. Only the endpoint/duration/frame count extend the prior60mm/6s case;
velocity0.01m/s, material and other numerical inputs remain unchanged. It is not a600s paper-rate run. Soil2 uses the declared signed plastic
tensor norm, incremental polar corotation approximation and monotonic history
scope rejection. This explicitly NEW opt-in model adds positive hydrostatic
apex volumetric flow gA=p. It is different constitutive physics from the retained
strict baseline and is not a paper-specified apex convention. No hidden history
maximum, parameter tuning or baseline switch is implied.

`frozen-launch-sources.zip` preserves the observed selected frozen source/DLL files (count recorded in verification),
source manifest and provenance, exact launch request/worker script and proof,
initial worker identity, the adjacent launch record, and timestamped copies of
status/manifest read once during capture. It also contains the three launch-hashed
postprocessors and trusted wrapper/source snapshots. Request and worker bytes
match the launch-recorded hashes; wrapper bytes match the request hash. The
detached-launcher file is a capture-time support snapshot, not an independently
pre-hashed executed-source claim.

All frozen files match their pre-load manifest hashes/sizes and their original
workspace bytes during this capture. The actual copied `kirchoff.dll` path/hash
is recorded by `GetModuleHandleW/GetModuleFileNameW`. Frozen-byte flags are the
runtime source-provenance claims, supplemented by the independent byte checks.
Third-party sources/FASLs and non-ASDF arbitrary loads are outside that claim.

One narrow Windows process identity observation checks WMI worker31296,
wrapper38252, cmd25892 and SBCL27304, including creation times and SessionId11.
This is not polling or a completion/continued-health guarantee. WMI detachment
does not prove immunity to logoff, sleep, reboot or provider-job policy.

Active CSV, VTK and log files were deliberately **not read or archived**.
Private native cache/FASLs are omitted. The immutable launch documents/source
files were checked unchanged during packaging. Changing status/manifest were
read once and represented only by timestamped snapshots.

Every ZIP member was decoded and checked for exact size/SHA256, complete member
inventory and CRC. `archive-member-manifest.json`, `launch-verification.json`,
`evidence-manifest.json` and `SHA256SUMS` retain the checks. Exact collector source
is under `analysis-support/`. No solver or numerical tests were executed here.

The first availability check immediately after this launch found the source
manifest/status/worker-start but no runtime provenance yet. No verified packet
was created and no waiting/polling followed. This later capture was separately
authorized at the15minute wakeup after the runtime proof became available; the
initial unavailable observation remains part of the recorded history.
