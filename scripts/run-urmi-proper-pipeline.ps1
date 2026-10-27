param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [Parameter(Mandatory=$true)][string]$Case,
  [double]$MaxWallHours=22
)
$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $taskRepo
$taskOutput=[IO.Path]::GetFullPath($OutputDirectory)
$taskPreparation=$taskOutput+'-launch-preparation'
$taskPipelinePath=$taskOutput+'-pipeline.json'
$taskPipeline=[ordered]@{status='STARTING';startedUtc=[DateTime]::UtcNow.ToString('o');nativeExitCode=$null;reviewExitCode=$null;solverReruns=0;output=$taskOutput}
function Save-Pipeline { $taskPipeline.heartbeatUtc=[DateTime]::UtcNow.ToString('o'); $taskPipeline | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskPipelinePath -Encoding utf8 }
try {
  if ($MaxWallHours -ne 22) { throw 'This declared pipeline reserves22h native plus2h media, within24h; do not silently change it.' }
  $taskFreeze=Get-Content -LiteralPath (Join-Path $taskPreparation 'preparation.json') -Raw | ConvertFrom-Json
  foreach ($taskRecord in $taskFreeze.records) {
    if ((Get-FileHash -LiteralPath $taskRecord.path -Algorithm SHA256).Hash -ne $taskRecord.sha256) { throw ('Prelaunch bytes changed: '+$taskRecord.path) }
  }
  $taskPipeline.status='NATIVE_RUNNING'; Save-Pipeline
  & (Join-Path $PSHOME 'pwsh.exe') -NoProfile -NonInteractive -WindowStyle Hidden -File (Join-Path $taskRepo 'scripts/run-gravity-slope-trial.ps1') -OutputDirectory $taskOutput -Case $Case -MaxWallHours $MaxWallHours
  $taskPipeline.nativeExitCode=$LASTEXITCODE
  $taskStatus=Get-Content -LiteralPath ($taskOutput+'-status.json') -Raw | ConvertFrom-Json
  $taskManifest=Get-Content -LiteralPath (Join-Path $taskOutput 'manifest.json') -Raw | ConvertFrom-Json
  $taskReview=Join-Path $taskOutput 'filled-review-001'
  $taskArguments=@((Join-Path $taskPreparation 'analysis/review-urmi-proper.py'),'--run-dir',$taskOutput,'--output-dir',$taskReview,'--video')
  if ($taskManifest.status -eq 'failed') { $taskArguments+='--allow-partial' }
  elseif ($taskManifest.status -ne 'complete') {
    if ($taskStatus.status -ne 'STOPPED_WALL_BUDGET') { throw 'No authoritative native terminal state; refusing ambiguous review.' }
    $taskArguments+='--stopped-wrapper'
  }
  $taskArguments | ConvertTo-Json | Set-Content -LiteralPath ($taskOutput+'-review-command.json') -Encoding utf8
  $taskPipeline.status='EXPORTING_SAVED_DATA'; $taskPipeline.reviewDirectory=$taskReview; Save-Pipeline
  # Argument quoting is needed by Windows ProcessStartInfo; paths are trusted
  # and checked by the native launcher to exclude quotes/newlines.
  $taskQuoted=@($taskArguments | ForEach-Object { '"'+[string]$_+'"' })
  $taskProcess=Start-Process -FilePath (Join-Path $taskRepo 'toolchain/analysis-venv/Scripts/python.exe') -ArgumentList $taskQuoted -WindowStyle Hidden -PassThru -RedirectStandardOutput ($taskOutput+'-review.stdout.log') -RedirectStandardError ($taskOutput+'-review.stderr.log')
  $taskMediaStarted=[DateTime]::UtcNow
  while (-not $taskProcess.WaitForExit(60000)) {
    Save-Pipeline
    if (([DateTime]::UtcNow-$taskMediaStarted).TotalHours -ge 2) {
      $taskProcess.Kill($true); $taskProcess.WaitForExit(); throw 'Media exceeded reserved2h; all saved data preserved.'
    }
  }
  $taskProcess.Refresh(); $taskPipeline.reviewExitCode=$taskProcess.ExitCode
  if ($taskProcess.ExitCode -notin @(0,2) -or -not (Test-Path -LiteralPath (Join-Path $taskReview 'review.json'))) { throw 'Saved review/export failed; repair saved data only.' }
  $taskPipeline.status=if ($taskManifest.complete) {'COMPLETE_VIDEOS_READY'} else {'PARTIAL_VIDEOS_READY'}
  $taskPipeline.endedUtc=[DateTime]::UtcNow.ToString('o'); Save-Pipeline
  exit $taskPipeline.nativeExitCode
} catch {
  $taskPipeline.status='PIPELINE_FAILED'; $taskPipeline.error=$_.Exception.Message
  $taskPipeline.endedUtc=[DateTime]::UtcNow.ToString('o'); Save-Pipeline
  throw
}
