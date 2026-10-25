$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$taskRoot = 'D:\MPM'
Set-Location -LiteralPath $taskRoot
$taskCommit = 'ac767e10e2856195aab4c51fade2d11c6cf70c61'
if ((git rev-parse HEAD).Trim() -ne $taskCommit) { throw 'Root-authorized source checkpoint changed' }
$taskBase = Join-Path $taskRoot 'output/mc-composite-apex-2026-10-25'
New-Item -ItemType Directory -Path $taskBase -Force | Out-Null
$taskLauncher = Join-Path $taskRoot 'windows/cl-mpm.cmd'
$taskPython = Join-Path $taskRoot 'toolchain/analysis-venv/Scripts/python.exe'
$taskVerifier = Join-Path $taskRoot '.tmp/verify-mc-default-compatibility.py'
$taskCompare = Join-Path $taskRoot '.tmp/compare-mc-default-hook-output.py'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'

function Invoke-TaskDefaultControl([string]$Name, [string]$Driver, [string]$Kind, [string[]]$ExtraArguments) {
  $taskDirectory = Join-Path $taskBase $Name
  $taskCommandPath = $taskDirectory + '-command.json'
  if ((Test-Path -LiteralPath $taskDirectory) -or (Test-Path -LiteralPath $taskCommandPath)) { throw ('Refuse repeated attempt '+$Name) }
  $taskArgs = @($Driver, $taskDirectory) + $ExtraArguments
  [ordered]@{
    sourceCommit=$taskCommit;startedUtc=[DateTime]::UtcNow.ToString('o');workingDirectory=$taskRoot
    executable=$taskLauncher;arguments=$taskArgs;kind=$Kind
    orchestratorSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    driverSha256=(Get-FileHash -LiteralPath $Driver -Algorithm SHA256).Hash
    strictProjectorSha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'materials/models/plastic/mohr-coulomb-evolution/projection.lisp') -Algorithm SHA256).Hash
    scope='FIRST authorized default-compatibility invocation; fresh frozen runtime; no full slope or old capsule'
  } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskCommandPath -Encoding utf8
  & $taskLauncher @taskArgs *> ($taskDirectory + '.log')
  $taskExit = $LASTEXITCODE
  [ordered]@{exitCode=$taskExit;finishedUtc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath ($taskDirectory + '-exit.json') -Encoding utf8
  if ($taskExit -ne 0) { throw ('Native control failed; no repeat: '+$Name+' exit '+$taskExit) }
  [ordered]@{command=@($taskPython,$taskVerifier,'--run',$taskDirectory,'--kind',$Kind);startedUtc=[DateTime]::UtcNow.ToString('o');verifierSha256=(Get-FileHash -LiteralPath $taskVerifier -Algorithm SHA256).Hash} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath ($taskDirectory+'-verification-command.json') -Encoding utf8
  & $taskPython $taskVerifier --run $taskDirectory --kind $Kind *> ($taskDirectory+'-verification.log')
  $taskVerifyExit=$LASTEXITCODE
  [ordered]@{exitCode=$taskVerifyExit;finishedUtc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath ($taskDirectory+'-verification-exit.json') -Encoding utf8
  if ($taskVerifyExit -ne 0) { throw ('Saved source/runtime gate failed; stop before next native invocation: '+$Name) }
  Write-Output ($Name+' native0/source verification0')
}

Invoke-TaskDefaultControl 'default-strict34-001' (Join-Path $taskRoot '.tmp/run-frozen-mc-regression.lisp') 'strict34' @()
Invoke-TaskDefaultControl 'default-output-001' (Join-Path $taskRoot 'tests/benchmarks/gravity-slope-controls.lisp') 'output' @('output')
$taskOutput = Join-Path $taskBase 'default-output-001'
[ordered]@{command=@($taskPython,$taskCompare,'--new-run',$taskOutput);startedUtc=[DateTime]::UtcNow.ToString('o');scriptSha256=(Get-FileHash -LiteralPath $taskCompare -Algorithm SHA256).Hash;scope='Five existing output files; no numerical execution'} |
  ConvertTo-Json -Depth 4 | Set-Content -LiteralPath ($taskOutput+'-comparison-command.json') -Encoding utf8
& $taskPython $taskCompare --new-run $taskOutput *> ($taskOutput+'-comparison.log')
$taskComparisonExit=$LASTEXITCODE
[ordered]@{exitCode=$taskComparisonExit;finishedUtc=[DateTime]::UtcNow.ToString('o')} |
  ConvertTo-Json | Set-Content -LiteralPath ($taskOutput+'-comparison-exit.json') -Encoding utf8
if ($taskComparisonExit -ne 0) { throw 'Saved exact-byte comparison failed; no numerical rerun' }
Write-Output 'Default compatibility native and exact byte gates complete'
