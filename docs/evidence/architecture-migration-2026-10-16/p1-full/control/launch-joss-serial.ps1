$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:\MPM'
$taskRoot = 'D:\MPM\output\architecture-migration-2026-10-16\p1-full'
$taskName = 'joss-serial'
$taskOutput = Join-Path $taskRoot $taskName
if (Test-Path -LiteralPath $taskOutput) { throw 'Refusing duplicate native run/output' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$taskStarted = [DateTime]::UtcNow.ToString('o')
$taskCommit = git rev-parse HEAD
$record = [ordered]@{ startedUtc=$taskStarted; sourceCommitAtLaunch=$taskCommit; case='tests\cases\joss-serial-regression.lisp'; wrapperPid=$PID; openblasThreads=1; ompThreads=1 }
$record | ConvertTo-Json | Set-Content -LiteralPath ($taskOutput + '-launch.json') -Encoding utf8
try {
  & 'D:\MPM\windows\cl-mpm.cmd' 'scripts\run-case.lisp' 'tests\cases\joss-serial-regression.lisp' $taskOutput *> ($taskOutput + '.log')
  $record.nativeExitCode = $LASTEXITCODE
  $record.nativeEndedUtc = [DateTime]::UtcNow.ToString('o')
  $record.exitCode = $record.nativeExitCode
  $record | ConvertTo-Json | Set-Content -LiteralPath ($taskOutput + '-status.json') -Encoding utf8
  if ($record.nativeExitCode -eq 0) {
    & 'D:\MPM\toolchain\analysis-venv\Scripts\python.exe' 'scripts\compare-framework-runs.py' '--baseline' 'D:\MPM\output\framework-refactor-2026-10-15\joss-serial-after' '--candidate' $taskOutput '--output' ($taskOutput + '-comparison.json') *> ($taskOutput + '-comparison.log')
    $record.comparisonExitCode = $LASTEXITCODE
    if ($taskName -ne 'joss-serial') {
      & 'D:\MPM\toolchain\analysis-venv\Scripts\python.exe' 'scripts\audit-triaxial.py' '--run-dir' $taskOutput *> ($taskOutput + '-audit.log')
      $record.auditExitCode = $LASTEXITCODE
    }
    $record.postprocessingEndedUtc = [DateTime]::UtcNow.ToString('o')
    $record | ConvertTo-Json | Set-Content -LiteralPath ($taskOutput + '-status.json') -Encoding utf8
  }
  exit $record.nativeExitCode
} catch {
  $record.error = $_.Exception.Message
  if (-not $record.Contains('nativeExitCode')) { $record.exitCode = -1 }
  $record | ConvertTo-Json | Set-Content -LiteralPath ($taskOutput + '-status.json') -Encoding utf8
  exit 1
}
