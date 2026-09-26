# AcqKnowledge scripts

## Required first cleanup step: retain original channels 3 and 4

The user opens the original recording in AcqKnowledge, then opens and runs
the cleanup script. Original channel numbers 3 and 4 are hidden raw channels.
The first cleanup operation must:

1. Verify both original channels exist before changing the graph.
2. Explicitly show channels 3 and 4 (not toggle their visibility).
3. Remove every other waveform from the working graph.
4. Leave exactly those two original waveforms visible, with their samples,
   sampling rates, units and time positions unchanged.

Use original channel identifiers, not third/fourth visible positions. The
native channel-number behavior after removal must be verified before coding
the deletion loop. Do not overwrite the source file.

This cleanup is not implemented yet: channel enumeration, visibility, and
removal command signatures have not been verified. BIOPAC lists Script 011
(Show all channels) and Script 027 (Delete selected channel) at
https://www.biopac.com/scripts/ but their downloads were inaccessible here.

The two scripts below are earlier isolated experiments, not the requested
cleanup pipeline. In particular, duplication is not the first cleanup step.

## Earlier experiment: Detect an open recording

`01_check_open_recording.bbs` checks whether AcqKnowledge has an active graph
and displays a message. It does not modify or save the recording.

The commands `GetTopGraph`, `GetStringLength`, `Prompt`, `Halt`, and the
`if`/`endif` structure appear in BIOPAC's AcqKnowledge 4 Software Guide,
Chapter 23, in its Script Editor example:
https://www.biopac.com/wp-content/uploads/acqknowledge-4-software-guide.pdf

This is native BIOPAC Basic code, not pseudocode. It has not been executed
in AcqKnowledge here; compatibility with the installed version remains to
be checked.

### Test in AcqKnowledge with scripting enabled

1. Open this `.bbs` file in the Script Editor.
2. Click **Check Syntax**, then **Run**.
3. With no recording open, expect a message asking you to open a recording.
4. Open a copy of a recording and run again. Expect the message
   "An active recording was found. Step 1 is complete."

If Check Syntax reports an error, retain its exact text and line number so
the script can be adjusted against the installed BIOPAC Basic Reference.

Filtering, MVC calculations, normalization, cropping, and saving will be
added in separate steps.

## Earlier experiment: Prepare a working copy of one channel

`02_prepare_selected_channel.bbs` includes the open-recording check, selects
all samples, duplicates the selected waveform, then selects the duplicate
and its full sample range. Run this script by itself; step 1 need not run first.

Open a copy of a recording and select the raw ZM or CS channel before running.
The script uses whichever channel is selected; it does not identify muscle
labels or validate that the channel is raw. Each run creates another duplicate.
It does not filter, remove channels, or save the recording.

The native commands `Edit Duplicate` (with output channel variable),
`Select Wave`, and `Edit SelectAll` are described in BIOPAC Application Note
253, steps 11-13:
https://www.biopac.com/wp-content/uploads/app253.pdf

Test with **Check Syntax**, then **Run**. Expect one additional channel with
the same samples as the source and with its full range selected. Native
execution has not been tested here.

The next processing operation is FIR band-pass at 28-500 Hz. Its exact native
command arguments still require the BIOPAC Basic Reference; no guessed filter
command is included in this script.
