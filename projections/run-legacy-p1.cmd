@echo off
setlocal
set "RESEARCH_ROOT=%~dp0.."
for %%I in ("%RESEARCH_ROOT%") do set "RESEARCH_ROOT=%%~fI"
if "%MYIS_LEGACY_DAPFAM_ROOT%"=="" (
  echo ERROR: MYIS_LEGACY_DAPFAM_ROOT must point to the Owner-local legacy DAPFAM data directory.
  exit /b 2
)
if "%MYIS_P1_STORE%"=="" set "MYIS_P1_STORE=%LOCALAPPDATA%\myIS\p1-cpu-store"
if "%MYIS_P1_EVIDENCE_ROOT%"=="" set "MYIS_P1_EVIDENCE_ROOT=%LOCALAPPDATA%\myIS\p1-evidence"
for /f %%I in ('powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')"') do set "RUNSTAMP=%%I"
set "REQUEST=%TEMP%\myis-legacy-dapfam-p1-request-%RUNSTAMP%.json"
set "INVENTORY=%TEMP%\myis-legacy-dapfam-inventory-%RUNSTAMP%.json"
set "RECEIPT=%MYIS_P1_EVIDENCE_ROOT%\legacy-p1-receipt-%RUNSTAMP%.json"
where uv >nul 2>&1 || (echo ERROR: uv is required.& exit /b 2)

uv run --no-sync myis-legacy-dapfam --repository-root "%RESEARCH_ROOT%" --legacy-root "%MYIS_LEGACY_DAPFAM_ROOT%" --inventory-output "%INVENTORY%" --make-request "%REQUEST%"
if errorlevel 1 (
  echo ERROR: legacy metadata certification failed.
  pause
  exit /b 1
)

uv run --no-sync myis-owner-local --repository-root "%RESEARCH_ROOT%" --request "%REQUEST%" --protected-root "%MYIS_LEGACY_DAPFAM_ROOT%" --legacy-root "%MYIS_LEGACY_DAPFAM_ROOT%" --store-root "%MYIS_P1_STORE%" --receipt "%RECEIPT%"
if errorlevel 1 (
  echo ERROR: P1 owner-local execution failed. No metric substitute was created.
  pause
  exit /b 1
)
echo P1 receipt written to "%RECEIPT%". No protected payload was emitted.
pause
endlocal
