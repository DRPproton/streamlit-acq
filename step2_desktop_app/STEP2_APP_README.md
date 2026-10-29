# Step 2 desktop app

Keep step2_app.py and step2_transfer.py in the same folder.

Install the one external dependency in your Python environment:

    python -m pip install openpyxl

Start the app:

    python step2_app.py

1. Browse to the TRM workbook (ktrials and ftrials sheets).
2. Browse to the formatted PsychoPy workbook.
3. Choose a NEW output .xlsx filename.
4. Keep PsychoPy_R and suffix length 7 to match the notebook.
5. Optionally include ctrials when that sheet and its destination columns exist.
6. Click Validate only, then Run transfer.

The app processes one file pair at a time. Select another pair to repeat.
The window stays responsive while processing, and shows validation errors and
matched-row counts. Original files and existing output files are not overwritten.
The default output is next to the selected PsychoPy file, ending in _step2.xlsx.

Matching uses img_file, Race, Gender and is case-sensitive. Suffix length applies
only to the source img_file, just like the notebook. Use 0 for full-name matching.
All keyed rows are processed. Fully blank key rows are skipped. Partial keys,
duplicate keys, missing columns, and unmatched destination keys stop the transfer.
Blank source responses leave destination values unchanged; other responses replace
the target cells. Extra source rows are reported but not copied.

Standard cell styles, formulas, and other worksheets are retained by openpyxl.
It does not recalculate formulas or guarantee preservation of advanced Excel objects.
Use ordinary .xlsx workbooks with value-based source data and matching keys.

Tkinter is normally included with Python on Windows. If it is missing, modify
your Python installation to include Tcl/Tk. Run in your existing project Python
environment if openpyxl is already installed.
