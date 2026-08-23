@echo off
rem Malrynth Windows CLI Batch Launcher
rem Requires Python 3.10 or newer; malrynth.py enforces the exact version gate.
setlocal
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%malrynth.py" %*
if %ERRORLEVEL% NEQ 0 (
    exit /b %ERRORLEVEL%
)
endlocal
