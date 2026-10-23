param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$taskSelf = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $PID)
[ordered]@{
  processId=$PID; parentProcessId=$taskSelf.ParentProcessId; sessionId=$taskSelf.SessionId
  creationUtc=$taskSelf.CreationDate.ToUniversalTime().ToString('o'); observedUtc=[DateTime]::UtcNow.ToString('o')
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'fixture-start.json') -Encoding utf8
Write-Output 'Detached fixture stdout captured.'
[Console]::Error.WriteLine('Detached fixture stderr captured.')
$taskTimer = [Diagnostics.Stopwatch]::StartNew()
while (-not (Test-Path -LiteralPath (Join-Path $OutputDirectory 'fixture-release')) -and $taskTimer.Elapsed.TotalSeconds -lt 60) {
  Start-Sleep -Milliseconds 200
}
if (-not (Test-Path -LiteralPath (Join-Path $OutputDirectory 'fixture-release'))) { exit 8 }
exit 7
