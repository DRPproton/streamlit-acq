# Native command verification

This note covers [the active filtering draft](acq_version.bbs) and [the cropping drafts](04_shortening_and_reorganizing.md). **Observed command examples do not establish a tested workflow.** All five scripts contain unresolved placeholders and have not been run in AcqKnowledge.

## Evidence from supplied examples

The source examples are in `/Users/dashelruizperez/Documents/Programming/PDX-Psy/acq_files`. This retains the earlier review's command references; cleanup of this folder does not newly validate native behavior.

Paths in the last column are relative to the supplied `acq_files` folder.

| Commands or pattern | Purpose in our draft | Source example |
| --- | --- | --- |
| `Lessons`, `OnOpenFile`, `End`; `if`, `endif`, `Halt`, `Prompt` | Script structure and stopping conditions | `ECG/Classify.bbs` |
| `GetTopGraph`, `GetStringLength`, `Select Window` | Find and select the open recording | `ECG/Classify.bbs`, lines 10–19 |
| `Get Channel Enable C, A`; `Set Channel C, On` | Check channel slots and show a waveform | `script-011-show-all-channels/011 - show all channels.bbs`, lines 12–15 |
| `Select Wave C`; `Edit Remove` | Select and delete one waveform | `ECG/Classify.bbs`, lines 49–50; `027 - Delete.bbs` |
| `GetNumber` | Request one numeric input | `ECG/Analyze.bbs`, line 16; our prompt and punctuation are adaptations |
| `Edit Duplicate D`; `Select Wave D`; `Edit SelectAll` | Create and select a full-waveform copy | `ECG/Classify.bbs`, lines 33–38; Script 015, lines 48–49 and 80–82 |
| `Set Channel D, Label, "..."` | Rename a result channel | `script-015-average-all-waveforms/015 - average all waveforms.bbs`, line 51 |
| `Get Marker Count`; `Get Marker Time` | Read marker count and time | `copymarkers.bbs`, lines 67–88 |
| `Get MaxLength`; `Get SampleTime`; `length * interval / 1000` | Calculate graph duration in seconds | `Compute HRVStats/056 - Compute HRV Stats.bbs`, lines 375–378 |
| `ROUND(...)` | Reject fractional task choices and marker IDs | Function used in `ECG/Classify.bbs`, line 155; validation use is our adaptation |
| `Save "", r`; success when `r = 1` | Request a destination and check the save result | `copymarkers.bbs`, lines 176–195 |
| `Set HCursor a, b`; `Set MMTUnits Time, 5` | Select a time range in seconds | `script-007-mark-selection/007 - mark selection.bbs`, lines 35 and 67 |
| `DeleteMarker m` | Delete a selected event-marker ID | `ECG/Clear.bbs`, lines 35–40 |

## Intended channel sequence

The user reported that raw ZM/CS remain displayed as 3/4 after initial cleanup and that ZM's new FIR, comb and RMS outputs use 1, 2 and 5. Display numbers are not yet verified as BIOPAC Basic channel IDs.

| After this stage | Intended retained displayed channels |
| --- | --- |
| Initial cleanup | 3 = raw ZM; 4 = raw CS |
| ZM processing and cleanup | 4 = raw CS; 5 = ZM RMS |
| CS processing and cleanup | 3 = CS RMS; 5 = ZM RMS |
| Normalize CS, then ZM into new waves | 1 = CS %MVC; 2 = ZM %MVC; 3 = CS RMS; 5 = ZM RMS |

The CS/output allocation follows the inferred reuse of free channel numbers. The draft captures actual output IDs in variables. `M` and `N` are reserved for ZM and CS MVCs. Percentage conversion must create new waves and retain the RMS sources in mV.

## Remaining checks

| Area | What remains unresolved |
| --- | --- |
| FIR | Native command and arguments for 28–500 Hz, Blackman −61 dB and optimized coefficients. The window choice is established by the screenshot; `Blackman61` in the placeholder is not verified native syntax. |
| Comb | Native command and arguments for 60 Hz, Q=5 and all harmonics up to Nyquist. |
| RMS | Native command and arguments for Average over 1000 samples, RMS, without baseline removal. |
| Output channels | Confirm each transform creates a new waveform and returns its ID; confirm display-to-script ID mapping and channel allocation. |
| Initial cleanup | Confirm the 0–59 scan covers the file's channels and check deletion's effect on IDs and channel-associated markers. |
| Sampling | Confirm aligned ZM/CS samples and rates above 1000 Hz for the specified FIR cutoffs. Graph duration alone does not establish per-channel coverage. |
| Percentage and units | Verify Waveform Math destination, constant division and assigning `%` only to the new outputs. MVC examples must be replaced with participant values. |
| Cropping | Implement `ASSUMED_EditClearAll_AllChannels` for the selected time range and verify sample/time behavior. Copies are prepared manually before cropping. |
| Journal | Implement `ASSUMED_RemoveEventMarkerSummaryFromJournal` without deleting acquisition notes. |
| Markers | Confirm native marker-ID behavior and that the deletion loop removes every intended marker type. The active cropping drafts delete remaining markers after using their times. |
| Inputs and saving | Confirm prompt/cancellation behavior and native Save As behavior. Filtering's save operation is a placeholder; cropping uses the observed dialog form. Choose new filenames to retain source files. |

Filter coefficient, gain, timing and boundary equivalence are tested in the [comparison notebook](../Step_3/03_compare_one_channel.ipynb), separately from native scripting syntax. Its reference file must retain raw and intermediate waves.

## Official references

- [BIOPAC script library](https://www.biopac.com/scripts/)
- [Application Note 253](https://www.biopac.com/wp-content/uploads/app253.pdf)
- [AcqKnowledge 5 Software Guide](https://www.biopac.com/wp-content/uploads/AcqKnowledge-5-Software-Guide.pdf)

These links are retained references. Command evidence above comes from supplied local examples; no native syntax has been newly confirmed by this cleanup.
