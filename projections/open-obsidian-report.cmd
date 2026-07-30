@echo off
setlocal
set "RESEARCH_ROOT=%~dp0.."
for %%I in ("%RESEARCH_ROOT%") do set "RESEARCH_ROOT=%%~fI"
where uv >nul 2>&1 || (echo ERROR: uv is required.& exit /b 2)

uv run --no-sync myis-report sync --repository-root "%RESEARCH_ROOT%"
if errorlevel 1 (
  echo ERROR: report generation failed.
  pause
  exit /b 1
)
start "" "obsidian://open?vault=02_Brain"
endlocal
