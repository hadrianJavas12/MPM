param(
  [Parameter(Mandatory=$true)][ValidateSet('Launch','Verify')][string]$Phase,
  [string]$OutputDirectory='output/wang2017-reference-2026-10-23/detached-launch-controls-001'
)
$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOutput=[IO.Path]::GetFullPath((Join-Path $taskRepo $OutputDirectory))
$taskControl=Join-Path $taskOutput 'fixture run with spaces'
$taskLaunch=$taskControl+'-detached'
$taskState=Join-Path $taskOutput 'controller.json'
function Assert-Task([bool]$Condition,[string]$Message) { if (-not $Condition) { throw $Message } }
if ($Phase -eq 'Launch') {
  Assert-Task (-not (Test-Path -LiteralPath $taskOutput)) 'Control output must be fresh.'
  New-Item -ItemType Directory -Path $taskOutput | Out-Null
  $taskCaller=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
  & (Join-Path $taskRepo 'scripts/start-wang2017-detached.ps1') -OutputDirectory $taskControl -LaunchControlFixture |
    Set-Content -LiteralPath (Join-Path $taskOutput 'launcher.stdout.json') -Encoding utf8
  [ordered]@{ controllerPid=$PID; creationUtc=$taskCaller.CreationDate.ToUniversalTime().ToString('o'); sessionId=$taskCaller.SessionId; launchDirectory=$taskLaunch } |
    ConvertTo-Json | Set-Content -LiteralPath $taskState -Encoding utf8
  Write-Output 'Launch phase complete. Let this command process exit before invoking Verify in a separate command.'
  exit 0
}
$taskStateValue=Get-Content -LiteralPath $taskState -Raw | ConvertFrom-Json
$taskPrevious=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskStateValue.controllerPid)
$taskPreviousStillSame=$taskPrevious -and ($taskPrevious.CreationDate.ToUniversalTime().ToString('o') -eq $taskStateValue.creationUtc)
Assert-Task (-not $taskPreviousStillSame) 'Original source command has not exited; Verify must run in a separate command.'
$taskProof=Get-Content -LiteralPath (Join-Path $taskLaunch 'launch-proof.json') -Raw | ConvertFrom-Json
$taskWorker=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskProof.workerProcessId)
Assert-Task ($taskProof.returnValue -eq 0 -and $taskProof.startupObserved) 'CIM creation/startup failed.'
Assert-Task ($null -ne $taskWorker) 'Detached worker did not survive the source command.'
Assert-Task ($taskWorker.ParentProcessId -ne $taskStateValue.controllerPid) 'Worker retained direct caller parentage.'
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
while (-not (Test-Path -LiteralPath (Join-Path $taskLaunch 'fixture-start.json')) -and $taskTimer.Elapsed.TotalSeconds -lt 10) { Start-Sleep -Milliseconds 200 }
Assert-Task (Test-Path -LiteralPath (Join-Path $taskLaunch 'fixture-start.json')) 'Fixture startup missing.'
New-Item -ItemType File -Path (Join-Path $taskLaunch 'fixture-release') | Out-Null
$taskTimer.Restart()
while (-not (Test-Path -LiteralPath (Join-Path $taskLaunch 'worker-exit.json')) -and $taskTimer.Elapsed.TotalSeconds -lt 15) { Start-Sleep -Milliseconds 200 }
Assert-Task (Test-Path -LiteralPath (Join-Path $taskLaunch 'worker-exit.json')) 'Bounded fixture exit proof missing.'
$taskExit=Get-Content -LiteralPath (Join-Path $taskLaunch 'worker-exit.json') -Raw | ConvertFrom-Json
Assert-Task ($taskExit.exitCode -eq 7 -and $taskExit.status -eq 'WORKER_EXITED') 'Fixture exit7 not captured.'
Assert-Task ((Get-Content -LiteralPath (Join-Path $taskLaunch 'wrapper.stdout.log') -Raw).Contains('fixture stdout')) 'Stdout not captured.'
Assert-Task ((Get-Content -LiteralPath (Join-Path $taskLaunch 'wrapper.stderr.log') -Raw).Contains('fixture stderr')) 'Stderr not captured.'
$taskDuplicateRejected=$false
try { & (Join-Path $taskRepo 'scripts/start-wang2017-detached.ps1') -OutputDirectory $taskControl -LaunchControlFixture | Out-Null } catch { $taskDuplicateRejected=$_.Exception.Message.Contains('Refusing duplicate attempt') }
Assert-Task $taskDuplicateRejected 'Duplicate attempt was not rejected.'
$taskBoundaryRejected=$false
try { & (Join-Path $taskRepo 'scripts/start-wang2017-detached.ps1') -OutputDirectory (Join-Path $taskRepo '.tmp/invalid-detached') -LaunchControlFixture | Out-Null } catch { $taskBoundaryRejected=$_.Exception.Message.Contains('fresh subdirectory') }
Assert-Task $taskBoundaryRejected 'Outside-output path was not rejected.'
[ordered]@{
  status='PASS'; controls=9; finishedUtc=[DateTime]::UtcNow.ToString('o'); physicalUpdates=0
  sourceCommandExited=$true; workerSurvived=$true; returnValue=$taskProof.returnValue; capturedExitCode=$taskExit.exitCode
  callerSessionId=$taskStateValue.sessionId; workerSessionId=$taskProof.workerSessionId; workerParentProcessId=$taskWorker.ParentProcessId
  scope='Trusted tiny fixture only, with spaced paths, no MPM run. Does not prove survival of logoff, reboot, sleep or arbitrary provider job restrictions.'
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOutput 'result.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskOutput 'result.json')
