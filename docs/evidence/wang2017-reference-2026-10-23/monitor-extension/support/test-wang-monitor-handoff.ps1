$ErrorActionPreference='Stop'
Set-Location D:\MPM
$taskRunRoot='D:\MPM\output\wang2017-reference-2026-10-23\monitor-handoff-test-003'
if(Test-Path ($taskRunRoot+'-status.json')) { throw 'Fresh fixture required' }
$taskShell=(Get-Command pwsh).Source
$taskSbcl=(Get-Process -Id 49524).Path
$taskOld=Start-Process $taskShell -ArgumentList @('-NoProfile','-File','D:\MPM\.tmp\test-wang-monitor-parent.ps1','-RunRoot',$taskRunRoot,'-SbclExe',('"'+$taskSbcl+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput ($taskRunRoot+'-old.stdout.log') -RedirectStandardError ($taskRunRoot+'-old.stderr.log')
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
while(-not (Test-Path ($taskRunRoot+'-status.json'))) { if($taskTimer.Elapsed.TotalSeconds -gt 6){throw 'Fixture startup timeout'}; Start-Sleep -Milliseconds 100 }
$taskNew=Start-Process $taskShell -ArgumentList @('-NoProfile','-File','D:\MPM\scripts\run-wang2017-trial.ps1','-OutputDirectory',$taskRunRoot,'-Case','.tmp/test-wang-monitor-child.lisp','-AttachRunning','-MaxWallHours','0.01') -WindowStyle Hidden -PassThru -RedirectStandardOutput ($taskRunRoot+'-new.stdout.log') -RedirectStandardError ($taskRunRoot+'-new.stderr.log')
$taskReadyPath=$taskRunRoot+'-monitor-'+$taskNew.Id+'-ready.json'
while(-not(Test-Path $taskReadyPath)) { if($taskNew.HasExited -or $taskTimer.Elapsed.TotalSeconds -gt 8) { throw 'Successor not ready before fixture deadline' }; Start-Sleep -Milliseconds 100 }
$taskReady=Get-Content $taskReadyPath -Raw | ConvertFrom-Json
$taskGate=[Threading.EventWaitHandle]::OpenExisting($taskReady.activationEvent)
Stop-Process -Id $taskOld.Id -ErrorAction Stop
$taskOld.WaitForExit()
$null=$taskGate.Set(); $taskGate.Dispose()
if(-not $taskNew.WaitForExit(25000)) { throw 'Successor did not finish synthetic native fixture' }
$taskStatus=Get-Content ($taskRunRoot+'-status.json') -Raw | ConvertFrom-Json
$taskLog=Get-Content ($taskRunRoot+'.stdout.log') -Raw
if($taskStatus.nativeExitCode -ne 7 -or $taskStatus.maxWallHours -ne .01 -or $taskLog -notmatch 'TICK 14' -or $taskLog -notmatch 'FINISHED' -or (Test-Path ($taskRunRoot+'-old-deadline.txt'))) { throw 'Survival/logging/exit/deadline assertion failed' }
@{passed=$true;nativeExitCode=$taskStatus.nativeExitCode;originalWrapperPid=$taskOld.Id;successorPid=$taskNew.Id;nativeCommandPid=$taskReady.nativeCommandPid;sbclPid=$taskReady.sbclPid;logContinuesBeyondOriginalDeadline=$true;fullLogRetained=$true;physicalUpdates=0;scope='Synthetic process survival, inherited-file logging, non-child exit code, deadline extension and monitor handoff only'} | ConvertTo-Json | Set-Content ($taskRunRoot+'-proof.json') -Encoding utf8
Get-Content ($taskRunRoot+'-proof.json')
