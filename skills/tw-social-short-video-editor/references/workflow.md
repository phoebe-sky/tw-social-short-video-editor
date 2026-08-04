# Vertical short workflow

## 1. Inspect and protect

- Work beside a protected source copy in an `edit/` directory.
- Hash the unchanged source and probe every stream.
- Detect HLG, HDR, BT.2020, rotation, variable frame rate, and missing audio before editing.
- Convert HLG/HDR to Rec.709 only when technically required; do not add an unapproved creative grade.

## 2. Transcribe with consent

- Ask before the first cloud upload of each source file.
- Name the provider and mention quota or cost.
- Require word-level start/end timestamps for precise cuts and caption sync.
- If a local fallback is chosen, label its timing confidence and inspect every edit boundary more closely.

## 3. Organize before cutting

Create a packed transcript and mark:

- strongest self-contained quote;
- false starts, filler, repeated ideas, and failed takes;
- story beats and likely target duration;
- ambiguous moments that need source playback.

Do not treat these observations as an approved EDL.

## 4. Approval gate

Resolve settings in this order: per-video brief, creator style profile, then skill defaults. Summarize what will be inherited, overridden, and proposed. Then propose the audience outcome, narrative order, kept material, pacing, duration, visual direction, caption style, and sound direction in 4–8 plain-language sentences. Wait for explicit approval.

## 5. Build the cut

- Snap cuts to word boundaries and retain 30–200 ms handles.
- Extract and process each retained segment independently.
- Apply about 30 ms audio fades at segment edges.
- Record source, start, end, beat, quote, reason, speed, and measured output offset.
- Keep picture/audio speed identical and preserve pitch.

## 6. Compose visuals and sound

- Apply only approved graphics and effects.
- Keep captions on top by rendering them last.
- Derive caption time from word timestamp, source segment start, speed, and measured output offset.
- Mix sound effects under narration and avoid stacking cues on consonant-heavy words.

## 7. Preview and QA

Render a complete 720×1280 preview. Inspect every cut in a ±1.5 s window, each caption/effect/sound cue, first/mid/last frames, subtitle safety, colour, loudness, true peak, black frames, and full audio/video decode. Make at most three evidence-led corrections.

## 8. Final approval and export

After explicit preview approval, rebuild one 1080×1920 final from the high-resolution source. Repeat boundary, sample, safe-area, colour, mix, stream, sync, and full-decode checks on the final itself. Deliver only the verified final.
