@echo off
setlocal
echo ========================================================
echo   CL-MPM Simulation Studio (Windows Native)
echo ========================================================
echo.
echo Menjalankan Web UI Server di port 3000...
echo.

set MINGW_DIR=C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin
set GNUPLOT_DIR=C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\gnuplot.gnuplot_Microsoft.Winget.Source_8wekyb3d8bbwe\gnuplot\bin
set PATH=C:\Program Files\Steel Bank Common Lisp;%MINGW_DIR%;D:\MPM\openblas\bin;%GNUPLOT_DIR%;D:\MPM\libs;D:\MPM;%PATH%

start "" http://localhost:3000

node "d:\MPM\server.js"
pause
