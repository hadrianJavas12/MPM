@echo off
rem ---------------------------------------------------------------------------
rem  make-video.cmd - encode numbered PNG frames (frame_00001.png, ...) to MP4.
rem
rem  Usage: windows\make-video.cmd [frames-dir] [fps] [output.mp4]
rem    frames-dir  default: output\studio\frames
rem    fps         default: 15
rem    output.mp4  default: <frames-dir>\..\video.mp4
rem ---------------------------------------------------------------------------
setlocal
call "%~dp0env.cmd" || exit /b 1

set "FRAMES=%~f1"
if "%~1"=="" set "FRAMES=%CL_MPM_ROOT%\output\studio\frames"
set "FPS=%~2"
if "%FPS%"=="" set "FPS=15"
set "OUT=%~f3"
if "%~3"=="" for %%I in ("%FRAMES%\..") do set "OUT=%%~fI\video.mp4"

where ffmpeg >nul 2>nul || (
    echo [make-video] ffmpeg not found. Install it with:  winget install Gyan.FFmpeg.Essentials
    echo              or set CL_MPM_FFMPEG to the folder containing ffmpeg.exe.
    exit /b 1
)

if not exist "%FRAMES%\frame_00001.png" (
    echo [make-video] No frames found in "%FRAMES%". Run a simulation first.
    exit /b 1
)

echo [make-video] %FRAMES% -^> %OUT% at %FPS% fps
rem pad filter: libx264/yuv420p need even width and height.
ffmpeg -hide_banner -loglevel error -y -framerate %FPS% -i "%FRAMES%\frame_%%05d.png" ^
    -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -c:v libx264 -pix_fmt yuv420p "%OUT%"
if errorlevel 1 (
    echo [make-video] ffmpeg failed.
    exit /b 1
)
echo [make-video] OK: %OUT%
