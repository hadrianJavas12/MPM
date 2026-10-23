param([string]$OutputDirectory='output/wang2017-reference-2026-10-23/monitor-hardening-001')
$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOutput=[IO.Path]::GetFullPath((Join-Path $taskRepo $OutputDirectory))
if (-not $IsWindows) { throw 'These process-supervision controls require Windows PowerShell7.' }
if (Test-Path -LiteralPath $taskOutput) { throw 'Fresh control output required.' }
$taskOutputRoot=[IO.Path]::GetFullPath((Join-Path $taskRepo 'output')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskOutputRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Control output must remain under workspace/output.' }
$taskFixture=Join-Path $taskOutput 'fixture'
foreach ($taskPart in @('scripts','windows','cases','output')) { New-Item -ItemType Directory -Path (Join-Path $taskFixture $taskPart) -Force | Out-Null }
Copy-Item -LiteralPath (Join-Path $taskRepo 'scripts/run-wang2017-trial.ps1') -Destination (Join-Path $taskFixture 'scripts/run-wang2017-trial.ps1')
foreach ($taskTool in @('plot-wang2017-descent.py','plot_m5_cliff_comparison.py','collect-wang2017-evidence.py')) {
  '# Unexecuted hash-only fixture; no postprocessing expected.' | Set-Content -LiteralPath (Join-Path $taskFixture ('scripts/'+$taskTool))
}
'; No MPM is loaded by the mock Windows launcher.' | Set-Content -LiteralPath (Join-Path $taskFixture 'scripts/run-case.lisp')
foreach ($taskMode in @('normal','timeout','attach')) { $taskMode | Set-Content -LiteralPath (Join-Path $taskFixture ('cases/'+$taskMode+'.lisp')) }
$taskSbcl=(Get-Command sbcl -ErrorAction Stop).Source
@"
@echo off
"$taskSbcl" --noinform --no-userinit --disable-debugger --script "%~dp0fixture.lisp" "%~2" "%~3"
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath (Join-Path $taskFixture 'windows/cl-mpm.cmd') -Encoding ascii
@'
;;;; Process-control fixture only: no Quicklisp, ASDF, project systems or MPM steps.
(let* ((case-file (second sb-ext:*posix-argv*))
       (output (third sb-ext:*posix-argv*))
       (mode (with-open-file (s case-file) (string-right-trim '(#\Return #\Newline) (read-line s))))
       (manifest (format nil "~A/manifest.json" output)))
  (ensure-directories-exist manifest)
  (flet ((progress (phase time updates)
           (with-open-file (s manifest :direction :output :if-exists :supersede)
             (format s "{\"status\":\"running\",\"complete\":false,\"phase\":\"~A\",\"timeS\":~F,\"settleUpdates\":25,\"loadingUpdates\":~D,\"gravityConverged\":true}" phase time updates))))
    (progress "gravity" 0.0 0)
    (format t "GRAVITY INITIAL; stdout intentionally does not report later progress.~%")
    (finish-output)
    (sleep 0.7)
    (progress "prescribed-descent" 1.2 123)
    (sleep (cond ((string= mode "timeout") 30) ((string= mode "attach") 8) (t 3)))
    (sb-ext:exit :code 7)))
'@ | Set-Content -LiteralPath (Join-Path $taskFixture 'windows/fixture.lisp') -Encoding ascii
$taskShell=(Get-Command pwsh -ErrorAction Stop).Source
$taskChecks=[Collections.Generic.List[object]]::new()
function Check-Task([string]$Name,[bool]$Passed) {
  $taskChecks.Add(@{name=$Name;passed=$Passed})
  if (-not $Passed) { throw ('Control failed: '+$Name) }
}
function Start-TaskMonitor([string]$Mode,[double]$Hours,[switch]$Attach) {
  $taskRun=Join-Path $taskFixture ('output/'+$Mode)
  $taskArguments=@('-NoProfile','-File',('"'+(Join-Path $taskFixture 'scripts/run-wang2017-trial.ps1')+'"'),
    '-OutputDirectory',('"'+$taskRun+'"'),'-Case',('cases/'+$Mode+'.lisp'),'-MaxWallHours',[string]$Hours,'-HeartbeatSeconds','0.2')
  if ($Attach) { $taskArguments+='-AttachRunning' }
  $taskSuffix=if ($Attach) {'-successor'} else {''}
  Start-Process -FilePath $taskShell -ArgumentList $taskArguments -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput ($taskRun+$taskSuffix+'-wrapper.stdout.log') -RedirectStandardError ($taskRun+$taskSuffix+'-wrapper.stderr.log')
}
function Read-TaskStatus([string]$Mode) {
  $taskPath=Join-Path $taskFixture ('output/'+$Mode+'-status.json')
  if (Test-Path -LiteralPath $taskPath) { try { return Get-Content -LiteralPath $taskPath -Raw | ConvertFrom-Json } catch {} }
  return $null
}
function Wait-TaskProgress([string]$Mode,[Diagnostics.Process]$Monitor) {
  $taskWatch=[Diagnostics.Stopwatch]::StartNew()
  while ($taskWatch.Elapsed.TotalSeconds -lt 12 -and -not $Monitor.HasExited) {
    $taskStatus=Read-TaskStatus $Mode
    if ($taskStatus.progress.phase -eq 'prescribed-descent' -and $null -ne $taskStatus.processIdentity.sbcl) { return $taskStatus }
    Start-Sleep -Milliseconds 100
  }
  throw ('No live manifest heartbeat for '+$Mode)
}
function Check-TaskIdentities($Status) {
  foreach ($taskRole in @('wrapper','nativeCommand','sbcl')) {
    $taskIdentity=$Status.processIdentity.$taskRole
    $taskLive=Get-Process -Id $taskIdentity.pid -ErrorAction Stop
    Check-Task ($taskRole+' PID/creation/session identity') (([DateTimeOffset]$taskIdentity.createdUtc) -eq ([DateTimeOffset]$taskLive.StartTime.ToUniversalTime()) -and $taskIdentity.sessionId -eq $taskLive.SessionId)
  }
}
$taskInvalid=Start-TaskMonitor 'invalid-budget' 73
if (-not $taskInvalid.WaitForExit(10000)) { throw 'Invalid-budget fixture did not reject.' }
$taskInvalid.Refresh()
Check-Task 'Wall budget above72h rejects before launch' ($taskInvalid.ExitCode -ne 0 -and -not (Test-Path -LiteralPath (Join-Path $taskFixture 'output/invalid-budget-status.json')))
$taskInvalid=Start-TaskMonitor 'invalid-nan' ([double]::NaN)
if (-not $taskInvalid.WaitForExit(10000)) { throw 'Nonfinite-budget fixture did not reject.' }
$taskInvalid.Refresh()
Check-Task 'NaN wall budget rejects before launch' ($taskInvalid.ExitCode -ne 0 -and -not (Test-Path -LiteralPath (Join-Path $taskFixture 'output/invalid-nan-status.json')))
$taskNormal=Start-TaskMonitor 'normal' 0.01
$taskLiveStatus=Wait-TaskProgress 'normal' $taskNormal
$taskLiveStatus | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $taskOutput 'normal-live-heartbeat.json')
Check-TaskIdentities $taskLiveStatus
Check-Task 'Heartbeat observes manifest phase/time/counters independent of stale stdout' ($taskLiveStatus.progress.timeS -eq 1.2 -and $taskLiveStatus.progress.loadingUpdates -eq 123 -and $taskLiveStatus.progress.settleUpdates -eq 25 -and $taskLiveStatus.heartbeatSequence -ge 2 -and $taskLiveStatus.progress.stdout.bytes -gt 0)
if (-not $taskNormal.WaitForExit(15000)) { throw 'Normal fixture monitor did not terminate.' }
$taskNormal.Refresh();$taskStatus=Read-TaskStatus 'normal'
Check-Task 'Native exit7 survives wrapper and records incomplete manifest' ($taskNormal.ExitCode -eq 7 -and $taskStatus.nativeExitCode -eq 7 -and $taskStatus.status -eq 'FAILED_NATIVE' -and -not $taskStatus.nativeComplete)
$taskTimeout=Start-TaskMonitor 'timeout' 0.002
$null=Wait-TaskProgress 'timeout' $taskTimeout
if (-not $taskTimeout.WaitForExit(15000)) { throw 'Timeout fixture monitor did not terminate.' }
$taskTimeout.Refresh();$taskStatus=Read-TaskStatus 'timeout'
Check-Task 'Wall budget retains exit3 and STOPPED_WALL_BUDGET' ($taskTimeout.ExitCode -eq 3 -and $taskStatus.status -eq 'STOPPED_WALL_BUDGET' -and -not $taskStatus.nativeComplete -and $null -eq $taskStatus.nativeExitCode)
Check-Task 'Timeout stops fixture native command and SBCL tree' ($null -eq (Get-Process -Id $taskStatus.nativeCommandPid -ErrorAction SilentlyContinue) -and $null -eq (Get-Process -Id $taskStatus.processIdentity.sbcl.pid -ErrorAction SilentlyContinue))
$taskPredecessor=Start-TaskMonitor 'attach' 0.005
$taskBefore=Wait-TaskProgress 'attach' $taskPredecessor
$taskSuccessor=Start-TaskMonitor 'attach' 0.01 -Attach
$taskReadyPath=Join-Path $taskFixture ('output/attach-monitor-'+$taskSuccessor.Id+'-ready.json')
$taskWatch=[Diagnostics.Stopwatch]::StartNew()
while (-not (Test-Path -LiteralPath $taskReadyPath)) {
  if ($taskSuccessor.HasExited -or $taskWatch.Elapsed.TotalSeconds -gt 8) { throw 'Successor was not ready.' }
  Start-Sleep -Milliseconds 100
}
$taskReady=Get-Content -LiteralPath $taskReadyPath -Raw | ConvertFrom-Json
Check-Task 'READY file retains complete native process identities' ($taskReady.processIdentity.nativeCommand.pid -eq $taskBefore.nativeCommandPid -and $taskReady.processIdentity.sbcl.pid -eq $taskBefore.processIdentity.sbcl.pid -and $taskReady.processIdentity.wrapper.pid -eq $taskSuccessor.Id)
$taskGate=[Threading.EventWaitHandle]::OpenExisting($taskReady.activationEvent)
Stop-Process -Id $taskPredecessor.Id
$taskPredecessor.WaitForExit()
$null=$taskGate.Set();$taskGate.Dispose()
if (-not $taskSuccessor.WaitForExit(15000)) { throw 'Attached monitor did not finish.' }
$taskSuccessor.Refresh();$taskStatus=Read-TaskStatus 'attach'
Check-Task 'READY/event attachment preserves native identities, exit7 and extended budget' ($taskSuccessor.ExitCode -eq 7 -and $taskStatus.nativeExitCode -eq 7 -and $taskStatus.maxWallHours -eq 0.01 -and $taskStatus.originalMaxWallHours -eq 0.005 -and $taskStatus.nativeCommandPid -eq $taskBefore.nativeCommandPid -and $taskStatus.processIdentity.sbcl.createdUtc -eq $taskBefore.processIdentity.sbcl.createdUtc -and $taskStatus.processIdentity.sbcl.sessionId -eq $taskBefore.processIdentity.sbcl.sessionId -and $taskStatus.previousWrapperIdentity.pid -eq $taskPredecessor.Id -and $taskStatus.processIdentity.wrapper.pid -eq $taskSuccessor.Id)
$taskExecutedHash=(Get-FileHash -LiteralPath (Join-Path $taskFixture 'scripts/run-wang2017-trial.ps1')).Hash
Check-Task 'Executed wrapper copy matches repository source after controls' ($taskExecutedHash -eq (Get-FileHash -LiteralPath (Join-Path $taskRepo 'scripts/run-wang2017-trial.ps1')).Hash)
$taskResult=@{passed=$true;checks=$taskChecks;checkCount=$taskChecks.Count;physicalUpdates=0;scope='Windows monitor only; mock launcher and tiny standalone SBCL. No MPM or constitutive updates.';wrapperSha256=$taskExecutedHash;testSha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}
$taskResult | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $taskOutput 'result.json')
$taskResult | ConvertTo-Json -Depth 10
