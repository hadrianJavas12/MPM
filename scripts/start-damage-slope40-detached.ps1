param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [Parameter(Mandatory=$true)][string]$Case,
  [double]$MaxWallHours = 12,
  [double]$ExpectedSimulationTimeS = 60,
  [ValidateRange(1,60)][int]$StartupTimeoutSeconds = 30,
  [switch]$LaunchControlFixture
)
$ErrorActionPreference = 'Stop'
if (-not $IsWindows -or $PSVersionTable.PSVersion.Major -lt 7) {
  throw 'Use Windows PowerShell 7 for the local CIM launcher.'
}
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
function Resolve-TaskPath([string]$Path) {
  if ($Path.Contains('"') -or $Path.Contains("`r") -or $Path.Contains("`n")) {
    throw 'Paths containing quotes or newlines are unsupported.'
  }
  if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
  return [IO.Path]::GetFullPath((Join-Path $taskRepo $Path))
}
function Save-TaskJson($Value, [string]$Path) {
  $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding utf8
}
$taskOutput = (Resolve-TaskPath $OutputDirectory).TrimEnd('\','/')
$taskOutputRoot = [IO.Path]::GetFullPath((Join-Path $taskRepo 'output')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskOutputRoot,[StringComparison]::OrdinalIgnoreCase)) {
  throw 'Detached output must be a fresh subdirectory of workspace/output.'
}
if ([double]::IsNaN($MaxWallHours) -or [double]::IsInfinity($MaxWallHours) -or
    $MaxWallHours -le 0 -or $MaxWallHours -gt 72) { throw 'Wall budget must be finite and in (0,72] hours.' }
if (-not [double]::IsFinite($ExpectedSimulationTimeS) -or $ExpectedSimulationTimeS -le 0) { throw 'Expected physical duration must be positive and finite.' }
$taskLaunchDirectory = $taskOutput + '-detached'
foreach ($taskPath in @($taskOutput,$taskLaunchDirectory,($taskOutput+'-launch.json'),($taskOutput+'-status.json'),($taskOutput+'.stdout.log'),($taskOutput+'.stderr.log'))) {
  if (Test-Path -LiteralPath $taskPath) { throw ('Refusing duplicate attempt: ' + $taskPath) }
}
$taskCase = Resolve-TaskPath $Case
$taskWrapperRelative = 'scripts/run-damage-slope40-trial.ps1'
$taskWrapper = Join-Path $taskRepo $taskWrapperRelative
$taskFixture = Join-Path $taskRepo 'tests/windows/fixtures/detached-exit-fixture.ps1'
if (-not (Test-Path -LiteralPath $taskWrapper -PathType Leaf)) { throw 'Trusted native trial wrapper missing.' }
if (-not (Test-Path -LiteralPath $taskCase -PathType Leaf)) { throw 'Case source missing.' }
if ($LaunchControlFixture -and -not (Test-Path -LiteralPath $taskFixture -PathType Leaf)) {
  throw 'Fixed trusted launch-control fixture missing.'
}
$taskPowerShell = Join-Path $PSHOME 'pwsh.exe'
$taskCaller = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $PID)
# The request directory and repository must be writable only by trusted local users.
# This launcher neither broadens their ACLs nor attempts privilege elevation.
New-Item -ItemType Directory -Path $taskLaunchDirectory | Out-Null
$taskRequest = [ordered]@{
  schemaVersion=1; requestedUtc=[DateTime]::UtcNow.ToString('o')
  repository=$taskRepo; output=$taskOutput; case=$taskCase; maxWallHours=$MaxWallHours
  expectedSimulationTimeS=$ExpectedSimulationTimeS
  powerShellPath=$taskPowerShell; wrapperPath=$taskWrapper
  wrapperSha256=(Get-FileHash -LiteralPath $taskWrapper -Algorithm SHA256).Hash
  caseSha256=(Get-FileHash -LiteralPath $taskCase -Algorithm SHA256).Hash
  fixtureMode=[bool]$LaunchControlFixture; fixturePath=$taskFixture
  callerProcessId=$PID; callerSessionId=$taskCaller.SessionId
  callerCreationUtc=$taskCaller.CreationDate.ToUniversalTime().ToString('o')
  stdoutPath=(Join-Path $taskLaunchDirectory 'wrapper.stdout.log')
  stderrPath=(Join-Path $taskLaunchDirectory 'wrapper.stderr.log')
  aclAssumption='Repository and output paths are controlled by trusted local users; ACLs are not changed.'
  limitation='Local WMI creation avoids direct caller parentage. Provider jobs, logoff, sleep, reboot and policy may still stop the run.'
}
$taskRequestPath = Join-Path $taskLaunchDirectory 'launch-request.json'
Save-TaskJson $taskRequest $taskRequestPath
$taskWorkerSource = @'
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
      '-MaxWallHours',[string]$taskRequest.maxWallHours,
      '-ExpectedSimulationTimeS',[string]$taskRequest.expectedSimulationTimeS)
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
'@
$taskWorkerPath = Join-Path $taskLaunchDirectory 'launch-request.ps1'
$taskWorkerSource | Set-Content -LiteralPath $taskWorkerPath -Encoding utf8
$taskCommand = '"' + $taskPowerShell + '" -NoProfile -NonInteractive -WindowStyle Hidden -File "' + $taskWorkerPath + '"'
$taskStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow=[uint16]0 }
$taskProof = [ordered]@{
  requestedUtc=$taskRequest.requestedUtc; method='local Win32_Process.Create / CIM'
  commandLine=$taskCommand; currentDirectory=$taskRepo; showWindow=0
  callerProcessId=$PID; callerSessionId=$taskCaller.SessionId
  requestSha256=(Get-FileHash -LiteralPath $taskRequestPath -Algorithm SHA256).Hash
  workerScriptSha256=(Get-FileHash -LiteralPath $taskWorkerPath -Algorithm SHA256).Hash
  workerProcessId=$null; returnValue=$null; startupObserved=$false
  limitation=$taskRequest.limitation
}
$taskProofPath = Join-Path $taskLaunchDirectory 'launch-proof.json'
try {
  $taskCreated = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine=$taskCommand; CurrentDirectory=$taskRepo; ProcessStartupInformation=$taskStartup
  }
  $taskProof.returnValue = $taskCreated.ReturnValue
  $taskProof.workerProcessId = $taskCreated.ProcessId
  Save-TaskJson $taskProof $taskProofPath
  if ($taskCreated.ReturnValue -ne 0) { throw ('Win32_Process.Create failed with return value ' + $taskCreated.ReturnValue + '; no fallback or elevation attempted.') }
  $taskCreatedInfo = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $taskCreated.ProcessId)
  if ($taskCreatedInfo) {
    $taskProof.workerSessionId = $taskCreatedInfo.SessionId
    $taskProof.workerParentProcessId = $taskCreatedInfo.ParentProcessId
    $taskProof.workerCreationUtc = $taskCreatedInfo.CreationDate.ToUniversalTime().ToString('o')
  }
  $taskTimer = [Diagnostics.Stopwatch]::StartNew()
  while ($taskTimer.Elapsed.TotalSeconds -lt $StartupTimeoutSeconds) {
    if (Test-Path -LiteralPath (Join-Path $taskLaunchDirectory 'worker-start.json')) {
      $taskProof.startupObserved = $true
      break
    }
    if (Test-Path -LiteralPath (Join-Path $taskLaunchDirectory 'worker-exit.json')) { break }
    Start-Sleep -Milliseconds 200
  }
  $taskProof.startupWaitSeconds = $taskTimer.Elapsed.TotalSeconds
  Save-TaskJson $taskProof $taskProofPath
  if (-not $taskProof.startupObserved) {
    throw 'Worker startup proof was not observed within the bounded interval. Inspect retained proof before any retry; a process may still exist.'
  }
  [ordered]@{ status='DETACHED_WORKER_STARTED'; output=$taskOutput; launchDirectory=$taskLaunchDirectory; workerProcessId=$taskCreated.ProcessId; fixtureMode=[bool]$LaunchControlFixture } | ConvertTo-Json
} catch {
  $taskProof.error = $_.Exception.Message
  Save-TaskJson $taskProof $taskProofPath
  throw
}

