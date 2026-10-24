$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:\MPM'
$taskDirectory = 'output/wang2017-soil2-2026-10-24/residual-integration-001'
if (Test-Path -LiteralPath $taskDirectory) { throw 'Fresh integration attempt required.' }
New-Item -ItemType Directory -Path $taskDirectory | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $taskDirectory 'executed-wrapper.ps1')
$taskStatus = [ordered]@{status='RUNNING';startedUtc=[DateTime]::UtcNow.ToString('o');sourceCommit=(git rev-parse HEAD).Trim();tests=@();scope='New input, relevant strict native regression, and two-update new output gate; no full slope'}
$taskStatusPath = Join-Path $taskDirectory 'status.json'
function Save-TaskStatus { $taskStatus | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $taskStatusPath -Encoding utf8 }
$taskInputReport = Join-Path $taskDirectory 'input-report.json'
$taskNativeDirectory = Join-Path $taskDirectory 'strict-native'
$taskOutputDirectory = Join-Path $taskDirectory 'residual-output'
$taskChecks = @(
  @{name='inputs';script='.tmp/prepare-residual-scope-inputs.lisp';arguments=@($taskInputReport)},
  @{name='strict-native';script='tests/materials/wang2017-native.lisp';arguments=@($taskNativeDirectory)},
  @{name='residual-output';script='tests/benchmarks/wang2017-soil2-output.lisp';arguments=@($taskOutputDirectory,'composite-apex-residual')}
)
Save-TaskStatus
try {
  foreach ($taskCheck in $taskChecks) {
    Copy-Item -LiteralPath $taskCheck.script -Destination (Join-Path $taskDirectory ($taskCheck.name+'-executed.lisp'))
    $taskArguments = @($taskCheck.script)+$taskCheck.arguments
    & ./windows/cl-mpm.cmd @taskArguments *> (Join-Path $taskDirectory ($taskCheck.name+'.log'))
    $taskCode=$LASTEXITCODE
    $taskStatus.tests += @{name=$taskCheck.name;exitCode=$taskCode;arguments=$taskArguments}
    Save-TaskStatus
    if ($taskCode -ne 0) { throw ('Failed '+$taskCheck.name+'; retain failure and inspect before retry.') }
  }
  $taskStatus.status='PASS'
} catch {
  $taskStatus.status='FAILED';$taskStatus.error=$_.Exception.Message
} finally {
  $taskStatus.endedUtc=[DateTime]::UtcNow.ToString('o');Save-TaskStatus
}
Get-Content -LiteralPath $taskStatusPath
if ($taskStatus.status -ne 'PASS') { exit 1 }
