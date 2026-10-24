$ErrorActionPreference='Stop'
Set-Location -LiteralPath 'D:\MPM'
$taskDirectory='output/wang2017-soil2-2026-10-24/apex-integration-002'
if(Test-Path -LiteralPath $taskDirectory){throw 'Fresh attempt required.'}
New-Item -ItemType Directory -Path $taskDirectory | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $taskDirectory 'executed-wrapper.ps1')
$taskStatus=[ordered]@{status='RUNNING';startedUtc=[DateTime]::UtcNow.ToString('o');tests=@();scope='Only missing strict/apex output gates after corrected wrapper argument array; no full slope'}
function Save-TaskStatus {$taskStatus|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $taskDirectory 'status.json') -Encoding utf8}
Save-TaskStatus
try {
 foreach($taskVariant in @('strict','composite-apex')) {
  $taskOutput=Join-Path $taskDirectory $taskVariant
  $taskArguments=@('tests/benchmarks/wang2017-soil2-output.lisp',$taskOutput,$taskVariant)
  if($taskArguments.Count -ne 3){throw 'Invalid argument count.'}
  & .\windows\cl-mpm.cmd @taskArguments *> (Join-Path $taskDirectory ($taskVariant+'.log'))
  $taskCode=$LASTEXITCODE
  $taskStatus.tests+=@{variant=$taskVariant;exitCode=$taskCode;arguments=$taskArguments}
  Save-TaskStatus
  if($taskCode -ne 0){throw ('Native output control failed: '+$taskVariant)}
  $taskResult=Get-Content (Join-Path $taskOutput 'result.json') -Raw|ConvertFrom-Json
  if(-not $taskResult.passed -or $taskResult.passedCount -ne 8 -or $taskResult.materialVariant -ne $taskVariant -or $taskResult.physicalUpdatesExecuted -ne 2 -or $taskResult.actualSavedStates -ne 2){throw 'Output gate scope/count/variant mismatch.'}
 }
 $taskStatus.status='PASS'
}catch{$taskStatus.status='FAILED';$taskStatus.error=$_.Exception.Message}
finally{$taskStatus.endedUtc=[DateTime]::UtcNow.ToString('o');Save-TaskStatus}
Get-Content (Join-Path $taskDirectory 'status.json')
if($taskStatus.status -ne 'PASS'){exit 1}
