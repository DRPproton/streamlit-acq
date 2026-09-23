@echo off
setlocal

cd /d "%~dp0"

echo Starting Baseline ACQ file extractor...
echo Project: %CD%
echo.

where uv >nul 2>nul
if %ERRORLEVEL%==0 (
    uv run streamlit run app.py
    goto end
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -m streamlit run app.py
    goto end
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    python -m streamlit run app.py
    goto end
)

echo Python was not found.
echo Install Python or uv, then run this launcher again.
echo.

:end
pause
