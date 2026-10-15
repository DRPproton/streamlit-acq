# AcqKnowledge workflow

**Start here. All `.bbs` files are drafts with unresolved commands; none is a finished runnable workflow.** Python processing and comparison stay in the project notebooks.

## Active files

| File | Purpose |
| --- | --- |
| [acq_version.bbs](acq_version.bbs) | The filtering and rescaling draft to maintain in this folder. |
| [04_shortening_and_reorganizing.md](04_shortening_and_reorganizing.md) | Instructions for the four cropping scripts below. |
| [04_1Video_filter_edit.bbs](04_1Video_filter_edit.bbs) | Keep 120 seconds from the video cue. |
| [05_2Interview_filter_edit.bbs](05_2Interview_filter_edit.bbs) | Keep the interview Star through the end. |
| [06_3PsychoPy_filter_edit.bbs](06_3PsychoPy_filter_edit.bbs) | Keep the PsychoPy Star through the end. |
| [07_4SlowRate_filter_edit.bbs](07_4SlowRate_filter_edit.bbs) | Keep the SlowRate Star through the end. |
| [command_verification.md](command_verification.md) | Command evidence and remaining native-software checks. |

## Current task: validate one channel

Use the [comparison notebook](../Step_3/03_compare_one_channel.ipynb). In AcqKnowledge, work on a separate copy and retain **raw → FIR → comb → RMS** for the same ZM channel, with each transform applied to the preceding result. Do not crop or resample. FIR can be compared first, before creating the remaining results.

| Step | Settings supplied in the tutorial screenshots |
| --- | --- |
| FIR | 28–500 Hz; Blackman −61 dB; optimize coefficients for sample rate and cutoff. |
| Comb | 60 Hz line frequency; Q=5; all harmonics up to Nyquist. |
| RMS | Average over 1000 samples; Root mean square; Remove baseline unchecked. |

The filtering draft deletes raw/intermediate waves, and the cropping drafts remove data and markers. **Those drafts are not the procedure for preparing the comparison file.**

## Later: full native workflow

`acq_version.bbs` processes ZM first, then CS. It keeps each RMS result in mV, creates a separate percentage waveform using `RMS / (MVC / 100)`, and specifies saving four final channels to a new `_filter.acq` file in `filter_edit files`.

Replace its example MVC values with the participant's values in the same units as the signals. Confirm raw channel identities and native command syntax before use. After full-record filtering, follow the cropping guide; create the interview from a full-length Application copy, not the shortened video.

Superseded drafts are in [archive](archive/README.md). They are historical references, not additional workflow steps.
