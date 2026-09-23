import pandas as pd
import numpy as np
import bioread
from plotly import graph_objects as go
import re


def load_acq_file(file):
    """
    Load a .acq file.

    Parameters:
    file (file-like object): The .acq file object.

    Returns:
    bioread.Sweep: The loaded .acq file data.
    """
    # Read the .acq file using bioread
    file.seek(0)  # Reset file pointer to the beginning
    return bioread.read_file(file)


def time_by_marker(data, marker_name: str):
    if not data.event_markers:
        return None

    for marker in data.event_markers:
        if marker_name in str(marker):
            return marker.sample_index / data.samples_per_second
    return None


def extract_study_id(filename: str):
    """
    Extract all digits from the BEGINNING of the uploaded filename.

    Examples:
        1234_test.acq      -> "1234"
        123456_ZM.acq      -> "123456"
        00123EMG.acq       -> "00123"
        subject_123.acq    -> ""

    Keep the result as a string so leading zeros are preserved.
    """
    match = re.match(r"^\d+", filename)
    return match.group() if match else None


def ask_for_approval():
    return input("Use this section to calculate the maximum? (y/n): ")


def plot_channel(channel, start_time=None, end_time=None,
                 marker_time=None, marker_name=""):
    fs = channel.samples_per_second
    time_axis = np.arange(len(channel.data)) / fs

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_axis,
        y=channel.data,
        mode="lines",
        name=channel.name,
    ))

    if marker_time is not None:
        fig.add_vline(
            x=marker_time,
            line_dash="dash",
            annotation_text=marker_name,
        )

    fig.update_layout(
        title=channel.name,
        xaxis_title="Time (seconds)",
        yaxis_title=channel.units,
    )

    if start_time is not None and end_time is not None:
        fig.update_xaxes(range=[start_time, end_time])

    return fig


def get_max_from_data(selected_channel, time, fs, shift=1):
    start_time = time - shift
    end_time = time + shift

    start_index = int(start_time * fs)
    end_index = int(end_time * fs)

    section = selected_channel.data[start_index: end_index]
    return np.max(section)


def find_muscle_channel(acq_data, muscle):
    """
    Find the RMS channel for the requested muscle.

    This replaces the nested channel-search code that was originally
    inside the `for muscle in muscles` loop.
    """
    for channel in acq_data.channels:
        if "RMS" in str(channel) and muscle in str(channel):
            return channel
    return None


def calculate_baseline(channel, acq_data):
    """
        Reuse the original baseline algorithm.

        Starting after FURROW1:
          - test 21 possible 60-second windows
          - move the candidate start by 10 seconds each time
          - calculate the mean for each candidate
          - choose the candidate with the smallest mean

        IMPORTANT:
        The baseline is calculated ONCE for the current muscle.
        The user does not manually recalculate it.
    """
    fs = channel.samples_per_second

    furrow1_time = time_by_marker(
        acq_data,
        "FURROW1"
    )

    if furrow1_time is None:
        raise ValueError("FURROW1 marker not found in the data.")

    means = []
    start_times = []

    for i in range(21):
        start_time = furrow1_time + 10 + i * 10
        end_time = start_time + 60

        start_index = int(start_time * fs)
        end_index = int(end_time * fs)

        section = channel.data[start_index:end_index]

        means.append(np.mean(section))
        start_times.append(start_time)

    min_idx = np.argmin(means)

    return {
        "value": float(means[min_idx]),
        "start": float(start_times[min_idx]),
        "end": float(start_times[min_idx] + 60),
    }
