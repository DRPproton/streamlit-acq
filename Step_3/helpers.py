import bioread
import numpy as np
import pandas as pd
from scipy import signal
from pathlib import Path
import json
import h5py


def compare(actual, expected, sampling_rate):
    """Compare aligned Python output against an AcqKnowledge reference.
        
        Parameters
        ----------
        actual, expected : array_like
            Finite, nonempty 1D signals with identical shape, units and time origin.
            Pass Python output as actual and AcqKnowledge output as expected.
        sampling_rate : float
            Positive finite sample rate in Hz shared by the two signals.
        
        Returns
        -------
        pandas.Series
            Maximum absolute error, RMSE, relative RMSE in percent of expected
            signal RMS, signed mean error (actual - expected), and the first worst
            sample and its time in seconds. Relative RMSE is NaN for a zero-RMS
            reference. Sample/time positions are relative to the supplied arrays;
            add the slice offset when comparing an interior segment.
        
        Raises
        ------
        ValueError
            If signal shapes, values, or the sampling rate are invalid.
        
        Notes
        -----
        No alignment, resampling, scaling or rounding is performed. Tiny residuals
        are expected from floating-point arithmetic. pandas may display the sample
        index as a float because the Series also contains floating-point metrics.
        """
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



def fir_bandpass(data, sampling_rate, fir_window=[0.44959, 0.49364, 0.05677, 0.0],
                low_hz=28.0, high_hz=500.0, num_taps=285):
    """Apply the FIR band-pass implementation.
        
        Parameters
        ----------
        data : array_like
            Finite, nonempty 1D input signal.
        sampling_rate : float
            Positive finite sampling rate in Hz.
        fir_window : sequence of float
            General-cosine weights; defaults to the custom Blackman -61 dB weights.
            The window is sampled with sym=False (periodic), as validated here.
        low_hz, high_hz : float
            Cutoff frequencies satisfying 0 < low_hz < high_hz < sampling_rate / 2.
        num_taps : int
            Odd coefficient count, at least three. The default 285 was validated
            for 2000 Hz and 28-500 Hz. It is not recalculated for other settings.
        
        Returns
        -------
        numpy.ndarray
            New floating-point array with the input length and units.
        
        Raises
        ------
        ValueError
            If the signal, sampling rate, cutoffs, tap count is invalid.
        
        Notes
        -----
        Uses an unscaled rectangular-window firwin base multiplied by the periodic
        custom window, endpoint-value padding and centered valid convolution.
        Do not describe the resulting coefficients as symmetric or the filter as
        exactly zero-phase. No passband gain normalization is applied.
        The current FIR -> comb -> RMS chain matched five tested muscle/recording
        combinations to floating-point precision at the protocol settings. Other
        settings require validation. Process the full recording before cropping.
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
        fir_window,
        sym=False,
    )
    coefficients *= window

    # Repeat endpoint values and center the filtered output.
    half_length = (num_taps - 1) // 2
    padded = np.pad(x, (half_length, half_length), mode="edge")

    return signal.convolve(padded, coefficients, mode="valid")



def comb_band(data, sampling_rate, base_hz=60.0, q=5.0):
    """Apply the validated cascade of RBJ notch filters to remove integer multiples of base_hz below Nyquist.
        
        Parameters
        ----------
        data : array_like
            Finite, nonempty 1D FIR-filtered signal.
        sampling_rate : float
            Positive finite sampling rate in Hz.
        base_hz : float
            Positive fundamental below Nyquist; defaults to 60 Hz.
        q : float
            Positive finite quality factor used for every notch; defaults to 5.
        
        Returns
        -------
        numpy.ndarray
            New floating-point array with unchanged length and units.
        
        Raises
        ------
        ValueError
            If the input signal or parameters are invalid.
        
        Notes
        -----
        Cascades one forward lfilter pass at each positive integer multiple of
        base_hz strictly below Nyquist, in ascending order. Each stage starts with
        lfilter_zi(b, a) multiplied by that stage's first input sample, representing
        constant prehistory. This is not zero-state or forward-backward filtering.
        At 2000 Hz and 60 Hz the cascade contains 16 notches, from 60 through 960 Hz.
        Agreement was checked at the project settings; it is not a guarantee for
        all possible settings. Process the full recording before cropping.
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
     
        zi = signal.lfilter_zi(b, a) * filtered[0]
        filtered, _ = signal.lfilter(b, a, filtered, zi=zi)

    return filtered



def integration_moving_rms(data, window_samples=1000):
    """Compute the trailing RMS.
        
        Parameters
        ----------
        data : array_like
            Finite, nonempty 1D FIR-and-comb-filtered signal.
        window_samples : int
            Window length of at least two; defaults to 1000 (0.5 s at 2000 Hz).
        
        Returns
        -------
        numpy.ndarray
            New nonnegative floating-point array with input length and units.
        
        Raises
        ------
        ValueError
            If the signal or window length is invalid.
        
        Notes
        -----
        For sample n, sum the squared current sample and up to window_samples - 1
        preceding samples. Divide by max(min(n + 1, window_samples) - 1, 1), then
        take the square root. Thus sample zero equals abs(data[0]); a full window
        uses denominator window_samples - 1. There is no mean subtraction and no
        reflected prehistory. This intentionally differs from conventional RMS
        with denominator equal to the number of samples. Apply before cropping.
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



def read_acq_files(files_suffix):
    """Load acknowledge files into a dictionary of bioread objects.

    Args:
        files_suffix (_type_): _dictionary of file suffixes and paths to read_

        Example:
            files_suffix = {
                "APP": Path(f"{folder_root_path}{study_id}_fEMG_div_2APP_raw.acq"),
                "PsychoPy": Path(f"{folder_root_path}{study_id}_fEMG_div_3PsychoPy_raw.acq"),
                "SlowRate": Path(f"{folder_root_path}{study_id}_fEMG_div_4SlowRate_raw.acq"),
            }
    Raises:
        OSError: 
            If any of the files cannot be opened or read, an OSError is raised
            with a message indicating the issue. The user is advised to check
            the source folder and try again.
    Returns:
       dict: 
            Task names mapped to loaded bioread recordings. Source files are
            unchanged. An empty mapping returns an empty dictionary
    """
    acq_data = {}
    for task, path in files_suffix.items():
        try:
            acq_data[task] = bioread.read(path)
        except OSError as e:
            print(f"Error {e} Could not open/read file: {path}")
            raise OSError("Please check source folder and try again!")
    return acq_data



def show_channels(data):
    """Return a table of channel information for each task in the data dictionary.

        Args:
            dict: Dictonary of task names mapped to loaded bioread recordings. 
                From read_acq_files function.

        Returns:
            pd.DataFrame:
                One row per channel with task, index, order_num, name, units,
                rate_hz and samples. index is the zero-based position in
                recording.channels; order_num is the source channel identifier.
                If there are no channels, the returned table has no columns.
    """  
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary of task names to bioread recordings.")

    channel_rows = []
    try:
        for task, recording in data.items():
            for index, channel in enumerate(recording.channels):
                channel_rows.append({"task": task, "index": index, "order_num": channel.order_num,
                                    "name": channel.name, "units": channel.units,
                                    "rate_hz": channel.samples_per_second, "samples": len(channel.data)})
    except Exception as e:
        raise ValueError(f"Error occurred while processing channel information: {e}")
    
    return pd.DataFrame(channel_rows)



def choose_indexes_per_file(data_df, file_name):
    """Map exact channel names to zero-based indices for one task.
    
        Parameters
        ----------
        data_df : pandas.DataFrame
            Channel inventory containing task, index and name columns.
        file_name : str
            Task key, such as APP, PsychoPy or SlowRate, not a filesystem path.

        Returns
        -------
        dict
            Channel names mapped to their indices. A task without rows returns
            an empty dictionary. Duplicate names retain the last matching index.

        Notes
        -----
        Confirm names are unique before using this lookup. This function does
        not validate duplicates or the resulting mapping against a recording.
    """
    if not isinstance(data_df, pd.DataFrame):
        raise ValueError("data_df must be a pandas DataFrame.")
    if "task" not in data_df.columns or "index" not in data_df.columns or "name" not in data_df.columns:
        raise ValueError("data_df must contain 'task', 'index', and 'name' columns.")
    if not isinstance(file_name, str):
        raise ValueError("file_name must be a string.")
    try:
        subset = data_df.loc[data_df["task"] == file_name, ["task", "index", "name"]]
    except Exception as e:
        raise ValueError(f"Error occurred while filtering data: {e}")
    
    return dict(zip(subset["name"], subset["index"]))



def get_reference_channels(data, taks, app_idx, muscle_name):
    data = data[taks]
    raw_index = app_idx[f"{muscle_name} - EMG100C"]
    reference_indices_fir = app_idx[f"{muscle_name} - FIR"]
    reference_indices_comb = app_idx[f"{muscle_name} - Comb"]
    if muscle_name == "ZM":
        try:
            reference_indices_integrate = app_idx[f"{muscle_name} - Int"]
        except KeyError:
            reference_indices_integrate = app_idx[f"{muscle_name} - Integrate"]
    else:
        reference_indices_integrate = app_idx[f"{muscle_name} - Integrate"]

    raw_channel = data.channels[raw_index]
    reference_channel_fir = data.channels[reference_indices_fir]
    reference_channel_comb = data.channels[reference_indices_comb]
    reference_channel_integrate = data.channels[reference_indices_integrate]

    return raw_channel, reference_channel_fir, reference_channel_comb, reference_channel_integrate


def get_channel_idx(data, taks, app_idx, muscle_name):
    try:
        data = data[taks]
        raw_index = app_idx[f"{muscle_name} - EMG100C"]
        raw_channel = data.channels[raw_index]
    except KeyError as e:
        raise KeyError(f"Channel for {muscle_name} not found in task {taks}: {e}")
    return raw_channel


def save_processed_emg_h5(output_path, *, recording, source_path, sampling_rate,
                        zm_rms, zm_percent, cs_rms, cs_percent, zm_mvc, cs_mvc):
    """Save four processed EMG channels on the original recording clock."""
    output_path = Path(output_path)
    sampling_rate = float(sampling_rate)

    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate must be positive and finite.")

    mvc = {"ZM": float(zm_mvc), "CS": float(cs_mvc)}
    if any(not np.isfinite(value) or value <= 0 for value in mvc.values()):
        raise ValueError("Both MVC values must be positive and finite.")

    signals = {
        "ZM mv": (np.asarray(zm_rms, dtype=float), "mV"),
        "ZM %": (np.asarray(zm_percent, dtype=float), "% MVC"),
        "CS mv": (np.asarray(cs_rms, dtype=float), "mV"),
        "CS %": (np.asarray(cs_percent, dtype=float), "% MVC"),
    }

    for label, (values, _) in signals.items():
        if values.ndim != 1 or values.size == 0:
            raise ValueError(f"{label} must be a nonempty 1D array.")
        if not np.isfinite(values).all():
            raise ValueError(f"{label} contains NaN or infinity.")

    lengths = {values.size for values, _ in signals.values()}
    if len(lengths) != 1:
        raise ValueError("All four channels must have the same sample count.")

    # Preserve event times on the original recording clock.
    source_metadata = {
        "filename": Path(source_path).name,
        "base_sampling_rate_hz": float(recording.samples_per_second),
        "journal": recording.journal,
        "event_markers": [
            {
                "text": marker.text,
                "time_index": float(marker.time_index),  # Seconds
                "sample_index": int(marker.sample_index),  # Source sample grid
                "type_code": marker.type_code,
                "channel_number": marker.channel_number,
            }
            for marker in (recording.event_markers or [])
        ],
    }

    processing_metadata = {"mvc_mV": mvc}

    # Serialize before creating the file.
    source_json = json.dumps(source_metadata, ensure_ascii=False, allow_nan=False)
    processing_json = json.dumps(processing_metadata, allow_nan=False)
    text_dtype = h5py.string_dtype(encoding="utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # "x" creates a new file and refuses to overwrite an existing one.
    with h5py.File(output_path, "x") as h5:
        h5.attrs.update(
            format="processed-facial-emg",
            schema_version=1,
            sampling_rate_hz=sampling_rate,
            sample_count=lengths.pop(),
            time_origin_seconds=0.0,
        )

        h5.create_dataset("channel_order", data=list(signals), dtype=text_dtype)
        group = h5.create_group("signals", track_order=True)

        for label, (values, units) in signals.items():
            dataset = group.create_dataset(
                label,
                data=values,
                compression="gzip",
                shuffle=True,
                fletcher32=True,
            )
            dataset.attrs.update(
                label=label,
                units=units,
                sampling_rate_hz=sampling_rate,
            )

        metadata = h5.create_group("metadata")
        metadata.create_dataset("source", data=source_json, dtype=text_dtype)
        metadata.create_dataset("processing", data=processing_json, dtype=text_dtype)

    return output_path


def express_as_percent_mvc(rms_signal, mvc_value):
    """Convert a processed RMS waveform to %MVC using a same-unit MVC."""
    rms = np.asarray(rms_signal, dtype=float)
    mvc = float(mvc_value)

    if rms.ndim != 1 or rms.size == 0 or not np.isfinite(rms).all():
        raise ValueError("rms_signal must be a nonempty, finite 1D array.")
    if not np.isfinite(mvc) or mvc <= 0:
        raise ValueError("mvc_value must be positive and finite.")

    return rms / (mvc / 100.0)