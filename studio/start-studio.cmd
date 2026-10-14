@echo off
rem ---------------------------------------------------------------------------
rem  start-studio.cmd - start the CL-MPM Studio web UI on http://127.0.0.1:3000
rem  Set STUDIO_PORT to use another port. Requires Node.js >= 18.
rem ---------------------------------------------------------------------------
setlocal
call "%~dp0..\windows\env.cmd" || exit /b 1

where node >nul 2>nul || (
    echo [studio] Node.js not found. Install it with:  winget install OpenJS.NodeJS.LTS
    exit /b 1
)

if not defined STUDIO_PORT set "STUDIO_PORT=3000"
start "" "http://127.0.0.1:%STUDIO_PORT%"
node "%~dp0server.js"
