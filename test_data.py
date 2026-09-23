from dataclasses import dataclass
from pathlib import Path

import numpy as np

TEST_FILE = Path(__file__).resolve().with_name("synthetic_recording.npz")


@dataclass
class TestChannel:
    name: str
    data: np.ndarray
    samples_per_second: float
    units: str = "Synthetic units"
    loaded: bool = True

    def __str__(self):
        return self.name


@dataclass
class TestMarker:
    name: str
    sample_index: int

    def __str__(self):
        return self.name


@dataclass
class TestRecording:
    channels: list
    event_markers: list
    samples_per_second: float


def create_test_file():
    """Create a repeatable synthetic recording."""

    sample_count = 908397
    sampling_rate = 2000.0

    target_max = 0.07933997293341269
    target_mean = 0.0034646084345279736

    seconds = np.arange(sample_count) / sampling_rate

    # Two simulated contractions.
    # Their centers match the maximum markers below.
    smile_peak = target_max * np.maximum(
        1 - np.abs(seconds - 150.0) / 1.5,
        0,
    )

    furrow_peak = target_max * 0.8 * np.maximum(
        1 - np.abs(seconds - 154.0) / 1.5,
        0,
    )

    peaks = smile_peak + furrow_peak

    # A low, gently varying background.
    background = (
            0.85 + 0.15 * np.sin(2 * np.pi * seconds / 17.0) ** 2
    )

    # Keep the background from increasing the specified peak maximum.
    background *= 1 - peaks / target_max

    # Ensure that the first sample is exactly zero.
    background[0] = 0.0

    # Choose the background amplitude to match the requested mean.
    background_scale = (
                               target_mean * sample_count - peaks.sum()
                       ) / background.sum()

    zm = peaks + background_scale * background
    cs = zm + 0.02

    # Check the generated ZM signal before saving it.
    assert len(zm) == sample_count
    assert zm.min() == 0.0
    assert np.isclose(zm.max(), target_max, rtol=0, atol=1e-14)
    assert np.isclose(zm.mean(), target_mean, rtol=0, atol=1e-14)

    np.savez_compressed(
        TEST_FILE,
        zm=zm,
        cs=cs,
        sampling_rate=sampling_rate,
        marker_names=np.array(["FURROW1", "SMILE2", "Furrow2"]),
        marker_times=np.array([10.0, 150.0, 154.0]),
    )


def load_test_recording():
    """Create the test file if necessary, then load its channels."""

    if not TEST_FILE.exists():
        create_test_file()

    with np.load(TEST_FILE, allow_pickle=False) as saved:
        sampling_rate = float(saved["sampling_rate"])

        channels = [
            TestChannel(
                name="ZM - RMS",
                data=saved["zm"],
                samples_per_second=sampling_rate,
            ),
            TestChannel(
                name="CS - RMS",
                data=saved["cs"],
                samples_per_second=sampling_rate,
            ),
        ]

        markers = [
            TestMarker(
                name=str(name),
                sample_index=int(round(float(seconds) * sampling_rate)),
            )
            for name, seconds in zip(
                saved["marker_names"],
                saved["marker_times"],
            )
        ]

    return TestRecording(
        channels=channels,
        event_markers=markers,
        samples_per_second=sampling_rate,
    )
