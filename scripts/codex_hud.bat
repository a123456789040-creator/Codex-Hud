@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_CMD=python"
where %PYTHON_CMD% >nul 2>nul
if errorlevel 1 (
  echo Python not found in PATH.
  exit /b 1
)

if "%~1"=="" (
  %PYTHON_CMD% "%SCRIPT_DIR%codex_hud.py" --layout single --watch
  exit /b %errorlevel%
)

%PYTHON_CMD% "%SCRIPT_DIR%codex_hud.py" %*
exit /b %errorlevel%
