$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/MPM'
$taskRoot = 'D:/MPM/output/architecture-migration-2026-10-16/joss-bounded'
$taskPrefix = Join-Path $taskRoot 'after-001'
if (Test-Path -LiteralPath ($taskPrefix + '-launch.json')) { throw 'Refusing duplicate candidate launch' }
if (Test-Path -LiteralPath $taskPrefix) { throw 'Candidate output must be fresh/nonexistent' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:CL_MPM_REFERENCE_PNG = '0'
$taskCommit = (git rev-parse HEAD).Trim()
$taskRecord = [ordered]@{
  startedUtc=[DateTime]::UtcNow.ToString('o')
  sourceCommitAtLaunch=$taskCommit
  case='tests/cases/joss-serial-integration.lisp'
  workers=1
  requestedPhysicalTimeS=4
  frameCap=10
  openblasThreads=1
  ompThreads=1
  pngEnabled=$false
  wrapperPid=$PID
  scope='Fresh bounded serial initiation control on final canonical root ASDF layout; compared strictly against completed before-003 pre-P2 baseline. Not full 40 s collapse/run-out.'
}
$taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-launch.json') -Encoding utf8
try {
  $taskCommand = 'call "D:/MPM/windows/cl-mpm.cmd" "scripts/run-case.lisp" "tests/cases/joss-serial-integration.lisp" "' + $taskPrefix + '"'
  $taskNative = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput ($taskPrefix + '.stdout.log') -RedirectStandardError ($taskPrefix + '.stderr.log')
  $taskRecord.nativeExitCode = $taskNative.ExitCode
  $taskRecord.stdoutPath = $taskPrefix + '.stdout.log'
  $taskRecord.stderrPath = $taskPrefix + '.stderr.log'
  $taskMetadataPath = Join-Path $taskPrefix 'reference-metadata.json'
  if (Test-Path -LiteralPath $taskMetadataPath) {
    $taskMetadata = Get-Content -Raw -LiteralPath $taskMetadataPath | ConvertFrom-Json
    $taskRecord.simulationComplete = $taskMetadata.complete
    $taskRecord.physicalTime = $taskMetadata.physicalTime
    $taskRecord.termination = $taskMetadata.termination
  }
  $taskRecord.nativeEndedUtc = [DateTime]::UtcNow.ToString('o')
  $taskRecord.exitCode = $taskRecord.nativeExitCode
  $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  if ($taskRecord.nativeExitCode -eq 0) {
    if ($taskRecord.simulationComplete -ne $true) { throw 'Native exit zero without complete reference-metadata.json' }
    & 'D:/MPM/toolchain/analysis-venv/Scripts/python.exe' 'scripts/compare-framework-runs.py' '--baseline' (Join-Path $taskRoot 'before-003') '--candidate' $taskPrefix '--output' (Join-Path $taskRoot 'joss-bounded-comparison.json') *> (Join-Path $taskRoot 'joss-bounded-comparison.log')
    $taskRecord.comparisonExitCode = $LASTEXITCODE
    if ($taskRecord.comparisonExitCode -ne 0) { $taskRecord.exitCode = $taskRecord.comparisonExitCode }
    $taskRecord.endedUtc = [DateTime]::UtcNow.ToString('o')
    $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  }
  exit $taskRecord.exitCode
} catch {
  $taskRecord.wrapperError = $_.Exception.Message
  if (-not $taskRecord.Contains('nativeExitCode')) { $taskRecord.nativeExitCode = $null; $taskRecord.exitCode = -1 }
  $taskRecord.endedUtc = [DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  throw
}
