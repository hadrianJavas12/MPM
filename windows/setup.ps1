<#
.SYNOPSIS
  One-time (idempotent) setup of the CL-MPM toolchain on native Windows.

.DESCRIPTION
  Installs what the project needs, entirely inside the repository where possible:
    toolchain\quicklisp   Quicklisp (Lisp library manager)
    toolchain\openblas    OpenBLAS (BLAS/LAPACK DLL used by MAGICL)
  and checks / installs through winget: SBCL, Node.js, gnuplot, ffmpeg.
  Optionally builds libs\kirchoff.dll with MinGW (-BuildKirchoff).

  Safe to re-run: every step is skipped when it is already done.

.PARAMETER SkipWinget
  Do not install SBCL / Node / gnuplot / ffmpeg with winget (only report them).
.PARAMETER BuildKirchoff
  Also compile libs\kirchoff.dll (needs g++ and Eigen, see windows\build-kirchoff.cmd).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File windows\setup.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipWinget,
    [switch]$BuildKirchoff
)

$ErrorActionPreference = 'Stop'
$Root      = Split-Path -Parent $PSScriptRoot
$Toolchain = Join-Path $Root 'toolchain'
$OpenBlasVersion = '0.3.34'
$OpenBlasUrl = "https://github.com/OpenMathLib/OpenBLAS/releases/download/v$OpenBlasVersion/OpenBLAS-$OpenBlasVersion-x64.zip"

function Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    ok: $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    !! $msg" -ForegroundColor Yellow }

function Test-Tool($name, [string[]]$extraPaths = @()) {
    if (Get-Command $name -ErrorAction SilentlyContinue) { return $true }
    foreach ($p in $extraPaths) { if (Test-Path $p) { return $true } }
    return $false
}

function Install-WingetPackage($id, $label) {
    if ($SkipWinget) { Warn "$label missing (winget install $id)"; return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Warn "$label missing and winget is unavailable - install it manually"; return
    }
    Step "Installing $label with winget"
    winget install --id $id -e --accept-source-agreements --accept-package-agreements
}

function Install-Quicklisp([string]$sbcl, [string]$quicklisp) {
    $installDir = Split-Path -Parent $quicklisp
    $installer = Join-Path $installDir 'quicklisp-install.lisp'
    $bootstrap = Join-Path $installDir 'quicklisp-bootstrap.lisp'
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    try {
        Invoke-WebRequest 'https://beta.quicklisp.org/quicklisp.lisp' -OutFile $installer
        # Pass Lisp through a file instead of --eval: PowerShell does not use
        # backslash to escape quotes, and Windows argument quoting differs
        # between PowerShell versions. Forward slashes also avoid Lisp escapes.
        $path = ($quicklisp.Replace('\', '/') + '/').Replace('"', '\"')
        $source = '(quicklisp-quickstart:install :path "{0}")' -f $path
        [System.IO.File]::WriteAllText($bootstrap, $source, [System.Text.UTF8Encoding]::new($false))
        & $sbcl --noinform --no-sysinit --no-userinit --non-interactive --load $installer --load $bootstrap
        if ($LASTEXITCODE -ne 0) { throw "Quicklisp installer exited with code $LASTEXITCODE." }
        if (-not (Test-Path (Join-Path $quicklisp 'setup.lisp'))) { throw 'Quicklisp installation failed.' }
    } finally {
        Remove-Item -LiteralPath $installer, $bootstrap -ErrorAction SilentlyContinue
    }
}

New-Item -ItemType Directory -Force -Path $Toolchain | Out-Null

# --- 1. External tools ------------------------------------------------------
Step 'Checking tools'
$sbclPaths = @("$env:ProgramFiles\Steel Bank Common Lisp\sbcl.exe")
if (Test-Tool 'sbcl' $sbclPaths) { Ok 'SBCL' } else { Install-WingetPackage 'SBCL.SBCL' 'SBCL' }

if (Test-Tool 'node') { Ok 'Node.js' } else { Install-WingetPackage 'OpenJS.NodeJS.LTS' 'Node.js (only needed for CL-MPM Studio)' }

$gnuplotPkg = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter 'gnuplot.gnuplot_*' -ErrorAction SilentlyContinue
if ($gnuplotPkg -or (Test-Path "$env:ProgramFiles\gnuplot\bin\gnuplot.exe")) { Ok 'gnuplot' }
else { Install-WingetPackage 'gnuplot.gnuplot' 'gnuplot (PNG frames)' }

if (Test-Tool 'ffmpeg') { Ok 'ffmpeg' } else { Install-WingetPackage 'Gyan.FFmpeg' 'ffmpeg (video export)' }

# --- 2. Quicklisp -----------------------------------------------------------
$quicklisp = Join-Path $Toolchain 'quicklisp'
Step 'Quicklisp'
if ((Test-Path (Join-Path $quicklisp 'setup.lisp')) -or (Test-Path (Join-Path $HOME 'quicklisp\setup.lisp'))) {
    Ok 'already installed'
} else {
    $sbcl = (Get-Command sbcl -ErrorAction SilentlyContinue).Source
    if (-not $sbcl) { $sbcl = $sbclPaths | Where-Object { Test-Path $_ } | Select-Object -First 1 }
    if (-not $sbcl) { throw 'SBCL is required to install Quicklisp. Install it and re-run this script.' }
    Install-Quicklisp $sbcl $quicklisp
    Ok "installed in $quicklisp"
}

# --- 3. OpenBLAS ------------------------------------------------------------
$openblas = Join-Path $Toolchain 'openblas'
$dll = Join-Path $openblas 'bin\libopenblas.dll'
Step "OpenBLAS $OpenBlasVersion"
if (Test-Path $dll) {
    Ok 'already installed'
} else {
    $zip = Join-Path $Toolchain 'openblas.zip'
    Invoke-WebRequest $OpenBlasUrl -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $openblas -Force
    Remove-Item $zip
    if (-not (Test-Path $dll)) { throw "libopenblas.dll not found in the archive (expected $dll)." }
    Ok "installed in $openblas"
}

# --- 4. kirchoff.dll (optional) --------------------------------------------
if ($BuildKirchoff) {
    Step 'Building libs\kirchoff.dll'
    & (Join-Path $PSScriptRoot 'build-kirchoff.cmd')
    if ($LASTEXITCODE -ne 0) { throw 'build-kirchoff.cmd failed.' }
}

Write-Host ''
Write-Host 'Setup finished. Verify with:' -ForegroundColor Green
Write-Host '    windows\cl-mpm.cmd scripts\smoke-test.lisp'
Write-Host 'Start the web UI with:'
Write-Host '    studio\start-studio.cmd'
