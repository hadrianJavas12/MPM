@echo off
rem Run from any Windows working directory; output must be a fresh directory.
setlocal
for %%I in ("%~dp0..") do set "TRIAXIAL_ROOT=%%~fI"
set "TRIAXIAL_CONFIG=%~1"
set "TRIAXIAL_OUTPUT=%~2"
if not defined TRIAXIAL_CONFIG set "TRIAXIAL_CONFIG=%~dp0triaxial-demo.json"
if not defined TRIAXIAL_OUTPUT set "TRIAXIAL_OUTPUT=%TRIAXIAL_ROOT%\output\triaxial-demo"
call "%TRIAXIAL_ROOT%\windows\cl-mpm.cmd" "%TRIAXIAL_ROOT%\scripts\run-triaxial.lisp" "%TRIAXIAL_CONFIG%" "%TRIAXIAL_OUTPUT%"
exit /b %ERRORLEVEL%
