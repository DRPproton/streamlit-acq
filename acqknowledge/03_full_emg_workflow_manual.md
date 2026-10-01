# Manual for the AcqKnowledge script code

Companion to [03_full_emg_workflow_draft.bbs](03_full_emg_workflow_draft.bbs). This document explains its **syntax, variables, arguments, and control flow**. Each code example is taken from that file; the examples share state and are not independent scripts.

**Status:** `ASSUMED_` commands are invented placeholders. The other command patterns are adapted from supplied BIOPAC examples, but the full script has not been executed in AcqKnowledge. No placeholder should be mistaken for a documented API.

## Script wrapper and comments

The supplied `.bbs` examples use this opening wrapper and finish with `End`. Lines beginning with `;` are explanatory comments and do not perform an operation. Indentation makes nested blocks easier to read; the examples use `if` and `endif` to mark their boundaries.

```text
Lessons
OnOpenFile
```

## Variable reference

| Variable | Value stored |
| --- | --- |
| `F` | Recording selector: APP=1, PsychoPy=2, SlowRate=3 |
| `G$`, `H$` | Full-graph and copied-graph window names |
| `C`, `D` | Raw ZM and raw CS channel IDs |
| `M`, `N` | Participant baseline MVCs for ZM and CS |
| `R`, `S` | ZM RMS and ZM %MVC channel IDs |
| `T`, `U` | CS RMS and CS %MVC channel IDs |
| `V`, `W` | Original video-cue and task-star times, in seconds |
| `L` | Graph length; overwritten with duration in seconds after conversion |
| `I` | Base sample interval in milliseconds |
| `A`, `B` | Temporary numeric results, reused for different commands |
| `K@`, `J@` | ZM and CS unit text |
| `X$`, `Y$`, `Z$` | Channel reference, MVC text, and complete expression text |

Channel-ID variables are numeric references to waveforms, not arrays of samples. The script asks AcqKnowledge to transform selected waveforms rather than loading NumPy-like arrays.

## Variables and numeric validation

`F = 1` assigns a numeric value. `if` evaluates a condition, and `endif` closes that block. `<` and `>` compare values; `<>` means “not equal.” `ROUND(F)` produces an integer-valued result, so comparing `F` with it rejects fractional input. `Halt` stops execution.

Here, `F` is the selector used later: 1 for APP, 2 for PsychoPy, 3 for SlowRate.

```text
F = 1
if F < 1
    Halt
endif
if F > 3
    Halt
endif
if F <> ROUND(F)
    Halt
endif
```

## Graph selection and channel availability

`GetTopGraph G$` places the active graph name in the text variable `G$`. `GetStringLength G$, A` puts the number of characters in numeric variable `A`. A length of zero triggers `Prompt`, followed by `Halt`. `Select Window G$` selects that graph.

`Get Channel Enable 3, A` queries channel ID 3 and stores its availability result in `A`; the same query uses `B` for channel 4. These are output variables, not additional channel IDs. The supplied show-all-channels example uses this query before setting visibility.

```text
GetTopGraph G$
GetStringLength G$, A
if A = 0
    Prompt "Open one raw recording.", "OK"
    Halt
endif
Select Window G$

Get Channel Enable 3, A
Get Channel Enable 4, B
if A < 1
    Prompt "Original channel 3 is missing.", "OK"
    Halt
endif
if B < 1
    Prompt "Original channel 4 is missing.", "OK"
    Halt
endif
```

## Numeric prompts and marker access

`Get Marker Count B` writes the marker count into `B`. `GetNumber` takes prompt text, a displayed unit or field description, and a numeric result variable. `A = 0` initializes that result before asking for input. The following conditions check its range and integer value.

`Get Marker Time A, V` reads marker ID `A` and writes its original time in seconds to `V`. The second prompt writes its time to `W`. `if F = 1` makes the first prompt APP-only. IDs follow the native examples’ 1-based search convention; they are not Python list indices. These checks do not establish that the user selected the correct event or handle every dialog error.

```text
Get Marker Count B
if F = 1
    A = 0
    GetNumber "Video cue marker ID (not label or time)", "marker ID", A
    if A < 1
        Halt
    endif
    if A > B
        Halt
    endif
    if A <> ROUND(A)
        Halt
    endif
    Get Marker Time A, V
endif
A = 0
GetNumber "Task star marker ID (interview star for APP)", "marker ID", A
if A < 1
    Halt
endif
if A > B
    Halt
endif
if A <> ROUND(A)
    Halt
endif
Get Marker Time A, W
```

## Arithmetic and nested conditions

`Get MaxLength L` and `Get SampleTime I` obtain the values used by BIOPAC Script 056 to calculate graph duration. `L = L*I/1000` replaces `L` with duration in seconds; `I` is the base interval in milliseconds. `*` multiplies and `/` divides.

Conditions can be nested: the checks involving `V` run only inside `if F = 1`. `V+120 > L` asks whether the requested interval extends past the graph’s end. This is a graph-level check, not a per-channel alignment check.

```text
Get MaxLength L
Get SampleTime I
L = L*I/1000
if W < 0
    Halt
endif
if W >= L
    Halt
endif
if F = 1
    if V < 0
        Halt
    endif
    if V+120 > L
        Prompt "Less than 120 seconds remain after the video cue.", "OK"
        Halt
    endif
endif
```

## Channel visibility and a cleanup placeholder

`Set Channel 3, On` makes channel 3 visible; `On` does not toggle its current state. The next statement does the same for channel 4.

`ASSUMED_KeepOnlyOriginalChannels` is not a real command. Its arguments describe the desired retained IDs and preservation requirement. `PreserveEvents` is also an invented descriptive argument. The native `Edit Remove` command deletes a selected waveform, but a verified sequence that preserves identities and events is still needed.

```text
Set Channel 3, On
Set Channel 4, On
ASSUMED_KeepOnlyOriginalChannels 3, 4, PreserveEvents
```

## Channel-selection dialogs

`ChooseChannel "Select raw ZM" C` presents a channel chooser and stores its result in `C`. The supplied example treats a negative result as cancellation. The second chooser stores its result in `D`.

`if C = D` compares the two results and stops when both choices identify the same channel. In later code, `C` identifies raw ZM and `D` identifies raw CS; their numbers are not hard-coded.

```text
ChooseChannel "Select raw ZM" C
if C < 0
    Halt
endif
ChooseChannel "Select raw CS" D
if D < 0
    Halt
endif
if C = D
    Prompt "Choose two different raw channels.", "OK"
    Halt
endif
```

## Channel units and two-number input

`Get Channel Units C, K@` reads the unit text for channel `C` into `K@`. `J@` receives the units for `D`. The imported examples use both `$` and `@` suffixed names for text variables.

`GetTwoNumbers` receives the prompt followed by two unit-label/result pairs: `K@, M` and `J@, N`. Consequently `M` receives ZM MVC and `N` receives CS MVC. Both are initialized to zero and checked for positive values. Reading the unit label does not convert the entered value into that unit.

```text
Get Channel Units C, K@
Get Channel Units D, J@
M = 0
N = 0
GetTwoNumbers "Participant MVC values: ZM then CS", K@, M, J@, N
if M <= 0
    Halt
endif
if N <= 0
    Halt
endif
```

## Selecting, duplicating, and labeling a waveform

`Select Wave C` selects the source waveform. `Edit SelectAll` selects its full range. `Edit Duplicate R` creates a copy and returns its channel ID in `R`. `Select Wave R` makes the destination explicit; the next `Edit SelectAll` ensures its full range is selected.

The three `ASSUMED_Transform...` statements are specifications, not callable BIOPAC commands. The draft assumes they modify `R` in place. If native transforms create new channels, their IDs must be captured instead.

`Set Channel R, Label, "ZM RMS"` changes the channel label. It does not change amplitude values or units.

```text
Select Wave C
Edit SelectAll
Edit Duplicate R
Select Wave R
Edit SelectAll
ASSUMED_TransformFilter BandPass, 28, 500, VerifyCoefficientSettings
ASSUMED_TransformCombBandStop 60, 5, VerifyHarmonicSettings
ASSUMED_TransformRMS 1000
Set Channel R, Label, "ZM RMS"
```

## Building and applying a waveform expression

`Edit Duplicate S` creates the normalized destination while retaining RMS in `R`. `EmbedString X$, "CH%1", LTRIM$(STR$(R,0))` builds a channel reference: if `R` were 6, the intended text is `CH6`. `%1` marks the substitution position, `STR$` converts the number to text, and `LTRIM$` removes leading spaces. This pattern appears in BIOPAC Script 015.

`Y$` holds the MVC as text. The `+` operators in the assignment to `Z$` concatenate strings. With illustrative values `R = 6` and `M = 0.10`, the resulting expression is conceptually `(CH6)*100/(0.10)`. `Transform Expression Z$` evaluates it over the selected destination range.

`STR$(M,15)` precision and decimal-format behavior remain unverified. The units operation is also a placeholder. The calculation is `100 × RMS / MVC`; changing the channel label alone would not perform this calculation.

```text
Edit SelectAll
Edit Duplicate S
Select Wave S
Edit SelectAll
EmbedString X$, "CH%1", LTRIM$(STR$(R,0))
Y$ = LTRIM$(STR$(M,15))
Z$ = "(" + X$ + ")*100/(" + Y$ + ")"
Transform Expression Z$
Set Channel S, Label, "ZM percent MVC"
ASSUMED_SetChannelUnits S, "%"
```

## Reusing the commands for a second source

This block repeats the same selection, duplication, and labeling commands with different IDs. `D` is the CS source and `T` is its RMS destination. These are separate variable values; selecting a channel does not automatically update all variables that refer to earlier channels.

The filter placeholders retain the same unresolved signatures and destination assumptions as the ZM block.

```text
Select Wave D
Edit SelectAll
Edit Duplicate T
Select Wave T
Edit SelectAll
ASSUMED_TransformFilter BandPass, 28, 500, VerifyCoefficientSettings
ASSUMED_TransformCombBandStop 60, 5, VerifyHarmonicSettings
ASSUMED_TransformRMS 1000
Set Channel T, Label, "CS RMS"
```

## Using a different denominator and destination

This expression reads CS RMS through `T`, uses CS MVC from `N`, and writes the normalized result into the selected duplicate `U`. The distinction between source reference and selected destination is essential: `CH...` inside `Z$` names the source; `Select Wave U` chooses the destination.

The units placeholder is intended to assign `%` after normalization.

```text
Edit SelectAll
Edit Duplicate U
Select Wave U
Edit SelectAll
EmbedString X$, "CH%1", LTRIM$(STR$(T,0))
Y$ = LTRIM$(STR$(N,15))
Z$ = "(" + X$ + ")*100/(" + Y$ + ")"
Transform Expression Z$
Set Channel U, Label, "CS percent MVC"
ASSUMED_SetChannelUnits U, "%"
```

## Passing channel IDs to a placeholder

`R`, `S`, `T`, and `U` are the four result IDs passed to this invented operation. Its required behavior is to retain those signals and relevant events. It does not establish their display order. A native implementation must account for any channel-ID changes during deletion.

```text
ASSUMED_KeepOnlyWaveforms R, S, T, U, PreserveEvents
```

## Save dialogs and return values

`Prompt` displays a message; it does not set a filename. In the supplied CopyMarkers example, `Save "", A` requests a save destination and places the result code in `A`. That example treats 1 as success. `if A <> 1` stops this draft for every other result.

The destination name is chosen in the dialog. Text such as “participant” in the prompt is not a variable substitution. These statements do not independently prevent choosing an existing source path. `GetTopGraph G$` then refreshes the saved full graph’s window name.

```text
Prompt "Save under a NEW participant task_filter.acq filename.", "OK"
Save "", A
if A <> 1
    Prompt "Save did not succeed. Workflow stopped.", "OK"
    Halt
endif

GetTopGraph G$
```

## Conditional branches and graph references

The outer `if F = 1` encloses both APP outputs. `G$` identifies the full graph. The invented `ASSUMED_DuplicateGraph H$` is intended to create an independent copy and return its window name in `H$`; `Select Window H$` selects that copy.

The crop placeholder receives start and end times in original seconds. For the first copy they are `V` and `V+120`; for the second they are `W` and `L`. Intended intervals include the start and exclude the end. `RebaseEvents` describes a requirement to move retained event times to the new origin; it is not a verified constant.

The second `Select Window G$` is necessary because the interview copy must come from the full graph, not the video crop. The journal placeholder concerns stale pasted summaries, not all acquisition notes. Nested `if A <> 1` blocks handle each save result.

```text
if F = 1
    Select Window G$
    ASSUMED_DuplicateGraph H$
    Select Window H$
    ASSUMED_KeepTimeRangeAllChannels V, V+120, RebaseEvents
    ASSUMED_RefreshPastedEventSummary
    Prompt "Save as NEW participant_1_video_filter_edit.acq.", "OK"
    Save "", A
    if A <> 1
        Prompt "Save did not succeed. Workflow stopped.", "OK"
        Halt
    endif

    Select Window G$
    ASSUMED_DuplicateGraph H$
    Select Window H$
    ASSUMED_KeepTimeRangeAllChannels W, L, RebaseEvents
    ASSUMED_RefreshPastedEventSummary
    Prompt "Save as NEW participant_2_interview_filter_edit.acq.", "OK"
    Save "", A
    if A <> 1
        Prompt "Save did not succeed. Workflow stopped.", "OK"
        Halt
    endif
endif
```

## An alternative branch

`if F > 1` selects the PsychoPy/SlowRate branch because earlier checks restrict `F` to 1, 2, or 3. It uses the same graph-copy, crop, journal, and save pattern. The crop arguments `W, L` mean the selected task star through the original graph end. The filename must still be supplied in the save dialog.

```text
if F > 1
    Select Window G$
    ASSUMED_DuplicateGraph H$
    Select Window H$
    ASSUMED_KeepTimeRangeAllChannels W, L, RebaseEvents
    ASSUMED_RefreshPastedEventSummary
    Prompt "Save as NEW participant task_filter_edit.acq.", "OK"
    Save "", A
    if A <> 1
        Prompt "Save did not succeed. Workflow stopped.", "OK"
        Halt
    endif
endif
```

## Selecting the final window and ending the script

`Select Window G$` returns focus to the full filtered graph. `End` closes the script. Neither command saves additional changes, closes graph windows, or opens the next file.

```text
Select Window G$
End
```

## Placeholder reference

| Placeholder | Intended action |
| --- | --- |
| `ASSUMED_KeepOnlyOriginalChannels` | Retain original raw 3/4 and preserve relevant events |
| `ASSUMED_TransformFilter` | Apply the specified FIR band-pass |
| `ASSUMED_TransformCombBandStop` | Apply the native comb filter using 60 Hz and Q=5 |
| `ASSUMED_TransformRMS` | Calculate RMS over 1,000 samples |
| `ASSUMED_SetChannelUnits` | Assign the displayed unit `%` to a normalized channel |
| `ASSUMED_KeepOnlyWaveforms` | Retain the four final signals and relevant events |
| `ASSUMED_DuplicateGraph` | Create an independent copy of the full graph and return its window name |
| `ASSUMED_KeepTimeRangeAllChannels` | Crop all channels together and rebase retained events |
| `ASSUMED_RefreshPastedEventSummary` | Remove or refresh stale summaries without deleting journal notes |

Arguments such as `PreserveEvents`, `RebaseEvents`, and `VerifyCoefficientSettings` are also descriptive placeholders, not verified native constants.

## Documentation and examples

[Command verification](command_verification.md) maps the observed command patterns to the supplied BIOPAC examples. The examples most relevant here are Script 011 (visibility), Script 015 (waveform expressions), ECG/Classify (duplication), CopyMarkers (markers and saving), and Script 056 (duration calculation).

Official references:

- [BIOPAC script library](https://www.biopac.com/scripts/)
- [Application Note 253](https://www.biopac.com/wp-content/uploads/app253.pdf)
- [AcqKnowledge 5 Software Guide](https://www.biopac.com/wp-content/uploads/AcqKnowledge-5-Software-Guide.pdf)

The online references returned HTTP 403 during the prior verification. This manual explains the existing source-based draft; it does not claim those inaccessible documents verify the unresolved commands.
