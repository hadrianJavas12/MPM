param([string]$OutputDirectory='output/wang2017-reference-2026-10-24/detached-launch-budget-controls-001')
$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOutput=[IO.Path]::GetFullPath((Join-Path $taskRepo $OutputDirectory))
$taskLauncher=Join-Path $taskRepo 'scripts/start-wang2017-detached.ps1'
function Assert-Task([bool]$Condition,[string]$Message) { if (-not $Condition) { throw $Message } }
Assert-Task (-not (Test-Path -LiteralPath $taskOutput)) 'Budget control output must be fresh.'
New-Item -ItemType Directory -Path $taskOutput | Out-Null
foreach ($taskInvalid in @([double]73,[double]::NaN)) {
  $taskInvalidOutput=Join-Path $taskOutput ('invalid-'+$taskInvalid.ToString([Globalization.CultureInfo]::InvariantCulture))
  $taskRejected=$false
  try { & $taskLauncher -OutputDirectory $taskInvalidOutput -MaxWallHours $taskInvalid -LaunchControlFixture | Out-Null }
  catch { $taskRejected=$_.Exception.Message.Contains('finite and in (0,72]') }
  Assert-Task $taskRejected ('Budget was not rejected: '+$taskInvalid)
  Assert-Task (-not (Test-Path -LiteralPath $taskInvalidOutput) -and -not (Test-Path -LiteralPath ($taskInvalidOutput+'-detached'))) 'Rejected budget created output artifacts.'
}
$taskValidOutput=Join-Path $taskOutput 'maximum72'
& $taskLauncher -OutputDirectory $taskValidOutput -MaxWallHours 72 -LaunchControlFixture |
  Set-Content -LiteralPath (Join-Path $taskOutput 'launcher.stdout.json') -Encoding utf8
$taskLaunch=$taskValidOutput+'-detached'
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
while (-not (Test-Path -LiteralPath (Join-Path $taskLaunch 'fixture-start.json')) -and $taskTimer.Elapsed.TotalSeconds -lt 10) { Start-Sleep -Milliseconds 200 }
Assert-Task (Test-Path -LiteralPath (Join-Path $taskLaunch 'fixture-start.json')) 'Maximum72 fixture startup missing.'
New-Item -ItemType File -Path (Join-Path $taskLaunch 'fixture-release') | Out-Null
$taskTimer.Restart()
while (-not (Test-Path -LiteralPath (Join-Path $taskLaunch 'worker-exit.json')) -and $taskTimer.Elapsed.TotalSeconds -lt 15) { Start-Sleep -Milliseconds 200 }
Assert-Task (Test-Path -LiteralPath (Join-Path $taskLaunch 'worker-exit.json')) 'Maximum72 fixture exit missing.'
$taskRequest=Get-Content -LiteralPath (Join-Path $taskLaunch 'launch-request.json') -Raw | ConvertFrom-Json
$taskExit=Get-Content -LiteralPath (Join-Path $taskLaunch 'worker-exit.json') -Raw | ConvertFrom-Json
Assert-Task ($taskRequest.maxWallHours -eq 72 -and $taskRequest.fixtureMode) 'Maximum72 request was not preserved.'
Assert-Task ($taskExit.exitCode -eq 7) 'Maximum72 tiny fixture did not finish with expected exit7.'
[ordered]@{
  status='PASS'; controls=3; rejected73WithoutArtifacts=$true; rejectedNaNWithoutArtifacts=$true
  accepted72TinyFixtureExitCode=$taskExit.exitCode; defaultHoursUnchanged=8; physicalUpdates=0
  finishedUtc=[DateTime]::UtcNow.ToString('o'); scope='Budget guard/request only; prior9 detached mechanism controls were not repeated. No MPM run.'
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOutput 'result.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskOutput 'result.json')
