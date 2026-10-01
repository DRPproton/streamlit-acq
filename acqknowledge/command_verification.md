# AcqKnowledge script verification

Reviewed against the user-supplied BIOPAC `.bbs` examples in `/Users/dashelruizperez/Documents/Programming/PDX-Psy/acq_files` and the video transcript.

**Observed syntax is not the same as a tested script.** The full and one-channel drafts still contain `ASSUMED_` placeholders and cannot run as complete scripts. No AcqKnowledge runtime is available here.

## Which file to read

- [Full workflow](03_full_emg_workflow_draft.bbs): numbered comments cover one recording, both muscles, normalization, saving, and task cropping. Set `F` to 1 for APP, 2 for PsychoPy, or 3 for SlowRate.
- [One selected muscle](02_clean_one_selected_channel_draft.bbs): a shorter explanation of filtering and normalization after cleanup.
- [Initial cleanup](01_show_raw_channels_3_and_4.bbs): shows original channels 3/4 and deletes the others. This is a standalone experiment; it is not a prerequisite to the full draft.

## Commands supported by the supplied examples

Paths in the last column are relative to the supplied `acq_files` folder.

| Commands or pattern | Purpose in our draft | Source example |
| --- | --- | --- |
| `Lessons`, `OnOpenFile`, `End`; `if`, `endif`, `Halt`, `Prompt` | Script structure and stopping conditions | `ECG/Classify.bbs` |
| `GetTopGraph`, `GetStringLength`, `Select Window` | Find and select the open recording | `ECG/Classify.bbs`, lines 10–19 |
| `Get Channel Enable C, A`; `Set Channel C, On` | Check channel slots and show a waveform | `script-011-show-all-channels/011 - show all channels.bbs`, lines 12–15 |
| `Select Wave C`; `Edit Remove` | Select and delete one waveform | `ECG/Classify.bbs`, lines 49–50; `027 - Delete.bbs` |
| `ChooseChannel "..." C` | Ask the user to identify a muscle channel; negative result indicates cancellation | `copymarkers.bbs`, lines 40–49 |
| `Get ActiveChannel C` | Identify the currently selected channel | `ECG/Classify.bbs`, line 21 |
| `Get Channel Units C,U@`; `GetTwoNumbers` | Read source units and request numeric inputs | `ECG/RemoveEventsInRange.bbs`, lines 26–27 |
| `GetNumber` | Request one numeric input | `ECG/Analyze.bbs`, line 16; our prompt and punctuation are adaptations |
| `Edit Duplicate D`; `Select Wave D`; `Edit SelectAll` | Create and select a full-waveform copy | `ECG/Classify.bbs`, lines 33–38; Script 015, lines 48–49 and 80–82 |
| `Set Channel D, Label, "..."` | Rename a result channel | `script-015-average-all-waveforms/015 - average all waveforms.bbs`, line 51 |
| `EmbedString`, `LTRIM$`, `STR$`, `Transform Expression Z$` | Build and apply waveform math using a `CH` channel reference | Script 015, lines 66–82 |
| `Get Marker Count`; `Get Marker Time` | Read marker count and time | `copymarkers.bbs`, lines 67–88 |
| `Get MaxLength`; `Get SampleTime`; `length * interval / 1000` | Calculate graph duration in seconds | `Compute HRVStats/056 - Compute HRV Stats.bbs`, lines 375–378 |
| `ROUND(...)` | Reject fractional task choices and marker IDs | Function used in `ECG/Classify.bbs`, line 155; validation use is our adaptation |
| `Save "", r`; success when `r = 1` | Request a destination and check the save result | `copymarkers.bbs`, lines 176–195 |

## Details that remain unverified

- **Filters:** the video specifies FIR 28–500 Hz, comb 60 Hz with Q=5, and RMS over 1,000 samples. The imported filter example is a derivative filter, not this EMG workflow. `Blackman61` was removed from the EMG placeholders because that derivative example does not establish the correct EMG window.
- **Filter destinations:** the drafts assume each placeholder modifies the selected duplicate in place. The video creates new waveforms at each stage. A native implementation must explicitly handle its destination behavior and track the resulting channel IDs.
- **Channel removal:** individual deletion syntax is known. Channel renumbering and effects on channel-associated events still need verification. The initial cleanup loop must leave the two original raw signals; the full draft deliberately leaves preservation behavior inside a placeholder.
- **Sampling:** comments call for rates above 1,000 Hz and aligned raw channels. The draft does not yet perform native per-channel sampling-rate or alignment checks. Graph duration alone does not prove both channels cover every crop.
- **Numeric input:** examples demonstrate input commands, but the drafts do not comprehensively handle every cancellation, formatting, or error result. Marker IDs follow the native examples' 1-based search convention, not Python list indices.
- **MVC expression:** Script 015 supports constructing channel expressions. The new normalization expression and `STR$(MVC,15)` precision/decimal behavior have not been checked in the native interpreter.
- **Units:** the exact command to assign `%` units remains a placeholder. Changing a label is not the same as changing units.
- **Graph duplication and cropping:** exact signatures and event rebasing are unresolved. Every crop must start from the full filtered graph; do not crop the already shortened video to create the interview.
- **Journals:** remove or refresh only obsolete pasted event summaries, preserving acquisition notes. The placeholder for this action has no verified implementation.
- **Saving:** the observed form uses a dialog and reports status. Our prompts request new filenames, but the scripts do not independently enforce destination uniqueness or prevent the user choosing an original source path.

## Full-draft variables

| Variable | Meaning |
| --- | --- |
| `F` | Recording type: APP=1, PsychoPy=2, SlowRate=3 |
| `G$`, `H$` | Full-recording window name and cropped-copy window name |
| `C`, `D` | Selected raw ZM and raw CS channel IDs |
| `M`, `N` | Participant baseline MVCs for ZM and CS |
| `R`, `S` | ZM RMS and ZM %MVC channel IDs |
| `T`, `U` | CS RMS and CS %MVC channel IDs |
| `V`, `W` | Original video-cue and task-star times in seconds |
| `L`, `I` | Original duration in seconds after conversion, and base sample interval in milliseconds |
| `A`, `B` | Temporary values reused for checks, marker input/count, and save status |
| `K@`, `J@` | Source-unit strings for ZM and CS |
| `X$`, `Y$`, `Z$` | Channel-reference string, MVC-number string, and complete math expression |

## Official references

- [BIOPAC script library](https://www.biopac.com/scripts/)
- [Application Note 253](https://www.biopac.com/wp-content/uploads/app253.pdf)
- [AcqKnowledge 5 Software Guide](https://www.biopac.com/wp-content/uploads/AcqKnowledge-5-Software-Guide.pdf)

These web pages returned HTTP 403 during this review. Command evidence above comes from the supplied local BIOPAC examples; the inaccessible PDFs were not treated as newly verified evidence.
