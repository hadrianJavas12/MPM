param(
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [string]$Case = 'cases/benchmarks/gravity-slope-mc-srf-1p4.lisp',
  [double]$MaxWallHours = 3,
  [ValidateRange(1,60)][int]$StartupTimeoutSeconds = 30,
  [switch]$LaunchControlFixture
)
# Reuse the established CIM process/identity/provenance launcher. Its historical
# Wang name remains compatible; the default runner for old callers is unchanged.
$taskArguments = @{OutputDirectory=$OutputDirectory;Case=$Case;MaxWallHours=$MaxWallHours;
  StartupTimeoutSeconds=$StartupTimeoutSeconds;Runner='gravity-slope'}
if ($LaunchControlFixture) { $taskArguments.LaunchControlFixture=$true }
& (Join-Path $PSScriptRoot 'start-wang2017-detached.ps1') @taskArguments
