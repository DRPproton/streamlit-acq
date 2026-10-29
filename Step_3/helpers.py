import bioread
import numpy as np
import pandas as pd
from scipy import signal


def compare(actual, expected, sampling_rate):
    actual = np.asarray(actual, dtype=float)
    expected = np.asarray(expected, dtype=float)

    if (
        actual.ndim != 1
        or expected.ndim != 1
        or actual.shape != expected.shape
        or actual.size == 0
    ):
        raise ValueError("Signals must be 1D with the same nonzero length.")

    if not (np.isfinite(actual).all() and np.isfinite(expected).all()):
        raise ValueError("Signals contain missing or infinite samples.")

    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate must be positive and finite.")

    difference = actual - expected
    worst = int(np.argmax(np.abs(difference)))
    rmse = np.sqrt(np.mean(difference**2))
    reference_rms = np.sqrt(np.mean(expected**2))

    return pd.Series({
        "max_absolute_error": np.max(np.abs(difference)),
        "rmse": rmse,
        "relative_rmse_percent": (
            100 * rmse / reference_rms if reference_rms > 0 else np.nan
        ),
        "mean_error": np.mean(difference),
        "worst_sample": worst,
        "worst_time_seconds": worst / sampling_rate,
    })



def biopac_fir_bandpass(data, sampling_rate, low_hz=28.0, high_hz=500.0, num_taps=285):
    """
    Approximate the AcqKnowledge FIR band-pass tested in this project.

    Uses a symmetric custom Blackman window, no gain normalization,
    edge padding, and centered convolution.

    The default 285 coefficients were confirmed in AcqKnowledge for
    the tested 2000 Hz recording. For other settings, supply the
    coefficient count shown in AcqKnowledge.

    Returns a new 1D array with the same length and units as data.
    """
    x = np.asarray(data, dtype=float)

    if x.ndim != 1 or x.size == 0:
        raise ValueError("data must be a nonempty, one-dimensional array.")
    if not np.isfinite(x).all():
        raise ValueError("data contains NaN or infinite values.")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate must be positive and finite.")
    if not 0 < low_hz < high_hz < sampling_rate / 2:
        raise ValueError(
            "Cutoffs must satisfy: 0 < low_hz < high_hz < sampling_rate / 2."
        )
    if (
        isinstance(num_taps, (bool, np.bool_))
        or not isinstance(num_taps, (int, np.integer))
        or num_taps < 3
        or num_taps % 2 == 0
    ):
        raise ValueError("num_taps must be an odd integer of at least 3.")

    # Design the base FIR without gain normalization.
    coefficients = signal.firwin(
        numtaps=num_taps,
        cutoff=[low_hz, high_hz],
        fs=sampling_rate,
        pass_zero=False,
        window="boxcar",
        scale=False,
    )

    # Apply the custom window used in our comparison.
    window = signal.windows.general_cosine(
        num_taps,
        [0.44959, 0.49364, 0.05677, 0.0],
        sym=True,
    )
    coefficients *= window

    # Repeat endpoint values and center the filtered output.
    half_length = (num_taps - 1) // 2
    padded = np.pad(x, (half_length, half_length), mode="edge")

    return signal.convolve(padded, coefficients, mode="valid")



def comb_band_stop_initialized(
    data,
    sampling_rate,
    base_hz=60.0,
    q=5.0,
):
    """
    Experimental comb band-stop using cascaded RBJ notch filters.

    Applies one forward pass with zero initial state at each harmonic
    strictly below Nyquist. Preserves signal length and units.

    Agreement with AcqKnowledge must be checked against its output.
    """
    filtered = np.asarray(data, dtype=float).copy()

    if filtered.ndim != 1 or filtered.size == 0:
        raise ValueError("data must be a nonempty 1D array.")

    if not np.isfinite(filtered).all():
        raise ValueError("data contains NaN or infinite values.")

    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate must be positive and finite.")

    nyquist = sampling_rate / 2

    if not np.isfinite(base_hz) or not 0 < base_hz < nyquist:
        raise ValueError("base_hz must be positive and below Nyquist.")

    if not np.isfinite(q) or q <= 0:
        raise ValueError("q must be positive and finite.")

    frequencies = np.arange(base_hz, nyquist, base_hz)

    for frequency in frequencies:
        omega = 2 * np.pi * frequency / sampling_rate
        alpha = np.sin(omega) / (2 * q)
        cosine = np.cos(omega)

        b = np.array([1.0, -2 * cosine, 1.0])
        a = np.array([1 + alpha, -2 * cosine, 1 - alpha])

        a0 = a[0]
        b /= a0
        a /= a0

        # Initialize each notch as if its input had been constant
        # at that stage's first value before the recording began.
        zi = signal.lfilter_zi(b, a) * filtered[0]
        filtered, _ = signal.lfilter(b, a, filtered, zi=zi)

    return filtered



def biopac_moving_rms(data, window_samples=1000):
    """
    Trailing RMS matching the AcqKnowledge behavior observed so far.

    Denominator:
        max(available_samples - 1, 1)

    Once the window is full, the denominator is window_samples - 1.
    Returns an array with the same length and units as the input.
    """
    x = np.asarray(data, dtype=float)

    if x.ndim != 1 or x.size == 0:
        raise ValueError("data must be a nonempty 1D array.")
    if not np.isfinite(x).all():
        raise ValueError("data contains NaN or infinite values.")
    if (
        isinstance(window_samples, (bool, np.bool_))
        or not isinstance(window_samples, (int, np.integer))
        or window_samples < 2
    ):
        raise ValueError("window_samples must be an integer of at least 2.")

    window_sums = np.convolve(
        x**2,
        np.ones(window_samples),
        mode="full",
    )[:x.size]

    available_samples = np.minimum(
        np.arange(x.size) + 1,
        window_samples,
    )
    denominator = np.maximum(available_samples - 1, 1)

    return np.sqrt(window_sums / denominator)