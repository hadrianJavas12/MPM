@echo off
"C:\Program Files\Steel Bank Common Lisp\sbcl.exe" --noinform --no-userinit --disable-debugger --script "%~dp0fixture.lisp" "%~2" "%~3"
exit /b %ERRORLEVEL%
