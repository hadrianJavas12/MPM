$ErrorActionPreference = 'Stop'
$taskRequest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'launch-request.json') -Raw | ConvertFrom-Json
$taskExitCode = 1
try {
  Set-Location -LiteralPath $taskRequest.repository
  $taskSelf = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $PID)
  [ordered]@{
    status='WORKER_STARTED'; processId=$PID; parentProcessId=$taskSelf.ParentProcessId
    sessionId=$taskSelf.SessionId; creationUtc=$taskSelf.CreationDate.ToUniversalTime().ToString('o')
    observedUtc=[DateTime]::UtcNow.ToString('o'); callerProcessId=$taskRequest.callerProcessId
    callerSessionId=$taskRequest.callerSessionId
  } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'worker-start.json') -Encoding utf8
  if ($taskRequest.fixtureMode) {
    $taskArguments = @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-File',
      $taskRequest.fixturePath,'-OutputDirectory',$PSScriptRoot)
  } else {
    if ((Get-FileHash -LiteralPath $taskRequest.wrapperPath -Algorithm SHA256).Hash -ne $taskRequest.wrapperSha256 -or
        (Get-FileHash -LiteralPath $taskRequest.case -Algorithm SHA256).Hash -ne $taskRequest.caseSha256) {
      throw 'Trusted wrapper or case changed between request and execution.'
    }
    $taskArguments = @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-File',
      $taskRequest.wrapperPath,'-OutputDirectory',$taskRequest.output,'-Case',$taskRequest.case,
      '-MaxWallHours',[string]$taskRequest.maxWallHours)
    if ($taskRequest.evidenceDirectory) { $taskArguments += @('-EvidenceDirectory',$taskRequest.evidenceDirectory) }
  }
  & $taskRequest.powerShellPath @taskArguments 1> $taskRequest.stdoutPath 2> $taskRequest.stderrPath
  $taskExitCode = $LASTEXITCODE
  [ordered]@{ status='WORKER_EXITED'; exitCode=$taskExitCode; processId=$PID; finishedUtc=[DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'worker-exit.json') -Encoding utf8
} catch {
  [ordered]@{ status='WORKER_FAILED'; exitCode=1; processId=$PID; finishedUtc=[DateTime]::UtcNow.ToString('o'); error=$_.Exception.Message } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'worker-exit.json') -Encoding utf8
}
exit $taskExitCode
