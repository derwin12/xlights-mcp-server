@echo off
rem YouTube link -> singing faces + house sequence -> .xsqz in F:\ShowFolderAI (see .claude\skills\song-to-package)
title Song to Package
cd /d "%~dp0.."

set "URL="
set /p "URL=YouTube link: "
if "%URL%"=="" goto :eof

set "ARGS="
set "ANS="
set /p "ANS=Play the music video on Matrix 2? [Y/n] "
if /i not "%ANS%"=="n" set "ARGS=%ARGS% --video-model "Matrix 2" --video-crop-x 12"

set "ANS="
set /p "ANS=Include audio/video in the .xsqz (review build)? [Y/n] "
if /i not "%ANS%"=="n" set "ARGS=%ARGS% --with-media"

rem xLights' automation port changes between runs (49913/49914) - use the one it is listening on
set "PORT="
for /f %%p in ('powershell -NoProfile -Command "$p = Get-Process xLights -ErrorAction SilentlyContinue | Select-Object -First 1; if ($p) { (Get-NetTCPConnection -OwningProcess $p.Id -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -ge 49900 | Select-Object -First 1).LocalPort }"') do set "PORT=%%p"
if defined PORT (
    echo xLights automation on port %PORT%
    set "ARGS=%ARGS% --port %PORT%"
) else (
    echo xLights is not running - the house preview video will be skipped
)

echo.
python -u scripts\song_to_package.py "%URL%" %ARGS%
echo.
pause
