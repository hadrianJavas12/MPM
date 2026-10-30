param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [Parameter(Mandatory=$true)][string]$Case,
  [double]$MaxWallHours = 3,
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
  $taskManifestPath = Join-Path $taskOutput 'manifest.json'
  if (Test-Path -LiteralPath $taskManifestPath) {
    try {
      $taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json -AsHashtable
      $taskStatus.progress = @{}
      foreach ($taskKey in @('status','complete','phase','timeS','updates','savedFrames','particleCount')) {
        if ($taskManifest.ContainsKey($taskKey)) { $taskStatus.progress[$taskKey] = $taskManifest[$taskKey] }
      }
    } catch { $taskStatus.manifestReadError = $_.Exception.Message }
  }
  if ($taskNative -and -not $taskNative.HasExited -and -not $taskStatus.processIdentity.sbcl) {
    $taskChildren = @(Get-CimInstance Win32_Process -Filter ('ParentProcessId='+$taskNative.Id) | Where-Object Name -eq 'sbcl.exe')
    if ($taskChildren.Count -eq 1) {
      try { $taskStatus.processIdentity.sbcl = Get-TaskIdentity (Get-Process -Id $taskChildren[0].ProcessId -ErrorAction Stop) }
      catch { $taskStatus.identityReadError = $_.Exception.Message }
    }
  }
  $taskJson = $taskStatus | ConvertTo-Json -Depth 10
  for ($taskRetry=0; $taskRetry -lt 20; $taskRetry++) {
    try {
      [IO.File]::WriteAllText(($taskOutput+'-status.json'),$taskJson,[Text.UTF8Encoding]::new($false))
      return
    } catch [IO.IOException] {
      if ($taskRetry -eq 19) { throw }
      Start-Sleep -Milliseconds 100
    }
  }
}
$taskOutput = (Resolve-TaskPath $OutputDirectory).TrimEnd('\','/')
$taskCase = Resolve-TaskPath $Case
$taskOutputRoot = [IO.Path]::GetFullPath((Join-Path $taskRepo 'output')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskOutput.StartsWith($taskOutputRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be a fresh workspace/output subdirectory.' }
if (-not [double]::IsFinite($MaxWallHours) -or $MaxWallHours -le 0 -or $MaxWallHours -gt 72) { throw 'Wall budget must be finite and in (0,72] hours.' }
if (-not (Test-Path -LiteralPath $taskCase -PathType Leaf)) { throw 'Trusted case source is missing.' }
foreach ($taskPath in @($taskOutput,($taskOutput+'-status.json'),($taskOutput+'-launch.json'))) {
  if (Test-Path -LiteralPath $taskPath) { throw ('Refusing duplicate attempt: '+$taskPath) }
}
New-Item -ItemType Directory -Force -Path (Split-Path $taskOutput -Parent) | Out-Null
$taskStarted = [DateTime]::UtcNow
$taskStatus = [ordered]@{
  scenario='gravity-slope';status='STARTING';startedUtc=$taskStarted.ToString('o');output=$taskOutput;case=$taskCase
  sourceCommit=(git rev-parse HEAD).Trim();maxWallHours=$MaxWallHours;wallDeadlineUtc=$taskStarted.AddHours($MaxWallHours).ToString('o')
  caseSha256=(Get-FileHash -LiteralPath $taskCase -Algorithm SHA256).Hash
  wrapperSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
  processIdentity=@{wrapper=(Get-TaskIdentity (Get-Process -Id $PID));nativeCommand=$null;sbcl=$null}
  nativeExitCode=$null;nativeComplete=$false;scientificValidation=$false;landslideVerified=$false;progress=@{}
}
$taskNative = $null
$taskStatus | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath ($taskOutput+'-launch.json') -Encoding utf8
Save-TaskStatus
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
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
      # Retained process handle identifies this exact command; kill its tree,
      # not a PID obtained by a later unrelated enumeration.
      $taskNative.Kill($true)
      $taskNative.WaitForExit()
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
  $taskStatus.nativeComplete = [bool]$taskStatus.progress.complete
  if ($taskNative.ExitCode -ne 0) { $taskStatus.status='FAILED_NATIVE'; Save-TaskStatus; exit $taskNative.ExitCode }
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
