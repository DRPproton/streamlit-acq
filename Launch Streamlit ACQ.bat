@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Edit these two paths. By default, use the folder containing this launcher.
set "APP_FILE=%~dp0main.py"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if not exist "%APP_FILE%" goto missing_app
if not exist "%PYTHON_EXE%" goto missing_python

rem Use the app folder even when started from a desktop shortcut.
for %%I in ("%APP_FILE%") do set "APP_DIR=%%~dpI"
pushd "%APP_DIR%"
if errorlevel 1 goto missing_directory

"%PYTHON_EXE%" -m streamlit --version >nul 2>nul
if errorlevel 1 goto missing_streamlit

echo Starting Streamlit ACQ...
echo App: "%APP_FILE%"
echo Python: "%PYTHON_EXE%"
echo Keep this window open while using the app. Press Ctrl+C to stop.
echo.

"%PYTHON_EXE%" -m streamlit run "%APP_FILE%" --server.address=127.0.0.1 --server.headless=false
set "APP_EXIT_CODE=%ERRORLEVEL%"
popd
if "%APP_EXIT_CODE%"=="0" exit /b 0
echo.
echo Streamlit stopped with exit code %APP_EXIT_CODE%. See the output above.
pause
exit /b %APP_EXIT_CODE%

:missing_app
echo App file not found: "%APP_FILE%"
echo Edit APP_FILE in this batch file.
goto failed

:missing_python
echo Python executable not found: "%PYTHON_EXE%"
echo Edit PYTHON_EXE to point to your Windows environment's python.exe.
goto failed

:missing_directory
echo Could not open the app folder: "%APP_DIR%"
goto failed

:missing_streamlit
popd
echo Could not run Streamlit with: "%PYTHON_EXE%"
echo Check that this environment works and has the project dependencies installed.
goto failed

:failed
pause
exit /b 1
