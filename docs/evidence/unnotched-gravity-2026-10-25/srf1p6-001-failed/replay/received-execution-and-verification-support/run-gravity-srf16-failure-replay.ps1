$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath 'D:\MPM'
$taskReplay = 'output/unnotched-gravity-2026-10-25/srf1p6-failure-replay-001'
$taskLog = "$taskReplay.log"
$taskExit = "$taskReplay-exit.json"
if ((Test-Path -LiteralPath $taskReplay) -or (Test-Path -LiteralPath $taskLog) -or (Test-Path -LiteralPath $taskExit)) {
    throw 'Replay must use fresh output, log, and exit paths.'
}
$taskStart = [DateTime]::UtcNow.ToString('o')
$taskHelper = '.tmp/gravity-srf16-failure-replay.lisp'
$taskCommand = [ordered]@{
    startedUtc = $taskStart
    command = 'windows\cl-mpm.cmd .tmp\gravity-srf16-failure-replay.lisp output\unnotched-gravity-2026-10-25\srf1p6-failure-replay-001 output\unnotched-gravity-2026-10-25\srf1p6-001'
    helperSha256 = (Get-FileHash -LiteralPath $taskHelper -Algorithm SHA256).Hash.ToLowerInvariant()
    purpose = 'FIRST and ONLY exact SRF1.6 failed principal replay; one point call, zero MPM updates'
}
$taskCommand | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$taskReplay-command.json" -Encoding utf8
& .\windows\cl-mpm.cmd .tmp\gravity-srf16-failure-replay.lisp output\unnotched-gravity-2026-10-25\srf1p6-failure-replay-001 output\unnotched-gravity-2026-10-25\srf1p6-001 *> $taskLog
$taskCode = $LASTEXITCODE
[ordered]@{
    startedUtc = $taskStart
    finishedUtc = [DateTime]::UtcNow.ToString('o')
    exitCode = $taskCode
    helperSha256 = (Get-FileHash -LiteralPath $taskHelper -Algorithm SHA256).Hash.ToLowerInvariant()
    log = $taskLog
    result = "$taskReplay/replay-result.json"
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskExit -Encoding utf8
Get-Content -LiteralPath $taskExit
Get-Content -LiteralPath $taskLog -Tail 6
exit $taskCode
