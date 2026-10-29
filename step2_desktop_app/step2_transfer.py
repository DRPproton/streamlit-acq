"""Step 2: join TRM results into a formatted PsychoPy .xlsx workbook.

Install: python -m pip install openpyxl
Example:
python step2_transfer.py --trm trials.xlsx --psychopy PsychoPy_data.xlsx

Headers must be in row 1. Keys: img_file, Race, Gender.
Like the notebook, source img_file uses its final 7 characters; use
--suffix-length 0 for exact full names. Matching is case-sensitive.
All keyed rows are processed, without the notebook's 24/25-row limit.
Blank source results preserve existing destination values. Nonblank results
replace them. Fully blank key rows are ignored; partial or duplicate keys fail.
Missing destination matches fail before saving; unused source rows are counted.
Only ordinary .xlsx workbooks are supported. openpyxl preserves cell formatting
and formulas, but does not recalculate formulas or preserve every Excel feature.
"""
import argparse
from copy import copy
from pathlib import Path
from openpyxl import load_workbook

KEYS = ("img_file", "Race", "Gender")
MAPPINGS = {
    "ktrials": {"order": "kOrder", "k_resp.keys_raw": "kResp"},
    "ftrials": {"order": "fOrder", "f_slider.response_mean": "fSlider"},
    "ctrials": {"order": "cOrder", "c_slider.response_mean": "cSlider"},
}
ALIASES = {"k_resp.ke.": "k_resp.keys_raw", "f_slider.re.": "f_slider.response_mean"}

def blank(value):
    return value is None or value == ""

def headers(ws, aliases=False):
    result = {}
    for cell in ws[1]:
        name = cell.value
        if blank(name):
            continue
        if aliases:
            name = ALIASES.get(name, name)
        if name in result:
            raise ValueError(f"{ws.title}: duplicate header {name!r}")
        result[name] = cell.column
    return result

def require(ws, columns, names):
    missing = set(names) - columns.keys()
    if missing:
        raise ValueError(f"{ws.title}: missing columns {sorted(missing)}")

def keyed_rows(ws, columns, suffix_length=0):
    result = {}
    for row in range(2, ws.max_row + 1):
        cells = [ws.cell(row, columns[key]) for key in KEYS]
        values = [cell.value for cell in cells]
        if all(blank(value) for value in values):
            continue
        if any(blank(value) for value in values):
            raise ValueError(f"{ws.title} row {row}: incomplete key {values!r}")
        if any(cell.data_type in ("f", "e") for cell in cells):
            raise ValueError(f"{ws.title} row {row}: key contains formula/error")
        if not isinstance(values[0], str):
            raise ValueError(f"{ws.title} row {row}: img_file must be text")
        if suffix_length:
            values[0] = values[0][-suffix_length:]
        key = tuple(values)
        if key in result:
            raise ValueError(f"{ws.title}: duplicate key {key!r}, rows {result[key]} and {row}")
        result[key] = row
    if not result:
        raise ValueError(f"{ws.title}: no keyed rows")
    return result

def transfer(trm, psychopy, output=None, sheet="PsychoPy_R",
             include_ctrials=False, suffix_length=7, dry_run=False):
    """Validate and save a separate workbook; return per-sheet counts."""
    trm, psychopy = Path(trm).resolve(), Path(psychopy).resolve()
    output = Path(output).resolve() if output else psychopy.with_name(psychopy.stem + "_step2.xlsx")
    if suffix_length < 0:
        raise ValueError("suffix_length must be >= 0")
    for path in (trm, psychopy, output):
        if path.suffix.lower() != ".xlsx":
            raise ValueError(f"Only .xlsx files are supported: {path}")
    if output in (trm, psychopy):
        raise ValueError("Output must differ from both inputs")
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    if not output.parent.is_dir():
        raise ValueError(f"Output directory does not exist: {output.parent}")
    source = load_workbook(trm, data_only=False)
    try:
        destination = load_workbook(psychopy)
        try:
            if sheet not in destination.sheetnames:
                raise ValueError(f"Missing destination sheet: {sheet}")
            ws = destination[sheet]
            dc = headers(ws)
            require(ws, dc, KEYS)
            dest_rows = keyed_rows(ws, dc)
            trials = ["ktrials", "ftrials"] + (["ctrials"] if include_ctrials else [])
            changes, summary = [], {}
            for trial in trials:
                if trial not in source.sheetnames:
                    raise ValueError(f"Missing source sheet: {trial}")
                src = source[trial]
                mapping = MAPPINGS[trial]
                sc = headers(src, aliases=True)
                require(src, sc, (*KEYS, *mapping))
                require(ws, dc, mapping.values())
                src_rows = keyed_rows(src, sc, suffix_length)
                unmatched = dest_rows.keys() - src_rows.keys()
                if unmatched:
                    raise ValueError(f"{trial}: {len(unmatched)} unmatched destination keys; examples: {list(unmatched)[:5]}")
                written = skipped = 0
                for key, dest_row in dest_rows.items():
                    for src_name, dest_name in mapping.items():
                        cell = src.cell(src_rows[key], sc[src_name])
                        if cell.data_type in ("f", "e"):
                            raise ValueError(f"{trial}!{cell.coordinate}: expected value, found formula/error")
                        if blank(cell.value):
                            skipped += 1
                            continue
                        changes.append((dest_row, dc[dest_name], cell.value, dest_name))
                        written += 1
                summary[trial] = {
                    "matched_rows": len(dest_rows), "cells_written": written,
                    "blank_values_skipped": skipped,
                    "unused_source_rows": len(src_rows.keys() - dest_rows.keys()),
                }
            if not dry_run:
                for row, column, value, name in changes:
                    cell = ws.cell(row, column)
                    cell.value = value
                    if isinstance(value, str):
                        cell.data_type = "s"
                    if name == "kResp":
                        alignment = copy(cell.alignment)
                        alignment.horizontal = "right"
                        cell.alignment = alignment
                with output.open("xb") as handle:
                    destination.save(handle)
            return summary
        finally:
            destination.close()
    finally:
        source.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trm", required=True, type=Path)
    parser.add_argument("--psychopy", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Default: <psychopy>_step2.xlsx; must not exist")
    parser.add_argument("--sheet", default="PsychoPy_R")
    parser.add_argument("--include-ctrials", action="store_true")
    parser.add_argument("--suffix-length", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        summary = transfer(**vars(args))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    for trial, counts in summary.items():
        print(f"{trial}: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    output = args.output or args.psychopy.with_name(args.psychopy.stem + "_step2.xlsx")
    print("Validation passed; no file written." if args.dry_run else f"Saved: {output.resolve()}")

if __name__ == "__main__":
    main()
