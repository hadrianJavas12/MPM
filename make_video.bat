@echo off
setlocal

set "FPS=15"
if not "%~1"=="" set "FPS=%~1"

set "OUTPUT_FILE=D:\MPM\simulation_video.mp4"
if not "%~2"=="" set "OUTPUT_FILE=%~2"

:: Add WinGet ffmpeg and WindowsApps to PATH
set "PATH=C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin;C:\Users\ASUS\AppData\Local\Microsoft\WindowsApps;%PATH%"

echo ========================================================
echo Converting PNG frames to MP4 video (FPS: %FPS%)...
echo ========================================================

:: Check if ffmpeg is available
where ffmpeg >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] FFmpeg tidak ditemukan di PATH.
    echo Anda dapat menginstall FFmpeg dengan menjalankan:
    echo     winget install Gyan.FFmpeg.Essentials
    echo Setelah selesai diinstall, jalankan kembali script ini.
    exit /b 1
)

if not exist "D:\MPM\outframes\frame_00001.png" (
    echo [ERROR] Tidak ada file frame di D:\MPM\outframes\
    echo Jalankan simulasi terlebih dahulu: d:\MPM\run_windows.bat run_example_chalk.lisp
    exit /b 1
)

echo Menghasilkan video: %OUTPUT_FILE%...
ffmpeg -y -framerate %FPS% -i "D:\MPM\outframes\frame_%%05d.png" -c:v libx264 -pix_fmt yuv420p "%OUTPUT_FILE%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo SUCCESS: Video berhasil dibuat!
    echo Lokasi: %OUTPUT_FILE%
    echo ========================================================
) else (
    echo [ERROR] Gagal mengonversi video.
)
