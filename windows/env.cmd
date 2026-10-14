@echo off
rem ---------------------------------------------------------------------------
rem  env.cmd - locate the tools CL-MPM needs and put them on PATH.
rem
rem  Called by the other windows\*.cmd scripts (call "%~dp0env.cmd").
rem  Nothing is hardcoded to a user profile: each tool is taken from an
rem  override variable, then PATH, then common install locations.
rem
rem  Overrides (set before calling, or in windows\env.local.cmd):
rem    CL_MPM_SBCL      full path to sbcl.exe
rem    CL_MPM_GNUPLOT   directory containing gnuplot.exe
rem    CL_MPM_FFMPEG    directory containing ffmpeg.exe
rem    CL_MPM_HEAP_MB   SBCL dynamic space size in MB (default 4000)
rem
rem  Exports: CL_MPM_ROOT, CL_MPM_SBCL, CL_MPM_HEAP_MB and an extended PATH.
rem ---------------------------------------------------------------------------

for %%I in ("%~dp0..") do set "CL_MPM_ROOT=%%~fI"

if exist "%~dp0env.local.cmd" call "%~dp0env.local.cmd"

if not defined CL_MPM_HEAP_MB set "CL_MPM_HEAP_MB=4000"

rem --- SBCL ------------------------------------------------------------------
if not defined CL_MPM_SBCL (
    for /f "delims=" %%S in ('where sbcl 2^>nul') do if not defined CL_MPM_SBCL set "CL_MPM_SBCL=%%S"
)
if not defined CL_MPM_SBCL if exist "%ProgramFiles%\Steel Bank Common Lisp\sbcl.exe" (
    set "CL_MPM_SBCL=%ProgramFiles%\Steel Bank Common Lisp\sbcl.exe"
)
if not defined CL_MPM_SBCL (
    echo [env] SBCL not found. Install it with:  winget install SBCL.SBCL
    echo       or set CL_MPM_SBCL to the full path of sbcl.exe.
    exit /b 1
)

rem --- gnuplot (optional: PNG frames / live plots) ---------------------------
rem  The WinGet "Links\gnuplot.exe" alias cannot start gnuplot when spawned from
rem  SBCL (DLL not found), so the real install directory is preferred.
if not defined CL_MPM_GNUPLOT (
    for /d %%G in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\gnuplot.gnuplot_*") do (
        if exist "%%~G\gnuplot\bin\gnuplot.exe" set "CL_MPM_GNUPLOT=%%~G\gnuplot\bin"
    )
)
if not defined CL_MPM_GNUPLOT if exist "%ProgramFiles%\gnuplot\bin\gnuplot.exe" (
    set "CL_MPM_GNUPLOT=%ProgramFiles%\gnuplot\bin"
)
if defined CL_MPM_GNUPLOT set "PATH=%CL_MPM_GNUPLOT%;%PATH%"

rem --- ffmpeg (optional: video export) ---------------------------------------
if not defined CL_MPM_FFMPEG (
    where ffmpeg >nul 2>nul || (
        for /d %%F in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
            for /d %%B in ("%%~F\ffmpeg-*") do if exist "%%~B\bin\ffmpeg.exe" set "CL_MPM_FFMPEG=%%~B\bin"
        )
    )
)
if defined CL_MPM_FFMPEG set "PATH=%CL_MPM_FFMPEG%;%PATH%"

rem --- Native libraries (OpenBLAS, kirchoff.dll) -----------------------------
set "PATH=%CL_MPM_ROOT%\toolchain\openblas\bin;%CL_MPM_ROOT%\libs;%PATH%"

exit /b 0
