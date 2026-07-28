@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop_owner_console.ps1"
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo The Owner Console could not stop cleanly. Review the error above.
pause
exit /b 1
