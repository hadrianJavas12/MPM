$ErrorActionPreference='Stop'
$taskRun='output/unnotched-gravity-2026-10-25/srf1p4-h05-001'
$taskState=Get-Content "$taskRun-status.json" -Raw | ConvertFrom-Json
$taskWorker=Get-Content "$taskRun-detached/worker-start.json" -Raw | ConvertFrom-Json
$taskRecords=@()
foreach($taskName in @('wrapper','nativeCommand','sbcl')) {
  $taskExpected=$taskState.processIdentity.$taskName
  $taskProcess=Get-Process -Id $taskExpected.pid -ErrorAction Stop
  if($taskProcess.SessionId -ne $taskExpected.sessionId -or
     $taskProcess.StartTime.ToUniversalTime().Ticks -ne ([DateTime]$taskExpected.createdUtc).ToUniversalTime().Ticks) {
    throw "Process identity mismatch: $taskName"
  }
  $taskCim=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskExpected.pid)
  $taskRecords += [ordered]@{role=$taskName;pid=$taskProcess.Id;name=$taskProcess.ProcessName;
    sessionId=$taskProcess.SessionId;creationUtc=$taskProcess.StartTime.ToUniversalTime().ToString('o');
    parentPid=$taskCim.ParentProcessId;creationClock='System.Diagnostics.Process';identityMatched=$true}
}
# Worker launch records use CIM microsecond precision; compare the SAME clock.
$taskCim=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskWorker.processId)
if(-not $taskCim -or $taskCim.SessionId -ne $taskWorker.sessionId -or
   $taskCim.CreationDate.ToUniversalTime().Ticks -ne ([DateTime]$taskWorker.creationUtc).ToUniversalTime().Ticks) {
  throw 'Worker CIM identity mismatch'
}
if(($taskRecords | Where-Object role -eq 'nativeCommand').parentPid -ne ($taskRecords | Where-Object role -eq 'wrapper').pid -or
   ($taskRecords | Where-Object role -eq 'sbcl').parentPid -ne ($taskRecords | Where-Object role -eq 'nativeCommand').pid -or
   ($taskRecords | Where-Object role -eq 'wrapper').parentPid -ne $taskWorker.processId) {
  throw 'Live parent chain mismatch'
}
$taskRecords += [ordered]@{role='detachedWorker';pid=$taskCim.ProcessId;sessionId=$taskCim.SessionId;
  creationUtc=$taskCim.CreationDate.ToUniversalTime().ToString('o');creationClock='Win32_Process';identityMatched=$true}
[ordered]@{capturedUtc=[DateTime]::UtcNow.ToString('o');sourceCommit=$taskState.sourceCommit;
  status=$taskState.status;processes=$taskRecords;
  scope='Exact live PID, session, creation-clock and parent-chain checks; no logoff/sleep/reboot guarantee'} |
  ConvertTo-Json -Depth 6 | Set-Content "$taskRun-live-process-verification.json"
$taskRecords | ConvertTo-Json -Depth 4
