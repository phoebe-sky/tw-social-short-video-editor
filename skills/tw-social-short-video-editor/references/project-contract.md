# Project and evidence contract

Keep generated files beside the protected source:

```text
edit/
├── project.md
├── transcripts/<source-hash>.json
├── corrected-transcript.md
├── story-plan.json
├── edl.json
├── master.srt
├── clips/
├── animations/<slot>/
├── qa/
├── preview.mp4
└── final.mp4
```

## Minimum EDL fields

Each retained range must contain:

```json
{
  "source": "source-id",
  "start": 12.32,
  "end": 16.06,
  "speed": 1.2,
  "beat": "problem",
  "quote": "verbatim retained words",
  "reason": "why this range is retained"
}
```

Store measured segment durations and output offsets after rendering. Store approved overlays and sound cues with output-timeline times.

## Subtitle timing

For a word inside a sped segment:

```text
output_time = measured_segment_offset + (word_start - source_segment_start) / speed
```

Clamp caption end times to the measured segment boundary. Apply captions after every other visual layer.

## QA evidence

Retain:

- source and final probe summaries;
- cut-boundary samples on both sides of every cut;
- first, representative middle, and final samples;
- safe-area results for captions and semantic overlays;
- black-frame and full-decode results;
- integrated loudness, loudness range, and true peak;
- observed A/V endpoint difference or another sync check;
- evidence-led correction count and unresolved issues.

Never substitute preview evidence for final-file QA.
