# Dashel Ruiz Perez 11/2026
import pandas as pd
# ============================================================
# 0. IMPORTS
import streamlit as st
from pathlib import Path
from helpers import *
import time
# TEST SUPPORT: Remove this import if removing the Load test data button.
from test_data import load_test_recording, TEST_FILE
from journal_text_extraction import extract_journal_text_bs4

# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

MUSCLES = ["ZM", "CS"]

# Each muscle uses a different marker for the max/MVC step.
MAX_MARKERS = {
    "ZM": "SMILE2",
    "CS": "Furrow2",
}

OUTPUT_FOLDER = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_FOLDER / "result.csv"


# ============================================================
# 2. SMALL HELPER FUNCTIONS FOR THIS STREAMLIT PAGE
# ============================================================

def calculate_max_window(channel, start_time, end_time):
    fs = channel.samples_per_second

    start_index = int(start_time * fs)
    end_index = int(end_time * fs)

    section = channel.data[start_index:end_index]

    if len(section) == 0:
        return None

    return np.max(section)


# ============================================================
# 3. SESSION STATE
# ============================================================
#
# Streamlit reruns this whole file from top to bottom after almost
# every user interaction.
#
# Session State remembers where we are between those reruns.
# ============================================================


if "acq_data" not in st.session_state:
    st.session_state.acq_data = None

if "file_signature" not in st.session_state:
    st.session_state.file_signature = None

if "current_muscle" not in st.session_state:
    st.session_state.current_muscle = 0

if "stage" not in st.session_state:
    st.session_state.stage = "upload"

if "results" not in st.session_state:
    st.session_state.results = {}

if "study_id" not in st.session_state:
    st.session_state.study_id = ""

if "cal_error" not in st.session_state:
    st.session_state.cal_error = None

if "needs_manual_review" not in st.session_state:
    st.session_state.needs_manual_review = False

# TEST SUPPORT: Real ACQ uploads work with this enabled; nothing needs disabling.
# To remove test support entirely, remove all TEST SUPPORT blocks together.
# Keep the fixed CSV_PATH = OUTPUT_FOLDER / "result.csv" near the top.
if "is_test_data" not in st.session_state:
    st.session_state.is_test_data = False

if st.session_state.is_test_data:
    CSV_PATH = OUTPUT_FOLDER / "test_results.csv"
else:
    CSV_PATH = OUTPUT_FOLDER / "result.csv"

# ============================================================
# 4. PAGE HEADER
# ============================================================

title_column, file_column = st.columns([3, 2])

with title_column:
    st.title("Baseline acq extractor")

with file_column:
    if st.session_state.acq_data is not None:
        st.caption("Current recording")

        file_name = st.session_state.file_signature[0]
        st.write(file_name)

        channel_count = len(st.session_state.acq_data.channels)
        st.caption(f"Channels: {channel_count}")

st.divider()

# TEST SUPPORT: Remove this message block if removing synthetic-data support.
# It stays hidden automatically when a real ACQ file is loaded.
if st.session_state.is_test_data:
    st.info("Synthetic test recording — results save to test_results.csv.")

# ============================================================
# 5. FILE UPLOAD
# ============================================================

if st.session_state.stage == "upload":

    # TEST SUPPORT: To hide synthetic loading, comment out this entire button block.
    # Keep the state initialization above unless removing all test support together.
    if st.button("Load test data"):
        st.session_state.acq_data = load_test_recording()

        st.session_state.file_signature = (
            TEST_FILE.name,
            TEST_FILE.stat().st_size,
            "synthetic",
        )

        st.session_state.study_id = "1000"
        st.session_state.is_test_data = True
        st.session_state.current_muscle = 0
        st.session_state.results = {}
        st.session_state.needs_manual_review = False
        st.session_state.cal_error = None

        for muscle in MUSCLES:
            st.session_state.pop(f"adjust_max_window_{muscle}", None)
            st.session_state.pop(f"shift_{muscle}", None)

        if st.session_state.is_test_data:
            st.info(
                "Synthetic test recording — results save to test_results.csv."
            )

        st.session_state.stage = "overview"
        st.rerun()

    # ==========================================================================

    uploaded_file = st.file_uploader('Choose a *.acq file', type=['acq'])

    if uploaded_file is None:
        st.info("Please upload a *.acq file")
        st.stop()

    if uploaded_file is not None:
        file_signature = (uploaded_file.name, uploaded_file.size, uploaded_file.type)

        if st.session_state.file_signature != file_signature:
            try:
                acq_data = load_acq_file(uploaded_file)
            except Exception:
                st.error(
                    "Could not read this ACQ file. "
                    "Please confirm it is a valid BIOPAC .acq file."
                )
                st.stop()

            if acq_data is None:
                st.error("Please upload a *.acq file")
                st.stop()

            st.session_state.acq_data = acq_data
            st.session_state.file_signature = file_signature
            # TEST SUPPORT: Keep while the test button exists; real uploads use result.csv.
            # Remove this assignment only when removing synthetic-data support entirely.
            st.session_state.is_test_data = False

            # Extract ID
            study_id = extract_study_id(uploaded_file.name)
            st.session_state.study_id = study_id
            st.session_state.study_id_input = study_id
            st.session_state.stage = "overview"
            st.rerun()

acq_data = st.session_state.acq_data

# ============================================================
# 6. FILE INFORMATION
# ============================================================

if st.session_state.stage == "overview":

    file_info_column, journal_column = st.columns(2)
    if acq_data is not None:
        with file_info_column:
            st.subheader("File information")
            st.write(f"File name: {st.session_state.file_signature[0]}")
            st.write(f"Number of channels: {len(acq_data.channels)}")
            channel_list = ["- " + channel.name for channel in acq_data.channels]
            st.markdown("\n".join(channel_list))
        try:
            if acq_data.journal:
                with journal_column:
                    st.subheader("Journal Information")
                    # Example usage - replace with actual journal text extraction logic
                    journal_text = extract_journal_text_bs4(acq_data.journal)
                    st.text_area("Journal Text", value=journal_text, height=300)
        except Exception as e:
            with journal_column:
                st.write("No Journal Information")

    st.divider()

    # ============================================================
    # 7. OVERVIEW / START
    # ============================================================
    st.info(
        "File loaded successfully. Start the analysis when you are ready."
    )

    if st.button("Start Calculation"):
        st.session_state.stage = "baseline"
        st.rerun()
    st.stop()

# ============================================================
# 8. DETERMINE THE CURRENT MUSCLE
# ============================================================
#
# THIS REPLACES:
#
#     for muscle in muscles:
#
# Only ONE muscle is active at a time.
# ============================================================

if st.session_state.stage == "baseline":
    muscle_index = st.session_state.current_muscle

    if muscle_index >= len(MUSCLES):
        st.session_state.stage = "review"
        st.rerun()

    muscle = MUSCLES[muscle_index]

    selected_channel = find_muscle_channel(acq_data, muscle)

    if selected_channel is None:
        st.error(f"Could not find RMS channel for {muscle}")
        time.sleep(3)
        st.session_state.needs_manual_review = True
        st.session_state.current_muscle += 1
        st.rerun()

    # Create the result container for this muscle if needed.
    if muscle not in st.session_state.results:
        st.session_state.results[muscle] = {}

    st.subheader(
        f"Muscle {muscle_index + 1}/{len(MUSCLES)}: {muscle}"
    )

    # ============================================================
    # 9. BASELINE STEP
    # ============================================================
    #
    # Desired behavior:
    #
    #   1. Show the FULL signal.
    #   2. Calculate the baseline automatically ONCE.
    #   3. Show the baseline number.
    #   4. User visually checks the full graph.
    #   5. User presses Continue.
    #
    # There is NO baseline adjustment/recalculation form.
    # ============================================================

    st.write("### Full signal")
    # Show the entire signal
    fig = plot_channel(selected_channel)

    st.plotly_chart(fig, width="stretch")

    if "baseline" not in st.session_state.results[muscle]:

        try:
            baseline = calculate_baseline(selected_channel, acq_data)
        except ValueError as exc:
            st.error(str(exc))
            time.sleep(3)
            st.session_state.needs_manual_review = True
            st.session_state.stage = "max_window"
            st.rerun()

        if baseline is None or not np.isfinite(baseline["value"]):
            st.error(f"Could not calculate baseline for muscle {muscle}")
            time.sleep(3)
            st.session_state.needs_manual_review = True
            st.session_state.stage = "max_window"
            st.rerun()

        st.session_state.results[muscle]["baseline"] = baseline

    baseline = (st.session_state.results[muscle]["baseline"])

    st.write(f"**{muscle} baseline:** {baseline['value']:.4f}")

    st.caption(f"Selected baseline interval: {baseline['start']:.2f} to {baseline['end']:.2f} seconds")

    st.info("Check the full signal above. If the baseline result looks reasonable, continue to the max step.")

    continue_calculations, skip_baseline = st.columns(2)

    with continue_calculations:
        if st.button("Continue to max", key=f"continue_baseline_{muscle}"):
            st.session_state.stage = "max_window"
            st.rerun()

    with skip_baseline:
        if st.button("Skip baseline and flag for manual review"):
            st.session_state.results[muscle].pop("baseline", None)
            st.session_state.needs_manual_review = True
            st.session_state.stage = "max_window"
            st.rerun()
    st.stop()

# ============================================================
# 10. MAX WINDOW REVIEW
# ============================================================
#
# ZM -> SMILE2
# CS -> Furrow2
#
# Desired behavior:
#
#   1. Find the correct marker.
#   2. ALWAYS show marker +/- 2 seconds first.
#   3. Ask the researcher:
#          - Use this window
#          - Change window
#   4. If the default +/- 2 second window is accepted,
#      calculate the max immediately.
#   5. Only show a number input if the researcher asks to
#      change the window.
#   6. When changing the window, update the graph as the shift
#      changes, then calculate only after final confirmation.
# ============================================================

if st.session_state.stage == "max_window":
    muscle_index = st.session_state.current_muscle
    muscle = MUSCLES[muscle_index]

    selected_channel = find_muscle_channel(acq_data, muscle)

    marker_name = MAX_MARKERS[muscle]

    marker_time = time_by_marker(acq_data, marker_name)

    if marker_time is None:
        st.error(f"Could not find marker {marker_name} for muscle {muscle}")
        time.sleep(3)
        st.session_state.needs_manual_review = True
        st.session_state.current_muscle += 1
        if muscle == "CS":
            st.session_state.stage = "review"
        else:
            st.session_state.stage = 'baseline'
        st.rerun()

    st.write(f"### Max window for {muscle} (marker: {marker_name})")
    st.write(f"Marker time: **{marker_time:.2f} seconds**")

    adjust_key = f"adjust_max_window_{muscle}"

    if adjust_key not in st.session_state:
        st.session_state[adjust_key] = False

    if not st.session_state[adjust_key]:
        shift = 2.0
        start_time = marker_time - shift
        end_time = marker_time + shift

        max_fig = plot_channel(
            selected_channel,
            marker_time=marker_time,
            marker_name=marker_name,
            start_time=start_time,
            end_time=end_time,
        )

        st.plotly_chart(max_fig, width="stretch")

        st.info(
            "Check the graph above. If the ±2 second window contains "
            "the section you want, use it. Otherwise choose Change window."
        )

        col1, col2 = st.columns(2)

        with col1:
            use_default = st.button(
                f"Use ±2 sec and calculate {muscle} max",
                key=f"use_default_max_{muscle}",
                type="primary",
            )

        with col2:
            change_window = st.button(
                "Change window",
                key=f"change_max_window_{muscle}",
            )

        if use_default:
            fs = selected_channel.samples_per_second
            max_value = get_max_from_data(selected_channel, marker_time, fs, shift=shift)
            st.session_state.results[muscle]["mvc"] = {
                "value": float(max_value),
                "marker": marker_name,
                "shift": float(shift),
                "start": float(start_time),
                "end": float(end_time),
            }

            st.session_state.stage = "max_result"
            st.rerun()

        if change_window:
            st.session_state[adjust_key] = True

            # Start manual adjustment from the normal 2-second value.
            shift_key = f"shift_{muscle}"
            if shift_key not in st.session_state:
                st.session_state[shift_key] = 2.0
            st.rerun()

        # --------------------------------------------------------
        # 10B. MANUAL WINDOW ADJUSTMENT
        # --------------------------------------------------------
        # This section appears ONLY if the researcher selected
        # "Change window" above.
        # --------------------------------------------------------

    else:

        shift = st.number_input(
            "Seconds before and after the marker",
            min_value=0.5,
            max_value=20.0,
            step=0.5,
            key=f"shift_{muscle}",
        )

        start_time = marker_time - shift
        end_time = marker_time + shift

        # Streamlit reruns when the number changes, so this chart
        # automatically previews the newly selected window.
        max_fig = plot_channel(
            selected_channel,
            marker_time=marker_time,
            marker_name=marker_name,
            start_time=start_time,
            end_time=end_time,
        )

        st.plotly_chart(
            max_fig,
            width="stretch",
        )

        if st.button("Cannot find a usable window — skip max", key=f"skip_max_{muscle}", ):
            st.session_state.results[muscle].pop("mvc", None)
            st.session_state.needs_manual_review = True
            st.session_state.current_muscle += 1

            if st.session_state.current_muscle >= len(MUSCLES):
                st.session_state.stage = "review"
            else:
                st.session_state.stage = "baseline"

            st.rerun()

        st.caption(
            f"Adjusted review window: "
            f"{start_time:.2f} to {end_time:.2f} seconds "
            f"(±{shift:.1f} seconds)"
        )

        st.info(
            "Adjust the window until the graph looks correct. "
            "The max is not calculated until you confirm below."
        )

        col1, col2 = st.columns(2)

        with col1:
            confirm_adjusted = st.button(
                f"Use this window and calculate {muscle} max",
                key=f"calculate_adjusted_max_{muscle}",
                type="primary",
            )

        with col2:
            use_default_again = st.button(
                "Back to ±2 sec",
                key=f"back_to_default_{muscle}",
            )

        if confirm_adjusted:
            fs = selected_channel.samples_per_second

            max_value = get_max_from_data(
                selected_channel,
                marker_time,
                fs,
                shift=shift,
            )

            st.session_state.results[muscle]["mvc"] = {
                "value": float(max_value),
                "marker": marker_name,
                "shift": float(shift),
                "start": float(start_time),
                "end": float(end_time),
            }

            st.session_state.stage = "max_result"
            st.rerun()

        if use_default_again:
            st.session_state[adjust_key] = False
            st.rerun()

    st.stop()

# ============================================================
# 11. SHOW THE CALCULATED MAX
# ============================================================

if st.session_state.stage == "max_result":
    muscle = MUSCLES[st.session_state.current_muscle]
    mvc = st.session_state.results[muscle]["mvc"]

    st.success(f"{muscle} max calculated")

    st.write(f"**{muscle} max:** {mvc['value']:.4f}")
    st.write(f"Marker: {mvc['marker']}")
    st.write(f"Shift: {mvc['shift']:.1f} seconds")

    st.caption(f"Final max window: {mvc['start']:.2f} to {mvc['end']:.2f} seconds")

    if st.button("Continue", key=f"continue_max_nuscle_{muscle}"):
        # If another muscle remains, move to it.
        if st.session_state.current_muscle < len(MUSCLES) - 1:

            st.session_state.current_muscle += 1
            st.session_state.stage = "baseline"

        # Otherwise both muscles are complete.
        else:
            st.session_state.stage = "review"

        st.rerun()

    st.stop()
# ============================================================
# 12. FINAL REVIEW
# ============================================================

if st.session_state.stage == 'review':
    st.subheader("Final results")

    results = st.session_state.results

    result_row = {
        "study_id": st.session_state.study_id,
        "CS baseline": results.get("CS", {}).get("baseline", {}).get("value"),
        "ZM baseline": results.get("ZM", {}).get("baseline", {}).get("value"),
        "CS MVC": results.get("CS", {}).get("mvc", {}).get("value"),
        "ZM MVC": results.get("ZM", {}).get("mvc", {}).get("value"),
        "needs_manual_review": st.session_state.needs_manual_review,
    }

    df = pd.DataFrame([result_row])
    st.dataframe(df, width='stretch', hide_index=True)

    if st.session_state.needs_manual_review:
        st.warning("Analysis finished. This recording needs manual review.")
    else:
        st.success("All four calculations are complete.")

    st.divider()
    if st.button("Save Results"):
        # Implement save/append workflow here
        if not st.session_state.study_id:
            st.error("No study_id provided.")
            st.stop()

        try:
            existing_data = pd.read_csv(CSV_PATH, dtype={"study_id": str})

            if st.session_state.study_id in existing_data['study_id'].values:
                st.warning("Study ID already exists")
            else:
                st.info("This study is new and can be added.")
                existing_data = pd.concat([existing_data, df], ignore_index=True)
                existing_data.to_csv(CSV_PATH, index=False)
                st.success(f"Study ID: {st.session_state.study_id} added successfully.")

        except FileNotFoundError:
            st.info("The CSV does not exists yet.")
            df.to_csv(CSV_PATH, index=False)
            st.success(f"File with study ID: {st.session_state.study_id} created successfully.")

    st.divider()
    st.caption(
        "Start a new file clears the current analysis, including unsaved results. "
        "The saved CSV will not be changed."
    )

    if st.button("Start a new file"):
        # TEST SUPPORT: Clear test mode before another recording is loaded.
        # Remove this assignment only when removing synthetic-data support entirely.
        st.session_state.is_test_data = False
        st.session_state.acq_data = None
        st.session_state.file_signature = None

        st.session_state.study_id = ""
        st.session_state.pop("study_id_input", None)

        st.session_state.results = {}
        st.session_state.needs_manual_review = False
        st.session_state.cal_error = None

        st.session_state.current_muscle = 0
        st.session_state.stage = "upload"

        for muscle in MUSCLES:
            st.session_state.pop(f"adjust_max_window_{muscle}", None)
            st.session_state.pop(f"shift_{muscle}", None)

        st.rerun()
