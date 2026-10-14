@echo off
rem ---------------------------------------------------------------------------
rem  cl-mpm.cmd - run a Lisp script (or a REPL) with CL-MPM ready to load.
rem
rem  Usage:
rem    windows\cl-mpm.cmd                      interactive REPL
rem    windows\cl-mpm.cmd script.lisp [args]   run a script, args after "--"
rem
rem  Inside the script:  (ql:quickload :cl-mpm)  and  (cl-user:cl-mpm-path "...")
rem  Script arguments are available via (cl-user::cl-mpm-script-args).
rem ---------------------------------------------------------------------------
setlocal
call "%~dp0env.cmd" || exit /b 1

set "INIT=%CL_MPM_ROOT%\windows\init.lisp"

if "%~1"=="" (
    "%CL_MPM_SBCL%" --dynamic-space-size %CL_MPM_HEAP_MB% --no-userinit --load "%INIT%"
    exit /b %ERRORLEVEL%
)

set "SCRIPT=%~f1"
shift
set "ARGS="
:collect
if "%~1"=="" goto run
set ARGS=%ARGS% "%~1"
shift
goto collect

:run
"%CL_MPM_SBCL%" --dynamic-space-size %CL_MPM_HEAP_MB% --noinform --no-userinit --disable-debugger ^
    --load "%INIT%" --load "%SCRIPT%" --quit --end-toplevel-options %ARGS%
exit /b %ERRORLEVEL%
