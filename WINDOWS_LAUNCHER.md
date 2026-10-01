# Windows desktop launcher

Edit the two settings near the top of `Launch Streamlit ACQ.bat`:

```bat
set "APP_FILE=C:\Users\YourName\Projects\streamlit-acq\main.py"
set "PYTHON_EXE=C:\Users\YourName\Environments\acq\Scripts\python.exe"
```

Use full paths and keep the quotes. `PYTHON_EXE` points to the **Python executable inside your Windows virtual environment**, not the environment folder or `activate.bat`. That environment must already contain the project's dependencies. A virtual environment copied from macOS will not work on Windows.

The default settings work when the launcher is in the project folder and the Windows virtual environment is in that folder's `.venv` directory. `%~dp0` means the folder containing this batch file.

To create the desktop shortcut:

1. Right-click `Launch Streamlit ACQ.bat` in File Explorer.
2. Choose **Send to → Desktop (create shortcut)**. On Windows 11, select **Show more options** first if needed.
3. Double-click the desktop shortcut to launch the app.

Keep the original batch file in place; the desktop item is a shortcut to it. The launcher uses the selected environment, switches to the app folder, and asks Streamlit to open the browser. Keep the console open while using the app. Press **Ctrl+C** there to stop it.

The launcher does not install dependencies. If startup fails, the console stays open so you can read the error.

Official reference: [Streamlit CLI](https://docs.streamlit.io/develop/api-reference/cli/run).
