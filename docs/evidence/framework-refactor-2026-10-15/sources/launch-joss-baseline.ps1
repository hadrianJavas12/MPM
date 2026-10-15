$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:\MPM'
$taskBase = 'D:\MPM\output\framework-refactor-2026-10-15'
$env:CL_MPM_REFERENCE_PNG = '0'
$started = [DateTime]::UtcNow.ToString('o')
try {
  & 'D:\MPM\windows\cl-mpm.cmd' ($taskBase + '\run-frozen-joss.lisp') ($taskBase + '\joss-baseline-config.json') ($taskBase + '\joss-baseline') *> ($taskBase + '\joss-baseline.log')
  $nativeExit = $LASTEXITCODE
  @{ startedUtc=$started; finishedUtc=[DateTime]::UtcNow.ToString('o'); exitCode=$nativeExit } | ConvertTo-Json | Set-Content -LiteralPath ($taskBase + '\joss-baseline-status.json') -Encoding utf8
  exit $nativeExit
} catch {
  @{ startedUtc=$started; finishedUtc=[DateTime]::UtcNow.ToString('o'); exitCode=-1; error=$_.Exception.Message } | ConvertTo-Json | Set-Content -LiteralPath ($taskBase + '\joss-baseline-status.json') -Encoding utf8
  exit 1
}
