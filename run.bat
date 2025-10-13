@echo off
REM Usage: run.bat [port]
SETLOCAL

IF "%~1"=="" (
  set PORT=8000
) ELSE (
  set PORT=%~1
)

REM Activate virtualenv if present
IF EXIST env\Scripts\activate.bat (
  call env\Scripts\activate.bat
) ELSE (
  echo Warning: virtual environment not found in env\ - continuing without activation
)

SET PYTHONPATH=src

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port %PORT%

ENDLOCAL
