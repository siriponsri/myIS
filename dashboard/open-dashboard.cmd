@echo off
setlocal
set "RESEARCH_ROOT=%~dp0.."
for %%I in ("%RESEARCH_ROOT%") do set "RESEARCH_ROOT=%%~fI"
if "%MYIS_DASHBOARD_PORT%"=="" set "MYIS_DASHBOARD_PORT=8765"
where uv >nul 2>&1 || (echo ERROR: uv is required.& exit /b 2)

start "myIS Dashboard" /min powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Set-Location -LiteralPath '%RESEARCH_ROOT%'; uv run --no-sync myis-dashboard --repository-root '%RESEARCH_ROOT%' --port %MYIS_DASHBOARD_PORT%"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:%MYIS_DASHBOARD_PORT%"
endlocal
