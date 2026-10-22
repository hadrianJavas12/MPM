param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [string]$Case = 'cases/benchmarks/clay-creep-slope-pilot.lisp',
  [double]$MaxWallHours = 1
)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $taskRepo
function Resolve-TaskPath([string]$Path) {
  if ($Path.Contains('"')) { throw 'Quotes are unsupported in paths.' }
  if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
  return [IO.Path]::GetFullPath((Join-Path $taskRepo $Path))
}
function Save-TaskStatus {
  $taskRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($taskOutput + '-status.json') -Encoding utf8
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
if (-not $taskOutput.StartsWith($taskOutputRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Use a fresh workspace/output subdirectory.' }
if ($MaxWallHours -le 0 -or $MaxWallHours -gt 24) { throw 'Wall budget must be in (0,24] hours.' }
foreach ($taskPath in @($taskOutput,($taskOutput + '-status.json'),($taskOutput + '-launch.json'))) {
  if (Test-Path -LiteralPath $taskPath) { throw ('Refusing duplicate output: ' + $taskPath) }
}
$taskCase = Resolve-TaskPath $Case
$taskPython = Join-Path $taskRepo 'toolchain/analysis-venv/Scripts/python.exe'
$taskTools = @('scripts/plot-slope-creep.py','scripts/plot_m5_cliff_comparison.py')
$taskHashes = @{}
foreach ($taskTool in $taskTools) { $taskHashes[$taskTool] = (Get-FileHash -LiteralPath (Join-Path $taskRepo $taskTool)).Hash }
New-Item -ItemType Directory -Force -Path (Split-Path $taskOutput -Parent) | Out-Null
$taskRecord = [ordered]@{startedUtc=[DateTime]::UtcNow.ToString('o'); sourceCommitAtLaunch=(git rev-parse HEAD).Trim()
  case=$Case; caseSha256=(Get-FileHash -LiteralPath $taskCase).Hash; output=$taskOutput
  maxWallHours=$MaxWallHours; wrapperPid=$PID; status='STARTING'; nativeExitCode=$null
  nativeComplete=$false; analysisSha256=$taskHashes; scientificValidation=$false}
$taskRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($taskOutput + '-launch.json') -Encoding utf8
Save-TaskStatus
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
try {
  $taskCommand = 'call "' + (Join-Path $taskRepo 'windows/cl-mpm.cmd') + '" "' +
    (Join-Path $taskRepo 'scripts/run-case.lisp') + '" "' + $taskCase + '" "' + $taskOutput + '"'
  $taskNative = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput ($taskOutput + '.stdout.log') -RedirectStandardError ($taskOutput + '.stderr.log')
  $taskRecord.nativeCommandPid=$taskNative.Id
  $taskRecord.status='NATIVE_RUNNING'
  Save-TaskStatus
  if (-not $taskNative.WaitForExit([int]($MaxWallHours * 3600000))) {
    Stop-NativeTree $taskNative.Id
    $taskRecord.status='STOPPED_WALL_BUDGET'
    $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
    Save-TaskStatus
    exit 3
  }
  $taskNative.Refresh()
  $taskRecord.nativeExitCode=$taskNative.ExitCode
  $taskRecord.nativeEndedUtc=[DateTime]::UtcNow.ToString('o')
  $taskManifest = Get-Content -LiteralPath (Join-Path $taskOutput 'manifest.json') -Raw | ConvertFrom-Json
  $taskRecord.nativeComplete=$taskManifest.complete
  $taskRecord.timeS=$taskManifest.timeS
  if ($taskNative.ExitCode -ne 0) { $taskRecord.status='FAILED_NATIVE'; Save-TaskStatus; exit $taskNative.ExitCode }
  if (-not $taskManifest.complete) { $taskRecord.status='INCOMPLETE_NATIVE'; Save-TaskStatus; exit 2 }
  foreach ($taskTool in $taskTools) {
    if ((Get-FileHash -LiteralPath (Join-Path $taskRepo $taskTool)).Hash -ne $taskHashes[$taskTool]) { throw 'Analysis tool changed during run.' }
  }
  $taskRecord.status='POSTPROCESSING'
  Save-TaskStatus
  & $taskPython (Join-Path $taskRepo 'scripts/plot-slope-creep.py') --run-dir $taskOutput --video *> ($taskOutput + '-plot.log')
  $taskRecord.auditAndRenderExitCode=$LASTEXITCODE
  if ($LASTEXITCODE -ne 0) { throw 'Native output audit/render failed; reuse saved data for repairs.' }
  $taskRecord.status='COMPLETED_REVIEW_PENDING'
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  Save-TaskStatus
} catch {
  $taskRecord.status='WRAPPER_OR_POSTPROCESS_FAILED'
  $taskRecord.error=$_.Exception.Message
  Save-TaskStatus
  throw
}
