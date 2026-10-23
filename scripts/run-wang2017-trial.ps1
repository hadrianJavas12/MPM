param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [string]$Case = 'cases/benchmarks/wang2017-soil1-fast-005.lisp',
  [double]$MaxWallHours = 4,
  [string]$EvidenceDirectory = '',
  [switch]$AttachRunning,
  [ValidateRange(0.1,3600)][double]$HeartbeatSeconds = 60
)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $taskRepo
function Resolve-TaskPath([string]$Path) {
  if ($Path.Contains('"')) { throw 'Paths containing quotes are unsupported.' }
  if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
  return [IO.Path]::GetFullPath((Join-Path $taskRepo $Path))
}
function Save-TaskStatus {
  $taskRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($taskOutput + '-status.json') -Encoding utf8
}
function Get-TaskProcessIdentity([Diagnostics.Process]$Process) {
  [ordered]@{
    pid=$Process.Id; name=$Process.ProcessName
    createdUtc=$Process.StartTime.ToUniversalTime().ToString('o'); sessionId=$Process.SessionId
  }
}
function Assert-TaskProcessIdentity($Recorded, [Diagnostics.Process]$Process) {
  if ($null -eq $Recorded) { return } # Historical monitor records predate identities.
  $taskIdentity = Get-TaskProcessIdentity $Process
  if ($Recorded.pid -ne $taskIdentity.pid -or ([DateTimeOffset]$Recorded.createdUtc) -ne ([DateTimeOffset]$taskIdentity.createdUtc) -or
      $Recorded.sessionId -ne $taskIdentity.sessionId) { throw 'Recorded process identity differs; no process was stopped.' }
}
function Update-TaskHeartbeat {
  $taskRecord.heartbeatUtc=[DateTime]::UtcNow.ToString('o')
  $taskRecord.heartbeatSequence++
  if ($null -eq $taskRecord.processIdentity.sbcl -and -not $taskNative.HasExited) {
    $taskChildren = @(Get-CimInstance Win32_Process -Filter ('ParentProcessId=' + $taskNative.Id) |
      Where-Object Name -eq 'sbcl.exe')
    if ($taskChildren.Count -eq 1) {
      try {
        $taskWorkerProcess=Get-Process -Id $taskChildren[0].ProcessId -ErrorAction Stop
        $taskRecord.processIdentity.sbcl=Get-TaskProcessIdentity $taskWorkerProcess
      } catch { $taskRecord.workerIdentityReadError=$_.Exception.Message }
    }
  }
  $taskProgress=[ordered]@{observedUtc=$taskRecord.heartbeatUtc}
  $taskManifestFile=Join-Path $taskOutput 'manifest.json'
  if (Test-Path -LiteralPath $taskManifestFile) {
    $taskProgress.manifestLastWriteUtc=(Get-Item -LiteralPath $taskManifestFile).LastWriteTimeUtc.ToString('o')
    try {
      $taskProgressManifest=Get-Content -LiteralPath $taskManifestFile -Raw | ConvertFrom-Json -AsHashtable
      foreach ($taskKey in @('status','complete','phase','timeS','commandedSettlementM','measuredSettlementM',
          'gravityConverged','settleUpdates','gravityTimeS','loadingUpdates','gravityFreeResidualRatio')) {
        if ($taskProgressManifest.ContainsKey($taskKey)) { $taskProgress[$taskKey]=$taskProgressManifest[$taskKey] }
      }
    } catch {
      # Native JSON may be between truncate and flush; a later heartbeat retries it.
      $taskProgress.manifestReadError=$_.Exception.Message
    }
  }
  foreach ($taskLogName in @('stdout','stderr')) {
    $taskLogPath=$taskOutput + '.' + $taskLogName + '.log'
    if (Test-Path -LiteralPath $taskLogPath) {
      $taskLogItem=Get-Item -LiteralPath $taskLogPath
      $taskProgress[$taskLogName]=@{lastWriteUtc=$taskLogItem.LastWriteTimeUtc.ToString('o');bytes=$taskLogItem.Length}
    }
  }
  $taskRecord.progress=$taskProgress
  Save-TaskStatus
}
function Stop-NativeTree([int]$RootId) {
  $taskProcesses = @(Get-CimInstance Win32_Process)
  $taskIds = [Collections.Generic.List[int]]::new()
  $taskIds.Add($RootId)
  for ($taskIndex=0; $taskIndex -lt $taskIds.Count; $taskIndex++) {
    foreach ($taskChild in $taskProcesses) {
      if ($taskChild.ParentProcessId -eq $taskIds[$taskIndex] -and -not $taskIds.Contains([int]$taskChild.ProcessId)) {
        $taskIds.Add([int]$taskChild.ProcessId)
      }
    }
  }
  for ($taskIndex=$taskIds.Count-1; $taskIndex -ge 0; $taskIndex--) {
    Stop-Process -Id $taskIds[$taskIndex] -ErrorAction SilentlyContinue
  }
}
$taskOutput = (Resolve-TaskPath $OutputDirectory).TrimEnd('\','/')
$taskOutputRoot = [IO.Path]::GetFullPath((Join-Path $taskRepo 'output')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskOutputRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Native output must be a fresh subdirectory of workspace/output.'
}
if (-not [double]::IsFinite($MaxWallHours) -or $MaxWallHours -le 0 -or $MaxWallHours -gt 72) { throw 'Wall budget must be finite and in (0,72] hours.' }
if (-not [double]::IsFinite($HeartbeatSeconds)) { throw 'Heartbeat interval must be finite.' }
if (-not $AttachRunning) {
  foreach ($taskPath in @($taskOutput,($taskOutput + '-launch.json'),($taskOutput + '-status.json'))) {
    if (Test-Path -LiteralPath $taskPath) { throw ('Refusing duplicate attempt: ' + $taskPath) }
  }
}
$taskCase = Resolve-TaskPath $Case
if (-not (Test-Path -LiteralPath $taskCase)) { throw 'Case source missing.' }
$taskPython = Join-Path $taskRepo 'toolchain/analysis-venv/Scripts/python.exe'
$taskTools = @('scripts/plot-wang2017-descent.py','scripts/plot_m5_cliff_comparison.py','scripts/collect-wang2017-evidence.py')
$taskHashes = @{}
foreach ($taskTool in $taskTools) { $taskHashes[$taskTool] = (Get-FileHash -LiteralPath (Join-Path $taskRepo $taskTool) -Algorithm SHA256).Hash }
New-Item -ItemType Directory -Force -Path (Split-Path $taskOutput -Parent) | Out-Null
if ($AttachRunning) {
  if (-not $IsWindows) { throw 'Monitor attachment is supported only on Windows PowerShell7.' }
  $taskRecord = Get-Content -LiteralPath ($taskOutput + '-status.json') -Raw | ConvertFrom-Json -AsHashtable
  if ($taskRecord.status -ne 'NATIVE_RUNNING') { throw 'Only a live native run can transfer monitors.' }
  if ((Resolve-TaskPath $taskRecord.output).TrimEnd('\','/') -ne $taskOutput -or
      (Resolve-TaskPath $taskRecord.case) -ne $taskCase) { throw 'Recorded output/case identity differs.' }
  if ($MaxWallHours -le $taskRecord.maxWallHours) { throw 'Attachment must extend the total original wall budget.' }
  $taskStarted = [DateTimeOffset]$taskRecord.startedUtc
  $taskDeadline = $taskStarted.ToUniversalTime().AddHours($MaxWallHours)
  if ($taskDeadline -le [DateTimeOffset]::UtcNow) { throw 'Proposed deadline has already expired.' }
  foreach ($taskTool in $taskTools) {
    if ($taskHashes[$taskTool] -ne $taskRecord.postprocessorSha256[$taskTool]) { throw ('Postprocessor changed: ' + $taskTool) }
  }
  $taskOldWrapper = Get-Process -Id ([int]$taskRecord.wrapperPid) -ErrorAction Stop
  $taskOldWrapperIdentity=Get-TaskProcessIdentity $taskOldWrapper
  $taskNative = Get-Process -Id ([int]$taskRecord.nativeCommandPid) -ErrorAction Stop
  if ($taskRecord.processIdentity) {
    Assert-TaskProcessIdentity $taskRecord.processIdentity.wrapper $taskOldWrapper
    Assert-TaskProcessIdentity $taskRecord.processIdentity.nativeCommand $taskNative
  }
  $taskNativeInfo = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $taskNative.Id)
  if ($taskNative.ProcessName -ne 'cmd' -or $taskNativeInfo.ParentProcessId -ne $taskOldWrapper.Id) {
    throw 'Native command process no longer belongs to the recorded monitor.'
  }
  if (-not $taskNativeInfo.CommandLine.Contains($taskOutput,[StringComparison]::OrdinalIgnoreCase) -or
      -not $taskNativeInfo.CommandLine.Contains($taskCase,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Native command line does not contain the recorded case/output paths.'
  }
  $taskWorkers = @(Get-CimInstance Win32_Process -Filter ('ParentProcessId=' + $taskNative.Id) |
    Where-Object Name -eq 'sbcl.exe')
  if ($taskWorkers.Count -ne 1) { throw 'Expected exactly one existing SBCL child; no process was stopped.' }
  $taskWorker = Get-Process -Id $taskWorkers[0].ProcessId -ErrorAction Stop
  if ($taskRecord.processIdentity) { Assert-TaskProcessIdentity $taskRecord.processIdentity.sbcl $taskWorker }
  foreach ($taskProcess in @($taskNative,$taskWorker)) {
    $taskProcessStart = [DateTimeOffset]$taskProcess.StartTime.ToUniversalTime()
    if ($taskProcessStart -lt $taskStarted.AddSeconds(-5) -or $taskProcessStart -gt $taskStarted.AddMinutes(1)) {
      throw 'Native process creation time differs from the original launch.'
    }
  }
  # Retain Windows process handles before predecessor exits, including exit code.
  $null = $taskNative.Handle
  $null = $taskWorker.Handle
  $null = $taskOldWrapper.Handle
  $taskNative.EnableRaisingEvents = $true
  $taskToken = [Guid]::NewGuid().ToString('N')
  $taskEventName = 'Local\MPM-Wang-Monitor-' + $PID + '-' + $taskToken
  $taskGate = [Threading.EventWaitHandle]::new($false,[Threading.EventResetMode]::ManualReset,$taskEventName)
  $taskReady = [ordered]@{
    status='READY_NOT_ACTIVE';createdUtc=[DateTime]::UtcNow.ToString('o');successorPid=$PID;previousWrapperPid=$taskOldWrapper.Id
    nativeCommandPid=$taskNative.Id;nativeStartUtc=$taskNative.StartTime.ToUniversalTime().ToString('o')
    sbclPid=$taskWorker.Id;sbclStartUtc=$taskWorker.StartTime.ToUniversalTime().ToString('o')
    activationEvent=$taskEventName;token=$taskToken;originalMaxWallHours=$taskRecord.maxWallHours
    proposedMaxWallHours=$MaxWallHours;deadlineUtc=$taskDeadline.ToString('o')
    supervisorSourceCommit=(git rev-parse HEAD).Trim();supervisorSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    processIdentity=@{wrapper=(Get-TaskProcessIdentity (Get-Process -Id $PID));nativeCommand=(Get-TaskProcessIdentity $taskNative);sbcl=(Get-TaskProcessIdentity $taskWorker)}
  }
  $taskReady | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($taskOutput + '-monitor-' + $PID + '-ready.json') -Encoding utf8
  try {
    if (-not $taskGate.WaitOne(60000)) { throw 'Monitor was not activated; original status remains unchanged.' }
    if (-not $taskOldWrapper.HasExited) { throw 'Previous monitor is still alive; refusing concurrent ownership.' }
  } finally { $taskGate.Dispose() }
  $taskRecord.previousWrapperPid=$taskOldWrapper.Id
  $taskRecord.originalMaxWallHours=$taskRecord.maxWallHours
  $taskRecord.wrapperPid=$PID
  $taskRecord.maxWallHours=$MaxWallHours
  $taskRecord.wallDeadlineUtc=$taskDeadline.ToString('o')
  $taskRecord.monitorTransfer=$taskReady
  $taskRecord.monitorTransferredUtc=[DateTime]::UtcNow.ToString('o')
  $taskRecord.previousWrapperIdentity=$taskOldWrapperIdentity
  $taskRecord.processIdentity=$taskReady.processIdentity
  $taskRecord.heartbeatIntervalSeconds=$HeartbeatSeconds
  if (-not $taskRecord.ContainsKey('heartbeatSequence')) { $taskRecord.heartbeatSequence=0 }
  Save-TaskStatus
} else {
$taskRecord = [ordered]@{
  startedUtc=[DateTime]::UtcNow.ToString('o'); sourceCommitAtLaunch=(git rev-parse HEAD).Trim()
  wrapperPid=$PID; case=$Case; caseSha256=(Get-FileHash -LiteralPath $taskCase -Algorithm SHA256).Hash
  output=$taskOutput; maxWallHours=$MaxWallHours; status='STARTING'; exitCode=$null
  postprocessorSha256=$taskHashes; scientificValidation=$false
  processIdentity=@{wrapper=(Get-TaskProcessIdentity (Get-Process -Id $PID));nativeCommand=$null;sbcl=$null}
  heartbeatIntervalSeconds=$HeartbeatSeconds;heartbeatSequence=0
}
$taskRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($taskOutput + '-launch.json') -Encoding utf8
Save-TaskStatus
}
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
try {
  if (-not $AttachRunning) {
  $taskCommand = 'call "' + (Join-Path $taskRepo 'windows/cl-mpm.cmd') + '" "' +
    (Join-Path $taskRepo 'scripts/run-case.lisp') + '" "' + $taskCase + '" "' + $taskOutput + '"'
  $taskNative = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput ($taskOutput + '.stdout.log') -RedirectStandardError ($taskOutput + '.stderr.log')
  $taskRecord.nativeCommandPid=$taskNative.Id
  $taskRecord.processIdentity.nativeCommand=Get-TaskProcessIdentity $taskNative
  $taskRecord.status='NATIVE_RUNNING'
  $taskDeadline = [DateTimeOffset]::UtcNow.AddHours($MaxWallHours)
  $taskRecord.wallDeadlineUtc=$taskDeadline.ToString('o')
  Update-TaskHeartbeat
  }
  $taskTimedOut=$false
  while (-not $taskNative.HasExited) {
    $taskRemainingMs = [Math]::Max(0,[Math]::Min([int]::MaxValue,($taskDeadline - [DateTimeOffset]::UtcNow).TotalMilliseconds))
    if ($taskRemainingMs -le 0) { $taskTimedOut=$true;break }
    $taskWaitMs=[int][Math]::Min($taskRemainingMs,($HeartbeatSeconds * 1000))
    if ($taskNative.WaitForExit($taskWaitMs)) { break }
    Update-TaskHeartbeat
  }
  Update-TaskHeartbeat
  if ($taskTimedOut) {
    Stop-NativeTree $taskNative.Id
    $taskRecord.status='STOPPED_WALL_BUDGET'
    $taskRecord.nativeExitCode=$null
    $taskRecord.nativeComplete=$false
    $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
    Save-TaskStatus
    exit 3
  }
  $taskNative.Refresh()
  $taskRecord.nativeExitCode=$taskNative.ExitCode
  $taskRecord.exitCode=$taskNative.ExitCode
  $taskRecord.nativeEndedUtc=[DateTime]::UtcNow.ToString('o')
  $taskManifestPath = Join-Path $taskOutput 'manifest.json'
  if (Test-Path -LiteralPath $taskManifestPath) {
    $taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
    $taskRecord.nativeComplete=$taskManifest.complete
    $taskRecord.timeS=$taskManifest.timeS
    $taskRecord.commandedSettlementM=$taskManifest.commandedSettlementM
    $taskRecord.measuredSettlementM=$taskManifest.measuredSettlementM
  }
  $taskRecord.status='NATIVE_FINISHED'
  Save-TaskStatus
  if ($taskNative.ExitCode -ne 0) { $taskRecord.status='FAILED_NATIVE'; Save-TaskStatus; exit $taskNative.ExitCode }
  if (-not $taskRecord.nativeComplete) { $taskRecord.status='INCOMPLETE_NATIVE'; Save-TaskStatus; exit 2 }
  foreach ($taskTool in $taskTools) {
    if ((Get-FileHash -LiteralPath (Join-Path $taskRepo $taskTool) -Algorithm SHA256).Hash -ne $taskHashes[$taskTool]) {
      throw ('Postprocessor changed during run: ' + $taskTool)
    }
  }
  $taskRecord.status='POSTPROCESSING'
  Save-TaskStatus
  & $taskPython (Join-Path $taskRepo 'scripts/plot-wang2017-descent.py') --run-dir $taskOutput --video *> ($taskOutput + '-plot.log')
  $taskRecord.auditAndRenderExitCode=$LASTEXITCODE
  Save-TaskStatus
  if ($LASTEXITCODE -ne 0) { throw 'Saved-output audit/render failed; inspect retained log.' }
  if ($EvidenceDirectory) {
    $taskEvidence = Resolve-TaskPath $EvidenceDirectory
    & $taskPython (Join-Path $taskRepo 'scripts/collect-wang2017-evidence.py') --run-dir $taskOutput --destination $taskEvidence *> ($taskOutput + '-collect.log')
    $taskRecord.collectionExitCode=$LASTEXITCODE
    Save-TaskStatus
    if ($LASTEXITCODE -ne 0) { throw 'Evidence collector failed; preserve partial output and inspect log.' }
  }
  $taskRecord.status='COMPLETED_REVIEW_PENDING'
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  Save-TaskStatus
} catch {
  $taskRecord.status='WRAPPER_OR_POSTPROCESS_FAILED'
  $taskRecord.error=$_.Exception.Message
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  Save-TaskStatus
  throw
}
