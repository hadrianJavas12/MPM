param([string]$OutputDirectory='output/unnotched-gravity-2026-10-24/monitor-controls-001')
$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOutput=[IO.Path]::GetFullPath((Join-Path $taskRepo $OutputDirectory))
if (Test-Path -LiteralPath $taskOutput) { throw 'Fresh control output required.' }
$taskRoot=[IO.Path]::GetFullPath((Join-Path $taskRepo 'output'))+[IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Control output escapes workspace/output.' }
$taskFixture=Join-Path $taskOutput 'fixture with spaces'
foreach ($taskPart in @('scripts','windows','cases','output')) {
  New-Item -ItemType Directory -Path (Join-Path $taskFixture $taskPart) -Force | Out-Null
}
Copy-Item -LiteralPath (Join-Path $taskRepo 'scripts/run-gravity-slope-trial.ps1') -Destination (Join-Path $taskFixture 'scripts/run-gravity-slope-trial.ps1')
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $taskOutput 'executed-test.ps1')
'; No MPM loaded.' | Set-Content -LiteralPath (Join-Path $taskFixture 'scripts/run-case.lisp')
foreach ($taskMode in @('success','nonzero','timeout')) {
  $taskMode | Set-Content -LiteralPath (Join-Path $taskFixture ('cases/'+$taskMode+'.lisp'))
}
$taskSbcl=(Get-Command sbcl -ErrorAction Stop).Source
@"
@echo off
"$taskSbcl" --noinform --no-userinit --disable-debugger --script "%~dp0fixture.lisp" "%~2" "%~3"
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath (Join-Path $taskFixture 'windows/cl-mpm.cmd') -Encoding ascii
@'
;;;; Trusted synthetic process control; no Quicklisp/MPM/project systems.
(let* ((case-file (second sb-ext:*posix-argv*))
       (output (third sb-ext:*posix-argv*))
       (mode (with-open-file (s case-file) (string-trim '(#\Return #\Newline) (read-line s))))
       (path (format nil "~A/manifest.json" output)))
  (ensure-directories-exist path)
  (flet ((write-state (complete)
           (with-open-file (s path :direction :output :if-exists :supersede)
             (format s "{\"status\":\"fixture\",\"complete\":~A,\"phase\":\"synthetic\",\"timeS\":1.2,\"updates\":0,\"savedFrames\":0}"
                     (if complete "true" "false")))))
    (write-state nil) (format t "Native process fixture only.~%") (finish-output)
    (sleep (if (string= mode "timeout") 30 1.5))
    (write-state (string= mode "success"))
    (sb-ext:exit :code (if (string= mode "success") 0 7))))
'@ | Set-Content -LiteralPath (Join-Path $taskFixture 'windows/fixture.lisp') -Encoding ascii
$taskChecks=[Collections.Generic.List[object]]::new()
function Assert-Task([string]$Name,[bool]$Passed) {
  $taskChecks.Add(@{name=$Name;passed=$Passed})
  if (-not $Passed) { throw ('Control failed: '+$Name) }
}
foreach ($taskMode in @('success','nonzero','timeout')) {
  $taskRun=Join-Path $taskFixture ('output/'+$taskMode)
  $taskHours=if ($taskMode -eq 'timeout') {.0008} else {.02}
  $taskArguments=@('-NoProfile','-NonInteractive','-File',('"'+(Join-Path $taskFixture 'scripts/run-gravity-slope-trial.ps1')+'"'),
    '-OutputDirectory',('"'+$taskRun+'"'),'-Case',('cases/'+$taskMode+'.lisp'),'-MaxWallHours',[string]$taskHours,'-HeartbeatSeconds','1')
  $taskProcess=Start-Process -FilePath (Join-Path $PSHOME 'pwsh.exe') -ArgumentList $taskArguments -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput ($taskRun+'-wrapper.stdout.log') -RedirectStandardError ($taskRun+'-wrapper.stderr.log')
  if (-not $taskProcess.WaitForExit(20000)) { throw 'Fixture controller did not terminate; inspect live handle before retry.' }
  $taskProcess.Refresh()
  $taskStatus=Get-Content -LiteralPath ($taskRun+'-status.json') -Raw | ConvertFrom-Json
  $taskExpected= switch ($taskMode) {success {'NATIVE_COMPLETE_REVIEW_PENDING'} nonzero {'FAILED_NATIVE'} timeout {'STOPPED_WALL_BUDGET'}}
  Assert-Task ($taskMode+' terminal status') ($taskStatus.status -eq $taskExpected)
  Assert-Task ($taskMode+' scientific flags remain false') (-not $taskStatus.scientificValidation -and -not $taskStatus.landslideVerified)
  Assert-Task ($taskMode+' process identities captured') ($taskStatus.processIdentity.nativeCommand.createdUtc -and $taskStatus.processIdentity.sbcl.createdUtc)
  if ($taskMode -eq 'success') {
    Assert-Task 'Native0/complete captured' ($taskStatus.nativeExitCode -eq 0 -and $taskStatus.nativeComplete -and $taskProcess.ExitCode -eq 0)
  } elseif ($taskMode -eq 'nonzero') {
    Assert-Task 'Native7 retained without MPM failure inference' ($taskStatus.nativeExitCode -eq 7 -and $taskProcess.ExitCode -eq 7)
  } else {
    Assert-Task 'Budget exit3 without invented native exit' ($taskProcess.ExitCode -eq 3 -and $null -eq $taskStatus.nativeExitCode)
    $taskChild=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskStatus.processIdentity.sbcl.pid)
    Assert-Task 'Exact native child terminated by retained root handle' (-not $taskChild -or $taskChild.CreationDate.ToUniversalTime().ToString('o') -ne $taskStatus.processIdentity.sbcl.createdUtc)
  }
}
[ordered]@{status='PASS';physicalUpdatesExecuted=0;controls=$taskChecks;finishedUtc=[DateTime]::UtcNow.ToString('o');scope='Trusted synthetic process fixtures, zero MPM updates; no logoff/sleep/reboot immunity claim'} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskOutput 'result.json') -Encoding utf8
Write-Output ('PASS '+$taskChecks.Count+' synthetic monitor assertions; zero MPM updates.')
