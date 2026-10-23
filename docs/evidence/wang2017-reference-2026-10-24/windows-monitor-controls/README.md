# Windows monitor and detached-launch controls

These are process-supervision controls, with **zero MPM/constitutive updates**.
Final monitor attempt005 passes12 checks; detached caller-command isolation passes9;
the final finite72-hour budget guard passes3 separate checks. Original outputs remain intact.

Monitor checks cover wrapper/cmd/SBCL PID, creation time and Windows SessionId;
live manifest phase/time/settling/loading counters despite stale gravity stdout;
native exit7; timeout exit3 and process-tree termination; READY/event handoff with
unchanged native identities; rejection of73h/NaN before launch; and executed source hashes.
Default wrapper budget remains4h and heartbeat60s. The launcher default remains8h.

Attempts001 and002 retain their initial failed controls: ISO timestamp string
comparison was corrected to typed instants, then CRLF fixture markers were trimmed.
Attempt003 passes9 controls. Attempt004 passes10 after the finite-budget guard.
Attempt005 adds complete READY JSON identity and executed-source verification (12 PASS).
These earlier artifacts are retained rather than overwritten.

Seven archives retain all existing control inputs, generated workers, logs,
requests, statuses and results, including selected sanitized Windows interruption
events in attempt001. Every archive was reopened; every member length and SHA-256
matches the original input. See archive-input-manifest.json and archive-verification.json.

Current wrapper, detached launcher, three test drivers and the trusted PowerShell
fixture are copied under current-source/. Final monitor wrapper/driver hashes match
the executed control. Historical wrappers/mock fixtures and detached generated
workers are preserved in their archives. Historical test-driver and associated
detached source provenance limits are explicit in source-and-scope-proof.json.

The detached worker survived its source command and captured stdout/stderr and
exit7, including spaced paths. Caller and worker actually used session11; this
does not prove survival of logoff, sleep, reboot or arbitrary job restrictions.
No scientific simulation result or numerical validation is claimed by this packet.
