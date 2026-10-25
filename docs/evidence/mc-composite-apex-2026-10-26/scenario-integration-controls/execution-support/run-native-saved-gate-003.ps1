$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/MPM'
$taskOutput = 'output/mc-composite-apex-2026-10-26/scenario-controls-003'
if (Test-Path -LiteralPath $taskOutput) { throw 'Preserve existing attempt' }
$taskArgs = @('tests/benchmarks/gravity-composite-apex-controls.lisp',$taskOutput,
  'saved','D:/MPM/output/mc-composite-apex-2026-10-26/scenario-controls-001/observations/')
$taskRecord = [ordered]@{sourceHead=(git rev-parse HEAD);executable='windows/cl-mpm.cmd';arguments=$taskArgs;
  startedUtc=[DateTime]::UtcNow.ToString('o');runnerSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;
  scope='Saved-state reader repair/read-only gate; skips four passed groups, zero MPM updates'}
[IO.File]::WriteAllText((Join-Path (Get-Location) ($taskOutput+'.command.json')),($taskRecord|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
& .\windows\cl-mpm.cmd @taskArgs *> ($taskOutput+'.log')
$taskExit = $LASTEXITCODE
[IO.File]::WriteAllText((Join-Path (Get-Location) ($taskOutput+'.exit.json')),
  (([ordered]@{exitCode=$taskExit;endedUtc=[DateTime]::UtcNow.ToString('o')})|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Get-Content -LiteralPath ($taskOutput+'.log') -Tail 18
exit $taskExit
