param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [Parameter(Mandatory=$true)][string]$Case,
  [double]$MaxWallHours = 12,
  [double]$ExpectedSimulationTimeS = 60,
  [ValidateRange(1,3600)][int]$HeartbeatSeconds = 60
)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $taskRepo
function Resolve-TaskPath([string]$Path) {
  if ($Path.IndexOfAny([char[]]@('"',"`r","`n")) -ge 0) { throw 'Quotes/newlines in paths are unsupported.' }
  if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
  [IO.Path]::GetFullPath((Join-Path $taskRepo $Path))
}
function Get-TaskIdentity([Diagnostics.Process]$Process) {
  [ordered]@{pid=$Process.Id;name=$Process.ProcessName;sessionId=$Process.SessionId;createdUtc=$Process.StartTime.ToUniversalTime().ToString('o')}
}
function Save-TaskStatus {
  $taskStatus.heartbeatUtc = [DateTime]::UtcNow.ToString('o')
  $taskCsv = Join-Path $taskOutput 'timesteps.csv'
  if (Test-Path -LiteralPath $taskCsv -PathType Leaf) {
    try {
      $taskHeader = Get-Content -LiteralPath $taskCsv -TotalCount 1
      $taskLast = Get-Content -LiteralPath $taskCsv -Tail 1
      if ($taskLast -and $taskLast -ne $taskHeader) {
        $taskRow = @($taskHeader,$taskLast) | ConvertFrom-Csv
        if ($taskRow.step -and $taskRow.time -and $taskRow.phase) {
          $taskStatus.progress = [ordered]@{phase=$taskRow.phase;timeS=$taskRow.time;step=$taskRow.step;preparationTimeS=$taskRow.preparationTime;massDamage=$taskRow.massDamage;particleCount=$taskRow.particles;massScale=$taskRow.massScale}
        }
      }
    } catch { $taskStatus.progressReadError = $_.Exception.Message }
  }
  $taskMetadata = Join-Path $taskOutput 'reference-metadata.json'
  if (Test-Path -LiteralPath $taskMetadata -PathType Leaf) {
    try {
      $taskRecord = Get-Content -LiteralPath $taskMetadata -Raw | ConvertFrom-Json -AsHashtable
      $taskStatus.metadata = @{}
      foreach ($taskKey in @('complete','termination','physicalTime','requestedSimulationTime','phase','frames','equilibrationSteps')) {
        if ($taskRecord.ContainsKey($taskKey)) { $taskStatus.metadata[$taskKey] = $taskRecord[$taskKey] }
      }
    } catch { $taskStatus.metadataReadError = $_.Exception.Message }
  }
  if ($taskNative -and -not $taskNative.HasExited -and -not $taskStatus.processIdentity.sbcl) {
    $taskChildren = @(Get-CimInstance Win32_Process -Filter ('ParentProcessId='+$taskNative.Id) | Where-Object Name -eq 'sbcl.exe')
    if ($taskChildren.Count -eq 1) {
      try { $taskStatus.processIdentity.sbcl = Get-TaskIdentity (Get-Process -Id $taskChildren[0].ProcessId -ErrorAction Stop) }
      catch { $taskStatus.identityReadError = $_.Exception.Message }
    }
  }
  $taskStatus | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath ($taskOutput+'-status.json') -Encoding utf8
}
$taskOutput = (Resolve-TaskPath $OutputDirectory).TrimEnd('\','/')
$taskCase = Resolve-TaskPath $Case
$taskOutputRoot = [IO.Path]::GetFullPath((Join-Path $taskRepo 'output')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskOutputRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be a fresh workspace/output subdirectory.' }
if (-not [double]::IsFinite($MaxWallHours) -or $MaxWallHours -le 0 -or $MaxWallHours -gt 72) { throw 'Wall budget must be finite and in (0,72] hours.' }
if (-not [double]::IsFinite($ExpectedSimulationTimeS) -or $ExpectedSimulationTimeS -le 0) { throw 'Expected physical duration must be positive and finite.' }
if (-not (Test-Path -LiteralPath $taskCase -PathType Leaf)) { throw 'Trusted case source is missing.' }
foreach ($taskPath in @($taskOutput,($taskOutput+'-status.json'),($taskOutput+'-launch.json'),($taskOutput+'.stdout.log'),($taskOutput+'.stderr.log'))) {
  if (Test-Path -LiteralPath $taskPath) { throw ('Refusing duplicate attempt: '+$taskPath) }
}
New-Item -ItemType Directory -Force -Path (Split-Path $taskOutput -Parent) | Out-Null
$taskStarted = [DateTime]::UtcNow
$taskStatus = [ordered]@{
  scenario='damage-slope40';status='STARTING';startedUtc=$taskStarted.ToString('o');output=$taskOutput;case=$taskCase
  sourceCommit=(git rev-parse HEAD).Trim();maxWallHours=$MaxWallHours;wallDeadlineUtc=$taskStarted.AddHours($MaxWallHours).ToString('o')
  expectedSimulationTimeS=$ExpectedSimulationTimeS
  caseSha256=(Get-FileHash -LiteralPath $taskCase -Algorithm SHA256).Hash
  wrapperSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
  processIdentity=@{worker=$null;wrapper=(Get-TaskIdentity (Get-Process -Id $PID));nativeCommand=$null;sbcl=$null}
  nativeExitCode=$null;nativeComplete=$false;scientificValidation=$false;landslideVerified=$false;progress=@{};metadata=@{}
}
# The detached worker's retained creation clock must match this wrapper's parent.
$taskWorkerPath = Join-Path ($taskOutput+'-detached') 'worker-start.json'
if (Test-Path -LiteralPath $taskWorkerPath -PathType Leaf) {
  $taskWorker = Get-Content -LiteralPath $taskWorkerPath -Raw | ConvertFrom-Json
  $taskSelf = Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
  if ($taskSelf.ParentProcessId -ne $taskWorker.processId) { throw 'Detached worker is not this wrapper parent.' }
  $taskParent = Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskWorker.processId)
  if (-not $taskParent -or $taskParent.SessionId -ne $taskWorker.sessionId -or
      $taskParent.CreationDate.ToUniversalTime().ToString('o') -ne $taskWorker.creationUtc) { throw 'Detached worker identity changed.' }
  $taskStatus.processIdentity.worker = $taskWorker
}
$taskNative = $null
$taskStatus | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath ($taskOutput+'-launch.json') -Encoding utf8
Save-TaskStatus
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:CL_MPM_REFERENCE_PNG = '0'
try {
  $taskCommand = 'call "'+(Join-Path $taskRepo 'windows/cl-mpm.cmd')+'" "'+(Join-Path $taskRepo 'scripts/run-case.lisp')+'" "'+$taskCase+'" "'+$taskOutput+'"'
  $taskNative = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput ($taskOutput+'.stdout.log') -RedirectStandardError ($taskOutput+'.stderr.log')
  $null = $taskNative.Handle
  $taskStatus.processIdentity.nativeCommand = Get-TaskIdentity $taskNative
  $taskStatus.status = 'NATIVE_RUNNING'
  Save-TaskStatus
  while (-not $taskNative.HasExited) {
    $taskRemainingMs = ($taskStarted.AddHours($MaxWallHours)-[DateTime]::UtcNow).TotalMilliseconds
    if ($taskRemainingMs -le 0) {
      # The retained handle belongs to this exact owned command; never kill by a later PID lookup.
      $taskNative.Kill($true)
      $taskNative.WaitForExit()
      $taskNative.Refresh()
      $taskStatus.nativeExitCode = $taskNative.ExitCode
      $taskStatus.status = 'STOPPED_WALL_BUDGET'
      $taskStatus.endedUtc = [DateTime]::UtcNow.ToString('o')
      Save-TaskStatus
      exit 3
    }
    if ($taskNative.WaitForExit([int][Math]::Min($taskRemainingMs,1000*$HeartbeatSeconds))) { break }
    Save-TaskStatus
  }
  $taskNative.Refresh()
  $taskStatus.nativeExitCode = $taskNative.ExitCode
  $taskStatus.endedUtc = [DateTime]::UtcNow.ToString('o')
  Save-TaskStatus
  if ($taskNative.ExitCode -ne 0) { $taskStatus.status='FAILED_NATIVE'; Save-TaskStatus; exit $taskNative.ExitCode }
  $taskMetadata = $taskStatus.metadata
  $taskStatus.nativeComplete = ($taskMetadata.complete -is [bool] -and $taskMetadata.complete -eq $true -and
    $taskMetadata.termination -eq 'simulation-time' -and
    $null -ne $taskMetadata.physicalTime -and $null -ne $taskMetadata.requestedSimulationTime -and
    [double]::IsFinite([double]$taskMetadata.physicalTime) -and [double]::IsFinite([double]$taskMetadata.requestedSimulationTime) -and
    [double]$taskMetadata.requestedSimulationTime -eq $ExpectedSimulationTimeS -and [double]$taskMetadata.physicalTime -ge $ExpectedSimulationTimeS)
  if (-not $taskStatus.nativeComplete) { $taskStatus.status='INCOMPLETE_NATIVE'; Save-TaskStatus; exit 2 }
  $taskStatus.status = 'NATIVE_COMPLETE_REVIEW_PENDING'
  Save-TaskStatus
} catch {
  $taskStatus.status = 'WRAPPER_FAILED'
  $taskStatus.error = $_.Exception.Message
  $taskStatus.endedUtc = [DateTime]::UtcNow.ToString('o')
  Save-TaskStatus
  throw
}
