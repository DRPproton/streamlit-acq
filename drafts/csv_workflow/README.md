# CSV saving and partial-results workflow — review draft

Nothing in this folder is connected to your current app. Your root `app.py` and
`helpers.py` were not changed. Review and install this yourself when ready.

## Read these files in this order

1. `csv_store.py`: preparing a CSV row and saving it without duplicate Study IDs.
2. `app_draft.py`: a complete, shorter review copy of the proposed Streamlit app.
3. `check_draft.py`: runnable examples that exercise saving and failed analysis steps.

The complete app copy avoids having to paste many small pieces at uncertain
indentation levels. Its numbered sections explain the integration points below.
It uses your existing `helpers.py`: baseline formula, MVC formula, marker matching,
channel matching, and filename identification are unchanged.

## Where the code will go later

After you review it:

- Put `csv_store.py` beside your existing root `app.py` and `helpers.py`.
- Compare `app_draft.py` with your existing `app.py`. It is a proposed replacement
  for `app.py`, not code to append at the bottom. Keep a backup of your current app
  before manually replacing it, or transfer the sections individually.
- Keep `helpers.py` as it is.
- Your launchers still run the root `app.py`; no launcher changes are needed.
- The default output becomes `results.csv` beside the installed root `app.py`.
  You can change that path on the final review screen. Its parent folder must exist.
  The path refers to the computer running Streamlit.

Do not simply append the new review screen after the old one. Old error stops and
channel lookup would prevent failed recordings from reaching it.

## Part A: Understand the CSV functions

### `build_result_row(...)`: prepare, but do not save

Inputs:

- `study_id`: the researcher-confirmed ID, treated as text.
- `results`: the current nested results dictionary, as used by your existing app.
- `issues`: messages accumulated during this recording's analysis.
- `manual_review`: the researcher's optional manual-review checkbox.
- `notes`: optional final-review notes.

Example:

```python
row = build_result_row(
    study_id="00123",
    results={
        "ZM": {
            "baseline": {"value": 0.02},
            "mvc": {"value": 0.15},
        },
        "CS": {"baseline": {"value": 0.03}},
    },
    issues=["CS MVC: Furrow2 marker missing"],
)
```

The CS MVC cell is blank, not zero. A zero could be a real measurement.
`needs_manual_review` is automatically `True`. The function also lists missing
measurements in `review_notes`, so an absent result cannot accidentally be saved
as a clean record. A `None`, NaN, or infinite measurement is treated as missing.

The timestamp remains blank in the preview: previewing is not saving.

### `save_result_csv(path, row)`: save only after the button is clicked

The function:

1. Validates the destination and Study ID.
2. Obtains a small `.lock` file so two copies of this saving function cannot race.
3. Reads an existing CSV, keeping IDs as text. `00123` stays `00123`.
4. Requires the expected column header and well-formed rows.
5. Returns `"duplicate"` without modifying anything when the ID already exists.
6. Sets `added_at` to the current UTC time, including the `+00:00` timezone.
7. Writes existing rows plus the new row to a temporary file, then replaces the
   destination after the write succeeds.
8. Removes the lock and any remaining temporary file.

It returns `"created"`, `"appended"`, or `"duplicate"`. Errors are raised to the
app, which shows a message and retains the analysis so you can retry saving.

The temporary-file approach logically appends a row, but rewrites the small CSV
in one replacement. This avoids leaving a half-written row after a write error.
It is suitable for this local results collection; it is not a database.

An existing CSV with the old five-column format is deliberately not migrated.
Choose a new filename or review and migrate the old file separately. An existing
empty file is also rejected because it has no expected header.

IDs are matched as text after removing surrounding whitespace. `00123` and `123`
are distinct. Reading with Python's CSV module preserves zeros; Excel may infer
numbers when opening CSV files, so import the Study ID column as text there.

The lock coordinates this app's saving function, not external CSV editors. A
forced process termination can leave a `.lock` file; remove it manually only
after confirming no save is running. A normal exception cleans it up.

### Output columns

```text
study_id,CS baseline,ZM baseline,CS MVC,ZM MVC,added_at,needs_manual_review,review_notes
```

`needs_manual_review` is written as `True`/`False`. `review_notes` is the extra
explanation column discussed in our proposed workflow. Successful values are
stored without rounding them to the six decimals used for screen display.

## Part B: Understand the Streamlit changes

### Section 1: reset and navigation helpers

Extend your current reset function to clear `issues`, `load_error`, review-widget
values, and the existing adjustment keys. This prevents review flags from leaking
from one uploaded recording into another. The chosen CSV path stays selected.

`add_issue(message)` records an issue once, so Streamlit reruns do not duplicate
the same explanation.

`next_muscle_or_review()` replaces the repeated Continue logic. It advances from
ZM to CS, then to final review.

`skip_measurement(muscle, step, reason)` removes only that measurement, records
why it was discarded, and advances:

```text
Skip ZM baseline -> ZM MVC
Skip ZM MVC      -> CS baseline
Skip CS baseline -> CS MVC
Skip CS MVC      -> final review
```

`show_signal(...)` catches a plotting exception separately. The researcher can
still skip or continue; the graph failure remains recorded for manual review.

### Section 2: replace the upload and file-information blocks

On a new filename/signature, discard old data and reset the workflow *before*
trying to load the new file. If loading fails, remember the error instead of
stopping before the Study ID field. The researcher can correct the ID and choose
“Review and save flagged record.” All four measurements will then be blank.

The Study ID field is outside the condition requiring successfully loaded data.
This is what makes saving an unreadable file possible. An empty ID disables saving.

Removing the upload still resets analysis. To retry reading a failed file, remove
it and upload it again. Ordinary reruns do not repeatedly attempt the same failed read.

### Section 3: move final review before channel lookup

Your existing review screen is at the bottom, after code that requires a channel.
The draft checks for `stage == "review"` first, displays the save controls, and
calls `st.stop()` after rendering them. This permits review even when an entire
recording or a channel could not be loaded.

The checkbox can add a flag; it cannot remove flags caused by missing values or
recorded errors. Notes also mark the row for review. Issues remain recorded even
if a later retry succeeds, so that an error during the run is still visible.

Saving happens only inside the Save button branch. A widget rerun alone never
writes a row. Clicking Save twice is safe because the second call checks the ID
in the CSV again. Already-saved partial rows are not updated by this workflow;
correcting them later needs a separate, explicit review/update process.

### Section 4: missing-channel recovery

Replace the current missing-channel error-only stop with a message and a
“Skip muscle and flag for manual review” button. Both measurements for that
muscle remain absent, and the other muscle is still processed.

### Section 5: baseline recovery

Keep your existing baseline calculation and finite-value check. Put the Skip
button before calculation, so it still appears when calculation fails.

- Successful result: display it and offer Continue.
- Calculation failure: show and record the error; the Skip button stays available.
- Visually unsuitable result: Skip removes the calculated baseline and continues
  to that same muscle's MVC step.

This does **not** implement the previously discussed incomplete-window change.
As requested, a finite value from an incomplete baseline window is still possible
and must be caught by researcher review.

### Section 6: MVC recovery and shared calculation

There is one calculation block for both default and adjusted windows. The default
is still ±2 seconds, and Change window still allows manual adjustment.

The Skip button appears before marker lookup. Missing marker, invalid value, or
calculation exception therefore does not trap the researcher on that step.
On calculation failure, adjust the window and retry, or skip the measurement.

Only calculation calls are wrapped in `try/except`; Streamlit navigation remains
outside those blocks. The math and window boundaries in `helpers.py` stay unchanged.

### Section 7: accept or discard the calculated MVC

The researcher can accept the result with Continue or discard it with a review
flag. Either route advances to the next muscle or final review.

## Checks you can run without installing the draft

From the project root:

```bash
.venv/bin/python drafts/csv_workflow/check_draft.py
```

The checks import the draft storage module and run the draft app through Streamlit's
headless test framework. They use synthetic recordings and temporary CSV files,
which are deleted afterward. They do not launch or alter your normal app.

Verified scenarios:

- New CSV, appended study, repeated Study ID, and leading-zero ID preservation.
- Timestamp at save time and automatic partial-result flagging.
- Existing CSV with incompatible columns and simulated write failure.
- Both muscles through default and adjusted windows, including Save and duplicate Save.
- Failed baselines while both MVC measurements still succeed.
- Missing muscle channel and missing MVC marker while another measurement succeeds.
- Unreadable ACQ file reaching flagged review and blank Study ID blocking saving.

Real ACQ-file validation and checking the workflow against your research protocol
remain part of your review. These checks demonstrate behavior, not scientific validity.
