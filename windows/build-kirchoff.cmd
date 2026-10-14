@echo off
rem ---------------------------------------------------------------------------
rem  build-kirchoff.cmd - build libs\kirchoff.dll (accelerated C++ strain update)
rem
rem  Windows counterpart of libs/build.sh. Requires MinGW-w64 g++ and Eigen 3.
rem  The DLL is linked statically against libstdc++/libgcc so it can be loaded
rem  without MinGW on PATH.
rem
rem  Eigen lookup order: %EIGEN_DIR%, libs\eigen_src\eigen-3.4.0
rem  Usage: windows\build-kirchoff.cmd
rem ---------------------------------------------------------------------------
setlocal
call "%~dp0env.cmd" || exit /b 1

if not defined EIGEN_DIR set "EIGEN_DIR=%CL_MPM_ROOT%\libs\eigen_src\eigen-3.4.0"
if not exist "%EIGEN_DIR%\Eigen\Dense" (
    echo [build-kirchoff] Eigen not found at "%EIGEN_DIR%".
    echo   Download https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
    echo   and extract it to libs\eigen_src\ or set EIGEN_DIR.
    exit /b 1
)

where g++ >nul 2>nul || (
    echo [build-kirchoff] g++ not found. Install MinGW-w64, e.g.:
    echo   winget install BrechtSanders.WinLibs.POSIX.UCRT
    exit /b 1
)

pushd "%CL_MPM_ROOT%\libs"
echo [build-kirchoff] Compiling libs\kirchoff.dll ...
g++ -O3 -march=native -shared -static -static-libgcc -static-libstdc++ ^
    -I "%EIGEN_DIR%" test.cpp -o kirchoff.dll
set "RC=%ERRORLEVEL%"
popd

if not "%RC%"=="0" (
    echo [build-kirchoff] FAILED with exit code %RC%.
    exit /b %RC%
)
echo [build-kirchoff] OK: libs\kirchoff.dll
