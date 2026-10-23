param([string]$RunRoot,[string]$SbclExe)
$ErrorActionPreference='Stop'
Set-Location D:\MPM
$taskCase='D:\MPM\.tmp\test-wang-monitor-child.lisp'
$taskHashes=@{}
foreach($taskTool in @('scripts/plot-wang2017-descent.py','scripts/plot_m5_cliff_comparison.py','scripts/collect-wang2017-evidence.py')) {
  $taskHashes[$taskTool]=(Get-FileHash -LiteralPath $taskTool -Algorithm SHA256).Hash
}
$taskCommand='call "'+$SbclExe+'" --noinform --no-userinit --disable-debugger --script "'+$taskCase+'" "'+$RunRoot+'"'
$taskStarted=[DateTime]::UtcNow.ToString('o')
$taskChild=Start-Process cmd.exe -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -PassThru -RedirectStandardOutput ($RunRoot+'.stdout.log') -RedirectStandardError ($RunRoot+'.stderr.log')
@{startedUtc=$taskStarted;sourceCommitAtLaunch='SYNTHETIC_SUPERVISOR_TEST';wrapperPid=$PID;nativeCommandPid=$taskChild.Id;case='.tmp/test-wang-monitor-child.lisp';output=$RunRoot;maxWallHours=.0028;status='NATIVE_RUNNING';postprocessorSha256=$taskHashes} | ConvertTo-Json -Depth 5 | Set-Content ($RunRoot+'-status.json') -Encoding utf8
if(-not $taskChild.WaitForExit(10080)) { $taskChild.Kill($true); 'ORIGINAL_DEADLINE_KILLED_CHILD' | Set-Content ($RunRoot+'-old-deadline.txt') }
