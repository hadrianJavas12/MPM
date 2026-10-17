param([Parameter(Mandatory=$true)][string]$Name,[Parameter(Mandatory=$true)][string[]]$ScriptArguments)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/MPM'
$taskEvidenceRoot = 'D:/MPM/output/architecture-migration-2026-10-16/p4-e'
$taskPrefix = Join-Path $taskEvidenceRoot $Name
if (Test-Path -LiteralPath ($taskPrefix + '-launch.json')) { throw 'Refusing duplicate attempt name' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$taskCommit = (git rev-parse HEAD).Trim()
$taskFiles = @('cl-mpm.asd','scripts/run-case.lisp','scripts/lisp/native-source-snapshot.lisp','tests/case-snapshot-contracts.lisp','tests/native-snapshot-contracts.lisp','tests/material-diagnostics.lisp','tests/p4-standalone-triaxial-compat.lisp','calibration/triaxial.lisp','tests/cases/cliff-mc-integration.lisp','scripts/joss-reference-smoke.lisp','tests/material-ownership-compat.lisp','tests/p4-orchestration-compat.lisp','tests/framework-components.lisp','tests/config-contracts.lisp','docs/architecture/P4_ORCHESTRATION_MIGRATION.json','tests/cases/triaxial-integration.lisp','config/git-commit-version.txt','libs/kirchoff.dll')
foreach ($taskTree in @('src','materials','framework','scenarios','studio/lisp')) {
  if (Test-Path -LiteralPath $taskTree) {
    $taskFiles += Get-ChildItem -LiteralPath $taskTree -Recurse -File | Where-Object { $_.Extension -in @('.lisp','.asd') } | ForEach-Object { $_.FullName.Substring(7).Replace('\','/') }
  }
}
foreach ($taskOptional in @('cl-mpm-simulation.asd','cl-mpm-framework.asd','cl-mpm-materials.asd')) { if (Test-Path -LiteralPath $taskOptional) { $taskFiles += $taskOptional } }
$taskSources = foreach ($taskFile in ($taskFiles | Sort-Object -Unique)) { $taskInfo = Get-Item -LiteralPath $taskFile; [ordered]@{ path=$taskFile; bytes=$taskInfo.Length; sha256=(Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant() } }
$taskSources | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($taskPrefix + '-source-sha256.json') -Encoding utf8
$taskRecord = [ordered]@{ startedUtc=[DateTime]::UtcNow.ToString('o'); sourceCommitAtLaunch=$taskCommit; arguments=$ScriptArguments; wrapperPid=$PID; openblasThreads=1; ompThreads=1; scope='Fresh native Windows attempt; direct unit suites use captured live source hashes; CLI snapshots additionally record copied sources and loaded DLL' }
$taskRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($taskPrefix + '-launch.json') -Encoding utf8
try {
  & 'D:/MPM/windows/cl-mpm.cmd' @ScriptArguments *> ($taskPrefix + '.log')
  $taskRecord.exitCode = $LASTEXITCODE
  $taskRecord.endedUtc = [DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  Get-Content -LiteralPath ($taskPrefix + '.log') -Tail 15
  exit $taskRecord.exitCode
} catch {
  $taskRecord.error = $_.Exception.Message
  $taskRecord.exitCode = -1
  $taskRecord.endedUtc = [DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  throw
}





