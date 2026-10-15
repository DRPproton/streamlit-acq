# Shortening filtered AcqKnowledge recordings

Use one script for each of the four **filtered, full-length** input graphs:

| Open input graph | Script | Required new filename suffix |
| --- | --- | --- |
| Filtered Application recording | [04_1Video_filter_edit.bbs](04_1Video_filter_edit.bbs) | `_1Video_filter_edit.acq` |
| Separate full-length copy of the filtered Application recording | [05_2Interview_filter_edit.bbs](05_2Interview_filter_edit.bbs) | `_2Interview_filter_edit.acq` |
| Filtered PsychoPy recording | [06_3PsychoPy_filter_edit.bbs](06_3PsychoPy_filter_edit.bbs) | `_3PsychoPy_filter_edit.acq` |
| Filtered SlowRate recording | [07_4SlowRate_filter_edit.bbs](07_4SlowRate_filter_edit.bbs) | `_4SlowRate_filter_edit.acq` |

Make the separate Application copy **before** cropping either Application graph. Open all four filtered graphs and select the intended one as the top graph before running its script. The interview script must start from the full-length copy, never from the shortened video output. The Save As dialog is interactive: choose a **new** filename with the suffix shown above so the filtered input remains available.

For **each** input graph, paste the event log into the journal, inspect the journal for timing exceptions, scroll through the event marks and segment lengths, and correct any problems before running the corresponding script. This inspection requires a person; the scripts ask for `1` to confirm it is complete. When prompted, enter the numeric ID of the correct video-cue or task Star marker. The scripts validate the ID's range, but cannot verify its meaning from the marker label.

The video script reads the cue time before editing, clears everything from 0 to the cue across all channels, then clears from **120 seconds on the shortened graph** to its end. The other three scripts clear 0 to their selected Star marker and keep the remainder. All four then remove the pasted event-marker summary from the journal, delete the remaining event markers, and open a Save As dialog. Journal notes about acquisition or timing should remain.

## Review checks

Each script checks the graph duration after removing the leading section against the original duration minus the selected marker time. The video script also checks for a final duration of 120 seconds. These checks allow one base sample interval for selection-edge rounding; the other three scripts separately reject an empty result. They are checks on graph duration, not proof that every channel had identical coverage or that a marker was correctly identified.

After the journal operation, the script explicitly reselects its original graph before deleting markers. It checks that the remaining marker count is zero and reselects the graph again before Save As. An unexpected duration, remaining markers, or unsuccessful save stops the script. If a check stops after an edit, the graph in memory may already be shortened; start a retry from a fresh full-length filtered input.

The draft control flow was checked locally with modeled graph operations, covering crop boundaries, sample rounding, invalid inputs, cancellation, journal focus changes, and edit failures. This validates the draft's decisions under those modeled command behaviors; it does not verify native BIOPAC command syntax. Copying/opening inputs, pasting/reviewing the event log, identifying the intended marker, and choosing the new Save As filename remain manual steps.

## Native-command gaps

These are **drafts**. `ASSUMED_EditClearAll_AllChannels` must become the BIOPAC Basic command for **Edit > Clear all** on the time range selected by `Set HCursor`. It must remove that interval from **every channel**, shifting later samples to the new time origin. `ASSUMED_RemoveEventMarkerSummaryFromJournal` must delete only the pasted marker summary and retain other journal notes. The supplied scripts establish marker selection/deletion and the Save As dialog, but do not establish these two native command signatures or a command that produces/pastes the event log. Paste and review that log manually before running.

The marker-deletion loop uses `Get Marker Count` and `DeleteMarker` from supplied BIOPAC examples. Verify in AcqKnowledge that the count covers every event marker type that must be deleted. The scripts use the graph-duration calculation shown in BIOPAC Script 056 and select ranges with `Set HCursor`, as shown in Script 007 and the ECG examples. They have not been run in AcqKnowledge.

BIOPAC describes [Edit > Clear all](https://www.biopac.com/knowledge-base/extracting-data-segments-from-a-file/) as removing a selected interval from all channels. It does not establish the BIOPAC Basic spelling of that menu command.
