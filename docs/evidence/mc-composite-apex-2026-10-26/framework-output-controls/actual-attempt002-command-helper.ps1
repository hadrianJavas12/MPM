param([Parameter(Mandatory=$true)][string]$Test,
      [Parameter(Mandatory=$true)][string]$Output,
      [string]$Groups)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/MPM'
if (Test-Path -LiteralPath $Output) { throw 'Preserve existing output; use a fresh attempt' }
New-Item -ItemType Directory -Force -Path (Split-Path $Output -Parent) | Out-Null
$taskArgs = @($Test, $Output)
if ($Groups) { $taskArgs += $Groups }
$taskRecord = [ordered]@{sourceHead=(git rev-parse HEAD);executable='windows/cl-mpm.cmd';arguments=$taskArgs;
  startedUtc=[DateTime]::UtcNow.ToString('o');runnerSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}
[IO.File]::WriteAllText((Join-Path (Get-Location) ($Output+'.command.json')),($taskRecord|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
& .\windows\cl-mpm.cmd @taskArgs *> ($Output+'.log')
$taskExit = $LASTEXITCODE
[IO.File]::WriteAllText((Join-Path (Get-Location) ($Output+'.exit.json')),
  (([ordered]@{exitCode=$taskExit;endedUtc=[DateTime]::UtcNow.ToString('o')})|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Get-Content -LiteralPath ($Output+'.log') -Tail 18
exit $taskExit
