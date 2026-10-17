param([Parameter(Mandatory=$true)][string]$ExecutionCheckpoint)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/MPM'
$taskRoot = 'D:/MPM/output/architecture-migration-2026-10-16/joss-bounded'
$taskPrefix = Join-Path $taskRoot 'before-003'
if (Test-Path -LiteralPath ($taskPrefix + '-launch.json')) { throw 'Refusing duplicate baseline launch' }
if (Test-Path -LiteralPath $taskPrefix) { throw 'Baseline output must be fresh/nonexistent' }
& 'D:/MPM/toolchain/analysis-venv/Scripts/python.exe' 'D:/MPM/scripts/prepare-joss-bounded-baseline.py' --verify-retry --attempt before-003
if ($LASTEXITCODE -ne 0) { throw 'Prepared baseline input verification failed' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:CL_MPM_REFERENCE_PNG = '0'
$taskRecord = [ordered]@{
  startedUtc=[DateTime]::UtcNow.ToString('o'); bootstrapRepositoryCheckpoint=$ExecutionCheckpoint
  numericalSourceBaselineCommit='a99a4e1d1a8deb17483230ee59d53c07f4a26822'
  sourceIdentity='Original manifest-bound payload copied into original-root, then old CLI re-copies/guards/compiles it in this fresh run'
  caseCommitReported='9568b8e'; workers=1; requestedPhysicalTimeS=4; frameCap=10
  openblasThreads=1; ompThreads=1; pngEnabled=$false; wrapperPid=$PID
  scope='Fresh bounded serial initiation control; not full collapse/run-out, not restarted cancelled run'
}
$taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-launch.json') -Encoding utf8
try {
  $taskCommand = 'call "D:/MPM/windows/cl-mpm.cmd" "' + (Join-Path $taskRoot 'before-003-bootstrap.lisp') + '" "' + (Join-Path $taskRoot 'original-root') + '" "' + (Join-Path $taskRoot 'joss-serial-integration.lisp') + '" "' + $taskPrefix + '"'
  $taskNative = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput ($taskPrefix + '.stdout.log') -RedirectStandardError ($taskPrefix + '.stderr.log')
  $taskRecord.nativeExitCode=$taskNative.ExitCode
  $taskRecord.stdoutPath=$taskPrefix + '.stdout.log'
  $taskRecord.stderrPath=$taskPrefix + '.stderr.log'
  $taskMetadataPath = Join-Path $taskPrefix 'reference-metadata.json'
  if (Test-Path -LiteralPath $taskMetadataPath) {
    $taskMetadata = Get-Content -Raw -LiteralPath $taskMetadataPath | ConvertFrom-Json
    $taskRecord.simulationComplete=$taskMetadata.complete
    $taskRecord.physicalTime=$taskMetadata.physicalTime
    $taskRecord.termination=$taskMetadata.termination
  }
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  exit $taskRecord.nativeExitCode
} catch {
  $taskRecord.wrapperError=$_.Exception.Message
  $taskRecord.nativeExitCode=$null
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  throw
}
