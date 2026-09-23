"""Review copy: install as root app.py only after reviewing the guide."""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from csv_store import build_result_row, save_result_csv
from helpers import (
    calculate_baseline, extract_study_id, find_muscle_channel,
    get_max_from_data, load_acq_file, plot_channel, time_by_marker,
)

MUSCLES = ["ZM", "CS"]
MAX_MARKERS = {"ZM": "SMILE2", "CS": "Furrow2"}
DEFAULT_CSV = str(Path(__file__).resolve().with_name("results.csv"))


# 1. Session state and small workflow helpers.
def reset_analysis_state():
    st.session_state.current_muscle = 0
    st.session_state.stage = "overview"
    st.session_state.results = {}
    st.session_state.issues = []
    st.session_state.load_error = None
    for key in ["manual_review", "review_notes"]:
        st.session_state.pop(key, None)
    for muscle in MUSCLES:
        for prefix in ["adjust_max_window", "shift"]:
            st.session_state.pop(f"{prefix}_{muscle}", None)


def add_issue(message):
    if message not in st.session_state.issues:
        st.session_state.issues.append(message)


def next_muscle_or_review():
    if st.session_state.current_muscle < len(MUSCLES) - 1:
        st.session_state.current_muscle += 1
        st.session_state.stage = "baseline"
    else:
        st.session_state.stage = "review"
    st.rerun()


def skip_measurement(muscle, step, reason):
    # Remove an untrusted result, even if it was already calculated.
    st.session_state.results[muscle].pop(step, None)
    add_issue(f"{muscle} {step}: {reason}")
    if step == "baseline":
        st.session_state.stage = "max_window"
        st.rerun()
    next_muscle_or_review()


def show_signal(channel, **kwargs):
    # Catch plotting failures separately so the skip controls remain available.
    try:
        figure = plot_channel(channel, **kwargs)
    except Exception as exc:
        message = f"{channel.name} graph failed: {type(exc).__name__}: {exc}"
        add_issue(message)
        st.error(message)
    else:
        st.plotly_chart(figure, width="stretch")


for key, value in {
    "acq_data": None, "file_signature": None, "current_muscle": 0,
    "stage": "upload", "results": {}, "study_id": "", "issues": [],
    "load_error": None,
}.items():
    st.session_state.setdefault(key, value)


# 2. Upload. A failed read still leaves the Study ID and review route available.
st.title("Baseline acq extractor")
uploaded_file = st.file_uploader("Choose a *.acq file", type=["acq"])
if uploaded_file is None:
    st.session_state.acq_data = None
    st.session_state.file_signature = None
    reset_analysis_state()
    st.session_state.stage = "upload"
    st.info("Upload an ACQ file to begin.")
    st.stop()

signature = (uploaded_file.name, uploaded_file.size, uploaded_file.type)
if signature != st.session_state.file_signature:
    reset_analysis_state()
    st.session_state.acq_data = None
    st.session_state.file_signature = signature
    st.session_state.study_id_input = extract_study_id(uploaded_file.name) or ""
    try:
        loaded = load_acq_file(uploaded_file)
        if loaded is None:
            raise ValueError("The ACQ reader returned no recording.")
    except Exception as exc:
        message = f"ACQ read failed: {type(exc).__name__}: {exc}"
        st.session_state.load_error = message
        add_issue(message)
    else:
        st.session_state.acq_data = loaded

st.write(f"File name: {uploaded_file.name}")
st.session_state.study_id = st.text_input("Study ID", key="study_id_input").strip()
acq_data = st.session_state.acq_data
if acq_data is not None:
    st.write(f"Number of channels: {len(acq_data.channels)}")
    st.write([channel.name for channel in acq_data.channels])

if st.session_state.stage == "overview":
    if st.session_state.load_error:
        st.error(st.session_state.load_error)
        if st.button("Review and save flagged record"):
            st.session_state.stage = "review"
            st.rerun()
    elif st.button("Start calculation"):
        st.session_state.stage = "baseline"
        st.rerun()
    st.stop()


# 3. Final review must run BEFORE channel selection: unreadable files can reach it.
if st.session_state.stage == "review":
    st.subheader("Final results")
    manual_review = st.checkbox("Flag for manual review", key="manual_review")
    notes = st.text_area("Review notes (optional)", key="review_notes")
    if st.session_state.issues:
        st.warning("Issues recorded: " + "; ".join(st.session_state.issues))

    row = None
    try:
        row = build_result_row(
            st.session_state.study_id, st.session_state.results,
            st.session_state.issues, manual_review, notes,
        )
    except ValueError as exc:
        st.error(str(exc))
    if row is not None:
        st.dataframe(pd.DataFrame([row]), hide_index=True, width="stretch")
        st.caption("added_at is filled with the UTC time when the row is saved.")
        if row["needs_manual_review"]:
            st.warning("This record will be saved with needs_manual_review=True.")

    output_path = st.text_input("Output CSV path", value=DEFAULT_CSV, key="output_csv")
    if st.button("Save results", disabled=row is None):
        try:
            status = save_result_csv(output_path, row)
        except Exception as exc:
            st.error(f"Save failed: {exc}. Your analysis remains available; correct the problem and retry.")
        else:
            if status == "duplicate":
                st.warning("This Study ID is already saved. The existing row was not changed.")
            else:
                st.success(f"Results saved ({status}): {output_path}")
    st.stop()


# 4. Missing channel: skip that muscle, preserving all other results.
muscle = MUSCLES[st.session_state.current_muscle]
st.session_state.results.setdefault(muscle, {})
st.subheader(f"Muscle: {muscle}")
try:
    selected_channel = find_muscle_channel(acq_data, muscle)
    if selected_channel is None:
        raise ValueError(f"Could not find RMS channel for {muscle}.")
except Exception as exc:
    reason = f"{muscle} channel unavailable: {type(exc).__name__}: {exc}"
    add_issue(reason)
    st.error(reason)
    if st.button("Skip muscle and flag for manual review"):
        next_muscle_or_review()
    st.stop()


# 5. Baseline: the formula in helpers.py is unchanged.
if st.session_state.stage == "baseline":
    show_signal(selected_channel)
    if st.button("Skip baseline and flag for manual review", key=f"skip_baseline_{muscle}"):
        skip_measurement(muscle, "baseline", "Skipped during researcher review")

    if "baseline" not in st.session_state.results[muscle]:
        try:
            baseline = calculate_baseline(selected_channel, acq_data)
            if baseline is None or not np.isfinite(baseline["value"]):
                raise ValueError("No finite baseline value was calculated.")
        except Exception as exc:
            reason = f"{muscle} baseline failed: {type(exc).__name__}: {exc}"
            add_issue(reason)
            st.error(reason)
            st.stop()  # Skip button above remains usable on the next rerun.
        st.session_state.results[muscle]["baseline"] = baseline

    baseline = st.session_state.results[muscle]["baseline"]
    st.write(f"Baseline: {baseline['value']:.6f}")
    st.caption(f"Interval: {baseline['start']:.2f}–{baseline['end']:.2f} seconds")
    if st.button("Continue to max", key=f"continue_baseline_{muscle}"):
        st.session_state.stage = "max_window"
        st.rerun()
    st.stop()


# 6. MVC window: one calculation block handles default and adjusted windows.
if st.session_state.stage == "max_window":
    if st.button("Skip MVC and flag for manual review", key=f"skip_mvc_{muscle}"):
        skip_measurement(muscle, "mvc", "Skipped during researcher review")
    marker_name = MAX_MARKERS[muscle]
    try:
        marker_time = time_by_marker(acq_data, marker_name)
        if marker_time is None or not np.isfinite(marker_time):
            raise ValueError(f"No valid {marker_name} marker was found.")
    except Exception as exc:
        reason = f"{muscle} MVC marker failed: {type(exc).__name__}: {exc}"
        add_issue(reason)
        st.error(reason)
        st.stop()

    adjust_key = f"adjust_max_window_{muscle}"
    shift_key = f"shift_{muscle}"
    adjusting = st.session_state.get(adjust_key, False)
    if adjusting:
        shift = st.number_input(
            "Seconds before and after the marker", min_value=0.5,
            max_value=20.0, step=0.5, key=shift_key,
        )
    else:
        shift = 2.0
    start, end = marker_time - shift, marker_time + shift
    show_signal(selected_channel, marker_time=marker_time, marker_name=marker_name,
                start_time=start, end_time=end)
    st.caption(f"Review window: {start:.2f}–{end:.2f} seconds (±{shift:.1f} seconds)")
    if adjusting:
        if st.button("Back to ±2 sec"):
            st.session_state[adjust_key] = False
            st.rerun()
    elif st.button("Change window"):
        st.session_state[adjust_key] = True
        st.session_state[shift_key] = 2.0
        st.rerun()

    if st.button("Use this window and calculate max", type="primary"):
        try:
            value = get_max_from_data(
                selected_channel, marker_time, selected_channel.samples_per_second,
                shift=shift,
            )
            if not np.isfinite(value):
                raise ValueError("No finite MVC value was calculated.")
        except Exception as exc:
            reason = f"{muscle} MVC calculation failed: {type(exc).__name__}: {exc}"
            add_issue(reason)
            st.error(reason)
        else:
            st.session_state.results[muscle]["mvc"] = {
                "value": float(value), "marker": marker_name, "shift": float(shift),
                "start": float(start), "end": float(end),
            }
            st.session_state.stage = "max_result"
            st.rerun()
    st.stop()


# 7. MVC result: accept or discard it, then advance independently.
if st.session_state.stage == "max_result":
    mvc = st.session_state.results[muscle]["mvc"]
    st.success(f"{muscle} max: {mvc['value']:.6f}")
    st.caption(f"{mvc['marker']}: {mvc['start']:.2f}–{mvc['end']:.2f} seconds")
    if st.button("Discard MVC and flag for manual review"):
        skip_measurement(muscle, "mvc", "Calculated value rejected during researcher review")
    if st.button("Continue", key=f"continue_max_{muscle}"):
        next_muscle_or_review()
    st.stop()
