param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference='Stop'
$run=[IO.Path]::GetFullPath($RunDirectory).TrimEnd('\','/')
$sidecar=$run+'-process-reconciliation.json'
if(Test-Path -LiteralPath $sidecar) { throw 'Refusing to overwrite prior reconciliation' }
$statusPath=$run+'-status.json'
$status=Get-Content -LiteralPath $statusPath -Raw|ConvertFrom-Json
$manifest=Get-Content -LiteralPath (Join-Path $run 'manifest.json') -Raw|ConvertFrom-Json
$identities=@()
foreach($role in @(@{role='wrapper';id=$status.wrapperPid},@{role='command';id=$status.nativeCommandPid},@{role='historicalSBCL';id=25128})) {
  $found=Get-Process -Id $role.id -ErrorAction SilentlyContinue
  if($found) { throw ('Recorded PID is now present; inspect creation time before classifying interruption: '+$role.id) }
  $identities+=@{role=$role.role;pid=$role.id;presentAtObservation=$false}
}
$files=@('manifest.json','force-displacement.csv','energy-history.csv','gravity-history.csv')|ForEach-Object {
  $p=Get-Item -LiteralPath (Join-Path $run $_)
  @{path=$_;sha256=(Get-FileHash -LiteralPath $p.FullName).Hash.ToLowerInvariant();lastWriteUtc=$p.LastWriteTimeUtc.ToString('o');bytes=$p.Length}
}
$result=[ordered]@{
  observedUtc=[DateTime]::UtcNow.ToString('o');classification='INTERRUPTED_UNKNOWN_EXIT';nativeExitCode=$null
  originalAdjacentStatus=$status.status;originalStatusSha256=(Get-FileHash -LiteralPath $statusPath).Hash.ToLowerInvariant()
  processObservations=$identities;nativeComplete=[bool]$manifest.complete;gravityConverged=[bool]$manifest.gravityConverged
  lastSavedPhase=$manifest.phase;lastSavedTimeS=$manifest.timeS;lastSavedCommandedSettlementM=$manifest.commandedSettlementM
  lastSavedLoadingUpdates=$manifest.loadingUpdates;sourceCommitAtLaunch=$status.sourceCommitAtLaunch;files=$files
  evidenceInterpretation='Wrapper/cmd/SBCL absent. No native exit, failure capsule or controlled terminal status. Session10 logoff15:23:15WIB and sleep/resume correlate with last artifacts15:22:31; historical process SessionId was not captured. Cause remains unproven.'
  stdoutIsPhysicalProgress=$false;wallBudgetTerminationProven=$false;materialFailureProven=$false
  restartCapability='No complete-state MPM restart checkpoint; VTK/CSV cannot resume this solver. Any retry starts fresh.'
  scientificValidation=$false
}
$result|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $sidecar -Encoding utf8
$result|Select-Object classification,lastSavedPhase,lastSavedTimeS,lastSavedCommandedSettlementM,nativeExitCode,nativeComplete|ConvertTo-Json -Compress
