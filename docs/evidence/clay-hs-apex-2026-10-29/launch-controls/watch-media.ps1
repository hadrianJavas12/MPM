param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference='Stop'
$taskRun=[IO.Path]::GetFullPath($RunDirectory)
$taskPrep=$taskRun+'-launch-preparation'
$taskInfo=Get-Content -LiteralPath (Join-Path $taskPrep 'media-request.json') -Raw | ConvertFrom-Json
$taskResult=[ordered]@{status='WAITING_NATIVE';startedUtc=[DateTime]::UtcNow.ToString('o');processId=$PID;nativeSolverReruns=0;reviewExitCode=$null}
function Save-Media { $taskResult.heartbeatUtc=[DateTime]::UtcNow.ToString('o'); $taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($taskRun+'-media-status.json') -Encoding utf8 }
try {
 Save-Media
 $taskDeadline=[DateTime]::UtcNow.AddHours(24)
 do {
  $taskNative=Get-Content -LiteralPath ($taskRun+'-status.json') -Raw | ConvertFrom-Json
  if ($taskNative.status -notin @('NATIVE_RUNNING','STARTING')) { break }
  if ([DateTime]::UtcNow -ge $taskDeadline) { throw 'Watcher deadline reached without authoritative native terminal status; no invented exit or native kill.' }
  Start-Sleep -Seconds 60
  Save-Media
 } while ($true)
 $taskManifest=Get-Content -LiteralPath (Join-Path $taskRun 'manifest.json') -Raw | ConvertFrom-Json
 if ($taskManifest.savedFrames -le 0) { throw 'No complete saved native frame available for media.' }
 $taskFreeze=Get-Content -LiteralPath (Join-Path $taskPrep 'analysis/analysis-freeze.json') -Raw | ConvertFrom-Json
 foreach ($r in $taskFreeze.records) { if ((Get-FileHash -LiteralPath $r.path -Algorithm SHA256).Hash -ne $r.sha256) { throw 'Frozen saved observer bytes changed.' } }
 $taskReview=Join-Path $taskRun 'filled-review-001'
 $taskArgs=@((Join-Path $taskPrep 'analysis/review-residual-clay-quarter.py'),'--run-dir',$taskRun,'--output-dir',$taskReview,'--video')
 if ($taskManifest.status -eq 'failed') { $taskArgs+='--allow-partial' }
 elseif ($taskManifest.status -ne 'complete') { if ($taskNative.status -ne 'STOPPED_WALL_BUDGET') { throw 'No authoritative native terminal proof.' }; $taskArgs+='--stopped-wrapper' }
 $taskArgs | ConvertTo-Json | Set-Content -LiteralPath ($taskRun+'-review-command.json') -Encoding utf8
 $taskResult.status='EXPORTING_SAVED_DATA';$taskResult.reviewDirectory=$taskReview;Save-Media
 $taskQuoted=@($taskArgs | ForEach-Object { '"'+[string]$_+'"' })
 $taskProcess=Start-Process -FilePath $taskInfo.pythonPath -ArgumentList $taskQuoted -WindowStyle Hidden -PassThru -RedirectStandardOutput ($taskRun+'-review.stdout.log') -RedirectStandardError ($taskRun+'-review.stderr.log')
 $taskMediaDeadline=[DateTime]::UtcNow.AddHours(2)
 while (-not $taskProcess.WaitForExit(60000)) {
  Save-Media
  if ([DateTime]::UtcNow -ge $taskMediaDeadline) { $taskProcess.Kill($true); $taskProcess.WaitForExit();throw 'Media exceeded2h; saved data retained.' }
 }
 $taskProcess.Refresh();$taskResult.reviewExitCode=$taskProcess.ExitCode
 if ($taskProcess.ExitCode -notin @(0,2) -or -not(Test-Path -LiteralPath (Join-Path $taskReview 'review.json'))) { throw 'Saved observer/media failure; repair saved data only.' }
 $taskResult.status=if($taskManifest.complete){'COMPLETE_VIDEOS_READY'}else{'PARTIAL_VIDEOS_READY'}
 $taskResult.endedUtc=[DateTime]::UtcNow.ToString('o');Save-Media
} catch { $taskResult.status='MEDIA_FAILED';$taskResult.error=$_.Exception.Message;$taskResult.endedUtc=[DateTime]::UtcNow.ToString('o');Save-Media;throw }
