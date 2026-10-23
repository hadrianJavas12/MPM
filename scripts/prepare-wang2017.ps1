param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $taskRepo
$taskOutput = if ([IO.Path]::IsPathRooted($OutputDirectory)) {
  [IO.Path]::GetFullPath($OutputDirectory)
} else { [IO.Path]::GetFullPath((Join-Path $taskRepo $OutputDirectory)) }
$taskOutputRoot = [IO.Path]::GetFullPath((Join-Path $taskRepo 'output')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskOutputRoot,[StringComparison]::OrdinalIgnoreCase)) {
  throw 'Use a fresh output subdirectory inside this workspace.'
}
if (Test-Path -LiteralPath $taskOutput) { throw 'Preparation output must be fresh.' }
New-Item -ItemType Directory -Path $taskOutput | Out-Null
$taskStatus = [ordered]@{sourceCommit=(git rev-parse HEAD).Trim();startedUtc=[DateTime]::UtcNow.ToString('o')
  scope='Native case/material preparation only';physicalUpdates=0;status='PREPARING'}
$taskStatusPath = Join-Path $taskOutput 'preparation-status.json'
try {
  & (Join-Path $taskRepo 'windows/cl-mpm.cmd') 'tests/benchmarks/wang2017-reference-preparation.lisp' `
    (Join-Path $taskOutput 'native-inputs.json') *> (Join-Path $taskOutput 'native-inputs.log')
  $taskStatus.nativeExitCode=$LASTEXITCODE
  if ($LASTEXITCODE -ne 0) { throw 'Native input preparation failed; see retained log.' }
  & (Join-Path $taskRepo 'toolchain/analysis-venv/Scripts/python.exe') 'scripts/prepare-wang2017.py' `
    --native-export (Join-Path $taskOutput 'native-inputs.json') `
    --output (Join-Path $taskOutput 'preparation-report.json') *> (Join-Path $taskOutput 'preparation-report.log')
  $taskStatus.auditExitCode=$LASTEXITCODE
  if ($LASTEXITCODE -ne 0) { throw 'Paper-input audit failed; see retained report/log.' }
  $taskStatus.status='PREPARED_WITH_OPEN_GATES'
} catch {
  $taskStatus.status='PREPARATION_FAILED'
  $taskStatus.error=$_.Exception.Message
  throw
} finally {
  $taskStatus.endedUtc=[DateTime]::UtcNow.ToString('o')
  $taskStatus | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStatusPath -Encoding utf8
}
