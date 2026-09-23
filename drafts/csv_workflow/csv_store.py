"""Draft CSV storage. Importing this module never writes a file."""

import csv
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


MEASUREMENTS = {
    "CS baseline": ("CS", "baseline"),
    "ZM baseline": ("ZM", "baseline"),
    "CS MVC": ("CS", "mvc"),
    "ZM MVC": ("ZM", "mvc"),
}
COLUMNS = [
    "study_id", *MEASUREMENTS, "added_at", "needs_manual_review", "review_notes"
]


def build_result_row(study_id, results, issues, manual_review=False, notes=""):
    """Build a reviewable row; blank measurements automatically require review."""
    study_id = str(study_id or "").strip()
    if not study_id:
        raise ValueError("Enter a Study ID before saving.")

    row = {"study_id": study_id}
    reasons = list(issues)
    for column, (muscle, step) in MEASUREMENTS.items():
        measurement = results.get(muscle, {}).get(step) or {}
        value = measurement.get("value")
        if value is None or not math.isfinite(float(value)):
            row[column] = ""
            reasons.append(f"{column}: no valid measurement")
        else:
            row[column] = float(value)

    if notes.strip():
        reasons.append(notes.strip())
    if manual_review:
        reasons.append("Researcher requested manual review")

    row["added_at"] = ""  # Set only when a new row is actually saved.
    row["needs_manual_review"] = bool(reasons)
    row["review_notes"] = "; ".join(dict.fromkeys(reasons))
    return row


def save_result_csv(path, row):
    """Return 'created', 'appended', or 'duplicate'; never replace an existing ID.

    A lock prevents two copies of this app from checking/appending simultaneously.
    A temporary file + atomic replacement preserves the old CSV on write failure.
    """
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() != ".csv":
        raise ValueError("The output filename must end in .csv.")
    if set(row) != set(COLUMNS):
        raise ValueError("The result row does not match the expected CSV columns.")
    study_id = str(row["study_id"] or "").strip()
    if not study_id:
        raise ValueError("Enter a Study ID before saving.")

    lock_path = path.with_name(path.name + ".lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("This CSV is being saved elsewhere. Try again shortly.") from None

    temp_path = None
    try:
        os.close(lock_fd)
        existing_rows = []
        exists = path.exists()
        if exists:
            with path.open("r", encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source, strict=True)
                if reader.fieldnames != COLUMNS:
                    raise ValueError("Existing CSV has different columns. Choose a new file.")
                existing_rows = list(reader)
            if any(set(r) != set(COLUMNS) or any(v is None for v in r.values())
                   or not r["study_id"].strip() for r in existing_rows):
                raise ValueError("Existing CSV contains an incomplete or malformed row.")
            if any(r["study_id"].strip() == study_id for r in existing_rows):
                return "duplicate"

        saved_row = dict(row)
        saved_row["study_id"] = study_id
        saved_row["added_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as target:
            temp_path = Path(target.name)
            writer = csv.DictWriter(target, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerow(saved_row)
            target.flush()
            os.fsync(target.fileno())

        os.replace(temp_path, path)
        return "appended" if exists else "created"
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        lock_path.unlink(missing_ok=True)
