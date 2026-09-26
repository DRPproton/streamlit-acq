# Keep original channels 3 and 4

Draft: `@@...@@` marks unresolved BIOPAC syntax; this template is not runnable yet.

```text
GetTopGraph Z$
GetStringLength Z$, z

if z = 0
    Prompt "Open a recording first.", "OK"
    Halt
endif

@@VERIFY_ORIGINAL_CHANNELS_3_AND_4_EXIST_OR_HALT@@

Select Wave 3
@@SET_SELECTED_WAVE_VISIBLE_TRUE@@

Select Wave 4
@@SET_SELECTED_WAVE_VISIBLE_TRUE@@

; Insert Select Wave <channel ID> followed by Edit Remove for each unwanted channel.
@@INSERT_DELETIONS_FOR_ACTUAL_CHANNEL_IDS_EXCEPT_3_AND_4@@

@@VERIFY_ONLY_THE_TWO_ORIGINAL_CHANNELS_REMAIN_VISIBLE_OR_HALT@@

Prompt "Only the two raw channels remain, both visible.", "OK"
End
```

`Edit Remove` removes the selected waveform (confirmed by your BIOPAC example).
If the original channel IDs are exactly **0–6**, use this deletion block:

```basic
Select Wave 6
Edit Remove

Select Wave 5
Edit Remove

Select Wave 2
Edit Remove

Select Wave 1
Edit Remove

Select Wave 0
Edit Remove
```

- [BIOPAC scripting examples — 011: Show all channels; 027: Delete selected channel](https://www.biopac.com/scripts/)
- [BIOPAC Basic Scripting tutorial](https://www.biopac.com/wp-content/uploads/app253.pdf)
- [AcqKnowledge Software Guide](https://www.biopac.com/wp-content/uploads/AcqKnowledge-5-Software-Guide.pdf)
