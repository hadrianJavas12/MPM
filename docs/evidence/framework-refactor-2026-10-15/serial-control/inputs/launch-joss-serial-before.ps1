$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:\MPM'
$taskBase = 'D:\MPM\output\framework-refactor-2026-10-15'
$env:CL_MPM_REFERENCE_PNG = '0'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$started = [DateTime]::UtcNow.ToString('o')
try {
  & 'D:\MPM\windows\cl-mpm.cmd' ($taskBase + '\run-frozen-joss.lisp') ($taskBase + '\joss-serial-before-config.json') ($taskBase + '\joss-serial-before') *> ($taskBase + '\joss-serial-before.log')
  $nativeExit = $LASTEXITCODE
  @{ startedUtc=$started; endedUtc=[DateTime]::UtcNow.ToString('o'); exitCode=$nativeExit; workers=1; openblasThreads=1; ompThreads=1; originalCommit='c749d32' } | ConvertTo-Json | Set-Content -LiteralPath ($taskBase + '\joss-serial-before-status.json') -Encoding utf8
  exit $nativeExit
} catch {
  @{ startedUtc=$started; endedUtc=[DateTime]::UtcNow.ToString('o'); exitCode=-1; error=$_.Exception.Message } | ConvertTo-Json | Set-Content -LiteralPath ($taskBase + '\joss-serial-before-status.json') -Encoding utf8
  exit 1
}
