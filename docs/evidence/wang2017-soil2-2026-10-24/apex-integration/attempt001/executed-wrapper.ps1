$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:\MPM'
$taskDirectory = 'output/wang2017-soil2-2026-10-24/apex-integration-001'
$taskStatusPath = Join-Path $taskDirectory 'regression-status.json'
if (Test-Path -LiteralPath $taskStatusPath) { throw 'Existing regression attempt; do not duplicate.' }
$taskStatus = [ordered]@{status='RUNNING';startedUtc=[DateTime]::UtcNow.ToString('o');sourceCommit=(git rev-parse HEAD).Trim();tests=@();scope='Native regression and two-step integration gates; no full slope'}
function Save-TaskStatus { $taskStatus | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $taskStatusPath -Encoding utf8 }
Save-TaskStatus
$taskTests = @(
  @{name='strict-point';script='tests/materials/wang2017-projection.lisp';arguments=@($taskDirectory+'/strict-point.json')},
  @{name='old-mc';script='tests/materials/mc-evolution-points.lisp';arguments=@()},
  @{name='framework';script='tests/framework-components.lisp';arguments=@()},
  @{name='strict-native';script='tests/materials/wang2017-native.lisp';arguments=@($taskDirectory+'/strict-native')},
  @{name='strict-inputs';script='tests/benchmarks/wang2017-soil2-inputs.lisp';arguments=@($taskDirectory+'/strict-inputs.json')},
  @{name='strict-output';script='tests/benchmarks/wang2017-soil2-output.lisp';arguments=@($taskDirectory+'/strict-output','strict')},
  @{name='apex-output';script='tests/benchmarks/wang2017-soil2-output.lisp';arguments=@($taskDirectory+'/apex-output','composite-apex')}
)
try {
  foreach ($taskTest in $taskTests) {
    $taskLog=Join-Path $taskDirectory ($taskTest.name+'.log')
    Copy-Item -LiteralPath $taskTest.script -Destination (Join-Path $taskDirectory ($taskTest.name+'-executed-test.lisp'))
    $taskArguments=@($taskTest.script)+$taskTest.arguments
    & .\windows\cl-mpm.cmd @taskArguments *> $taskLog
    $taskCode=$LASTEXITCODE
    $taskStatus.tests+=@{name=$taskTest.name;exitCode=$taskCode;log=$taskLog}
    Save-TaskStatus
    if ($taskCode -ne 0) { throw ('Failed '+$taskTest.name+'; inspect retained log, do not repeat blindly.') }
  }
  $taskStatus.status='PASS'
} catch {
  $taskStatus.status='FAILED'
  $taskStatus.error=$_.Exception.Message
} finally {
  $taskStatus.endedUtc=[DateTime]::UtcNow.ToString('o')
  Save-TaskStatus
}
Get-Content -LiteralPath $taskStatusPath
if ($taskStatus.status -ne 'PASS') { exit 1 }
