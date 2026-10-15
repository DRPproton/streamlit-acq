import neurokit2 as nk
import numpy as np
import scipy.signal

def neurokit_biopac_pipeline(raw_emg, sampling_rate=2000, mvc_value=0.101):
    # Step 1: Bandpass filter (28 - 500 Hz)
    # Using butterworth_ba / SOS filter in NeuroKit2:
    emg_band = nk.signal_filter(
        raw_emg,
        sampling_rate=sampling_rate,
        lowcut=28,
        highcut=500,
        method="butterworth",
        order=4
    )

    # Step 2: Comb notch filter for 60 Hz harmonics
    # Loop standard iirnotch across harmonics up to Nyquist
    emg_clean = emg_band.copy()
    for freq in range(60, int(sampling_rate / 2), 60):
        emg_clean = nk.signal_filter(
            emg_clean,
            sampling_rate=sampling_rate,
            method="iirnotch",
            cutoff=freq,
            Q=5.0
        )

    # Step 3: Moving RMS (1000 samples)
    # Square the signal, smooth over 1000 samples, and take square root
    squared = emg_clean ** 2
    mean_squared = nk.signal_smooth(squared, method="convolution", kernel="boxcar", size=1000)
    rms_envelope = np.sqrt(mean_squared)

    # Step 4: Express as %MVC
    pct_mvc = rms_envelope / (mvc_value / 100.0)

    # Step 5: Feed back into NeuroKit2 for activation detection
    activations, info = nk.emg_activation(
        rms_envelope,
        sampling_rate=sampling_rate,
        method="threshold"
    )

    return pct_mvc, activations, info