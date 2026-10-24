# Soil2 fast010: LAUNCH-ONLY provenance

This packet captures the first full Soil2 slope launch on24October2026, source
`621146b`. It verifies launch identity and selected frozen input bytes only.
**It does not establish simulation completion, a landslide or scientific PASS.**

The case is accelerated0.01m/s loading (100times paper rate), targeting0.06m
over6s. It is not a600s paper-rate run. Soil2 uses the declared signed plastic
tensor norm, incremental polar corotation approximation and monotonic history
scope rejection; no hidden irreversible maximum or apex change is introduced.

`frozen-launch-sources.zip` preserves all271 selected frozen source/DLL files,
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

One narrow Windows process identity observation checks WMI worker48936,
wrapper41032, cmd38956 and SBCL20484, including creation times and SessionId11.
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
