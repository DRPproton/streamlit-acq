# EMG processing steps

Verified against the supplied video transcript. Baseline MVC values have already been obtained before this workflow begins.

1. Open the participant's **APP, PsychoPy, and SlowRate** files.
2. Unhide raw channels **3 and 4**.
3. Delete all other channels, including the LED channel.
4. Select raw **ZM**.
5. Apply **FIR band-pass: 28–500 Hz**.
6. Apply **comb band-stop: 60 Hz, Q = 5** to the new filtered waveform.
7. Apply **RMS: 1,000 samples** to that result.
8. Delete ZM's raw and intermediate waveforms; retain its RMS waveform.
9. Repeat steps **5–8 for CS**, starting with raw CS.
10. Create a **%MVC waveform for each muscle**: `RMS / (baseline MVC / 100)`.
11. Change the normalized waveforms' units to **%**. Keep both RMS and %MVC waveforms—**four channels total**.
12. Complete steps **2–11 for each recording**, then save each as a new **`_filter`** file inside **`filter_edit_files`**. Preserve the original raw files.
13. Duplicate the filtered APP file for separate video and interview edits.
14. Review journals and event summaries for timing exceptions.
15. **Video:** remove everything before the video cue, then retain **120 seconds**. The manipulation occurs at **60 seconds** in the cropped recording.
16. **Interview:** retain everything from its star marker to the end.
17. **PsychoPy:** retain everything from its star marker to the end.
18. **SlowRate:** retain everything from its star marker to the end.
19. Delete the pasted event summaries because their timestamps are outdated.
20. Save the four edited files: **`1_video_filter_edit`**, **`2_interview_filter_edit`**, **`PsychoPy_filter_edit`**, and **`SlowRate_filter_edit`**. Keep the participant identifier in each filename.

## Differences in the Python notebook

The notebook is [01_process_acq.ipynb](01_process_acq.ipynb).

- Hidden channels are read automatically; unused channels are excluded rather than deleted. Select the notebook indices corresponding to original channels 3 and 4, and confirm which muscle each contains.
- Baseline MVC values are entered manually for each muscle.
- HDF5 retains raw and intermediate signals; text exports contain the four final channels.
- Original journals are preserved, including any old event summaries. Retained event-marker times are adjusted to each segment's new start.
- Outputs are **HDF5, text, and JSON**, rather than `.acq`.
- **Exact filtering remains unverified:** the transcript specifies cutoffs, Q, and RMS window size, but not FIR length, padding, or RMS alignment. Its explanation of Q as “five multiples” does not establish the harmonic count used by AcqKnowledge. The notebook uses notches at all 60 Hz harmonics below Nyquist.
