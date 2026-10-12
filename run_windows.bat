@echo off
setlocal

:: Setup PATH for SBCL, MinGW GCC, OpenBLAS, Gnuplot, and local libraries
set "GNUPLOT_DIR=C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\gnuplot.gnuplot_Microsoft.Winget.Source_8wekyb3d8bbwe\gnuplot\bin"
set "MINGW_DIR=C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin"
set "PATH=C:\Program Files\Steel Bank Common Lisp;%MINGW_DIR%;D:\MPM\openblas\bin;%GNUPLOT_DIR%;D:\MPM\libs;D:\MPM;%PATH%"

if "%~1"=="" (
    echo [CL-MPM] Menjalankan script simulasi default: run.lisp...
    sbcl --dynamic-space-size 4000 --no-userinit --load "D:\MPM\init.lisp" --load "D:\MPM\run.lisp"
) else (
    echo [CL-MPM] Menjalankan file simulasi: %*
    sbcl --dynamic-space-size 4000 --no-userinit --load "D:\MPM\init.lisp" --load "%~1" -- %2 %3 %4 %5 %6 %7 %8 %9
)
