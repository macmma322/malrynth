@echo off
rem Malrynth Windows CLI Batch Launcher
setlocal
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%malrynth.py" %*
if %ERRORLEVEL% NEQ 0 (
    exit /b %ERRORLEVEL%
)
endlocal
