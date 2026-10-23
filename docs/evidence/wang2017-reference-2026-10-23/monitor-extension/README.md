# Live Wang diagnostic monitor extension

User requested a longer running limit. Same cmd21008/SBCL49524 (start04:24:16.4348816UTC), new supervisor25584 replaces18936. Total deadline is14:24WIB/3h instead of12:54WIB/1.5h. Native source d60335a, case hash and postprocessor hashes are unchanged; original launch remains immutable. Monitor implementation a3afef0; READY/event transfer and retained handles are recorded.

Synthetic control003 PASS: logging continues beyond old deadline and exact native exit7 is retained; zero MPM updates. Controls001/002 failed fixture argument quoting and are retained, not counted PASS. This evidence concerns supervision only, not scientific validation or native full-run completion.

[Official PowerShell7.6.5 Windows file-handle implementation](https://github.com/PowerShell/PowerShell/blob/v7.6.5/src/Microsoft.PowerShell.Commands.Management/commands/management/Process.cs#L2244) was inspected before transfer; the synthetic test also checks continued inherited-file logging.
