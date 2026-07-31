@echo off
setlocal
set "RESEARCH_ROOT=%~dp0.."
for %%I in ("%RESEARCH_ROOT%") do set "RESEARCH_ROOT=%%~fI"
if "%MYIS_DASHBOARD_PORT%"=="" set "MYIS_DASHBOARD_PORT=8765"
where uv >nul 2>&1 || (echo ERROR: uv is required.& exit /b 2)

uv run --no-sync python -m myis_research.dashboard.launcher --repository-root "%RESEARCH_ROOT%" --port "%MYIS_DASHBOARD_PORT%"
if errorlevel 1 (
  echo ERROR: Dashboard launch failed.
  pause
  exit /b 1
)
endlocal
