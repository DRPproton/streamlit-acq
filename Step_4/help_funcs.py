import numpy as np
import re

def get_metrics(selected_channel, start_time: int, end_time: int, fs: int, baseline: float | int):

    start_index = int(start_time * fs)
    end_index = int(end_time * fs)

    section = selected_channel.data[start_index: end_index]
    return {
        "max": np.max(section),
        "min": np.min(section),
        "mean": np.mean(section),
        "std_ddof0": np.std(section),
        "std_ddof1": np.std(section, ddof=1),
        "delta": np.mean(section) - baseline
    }


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