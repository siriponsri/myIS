@echo off
setlocal

if not defined MYIS_VASTAI_PYTHON exit /b 64
if /I not "%~1"=="show" exit /b 65
if /I not "%~2"=="instance" exit /b 66
if "%~3"=="" exit /b 67
if /I not "%~4"=="--raw" exit /b 68
if not "%~5"=="" exit /b 69

"%MYIS_VASTAI_PYTHON%" -c "from vastai.cli.main import main; main()" --raw show instance "%~3"
exit /b %ERRORLEVEL%
