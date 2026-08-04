---
name: tw-social-short-video-editor
description: Edit user-supplied talking-head footage into polished 9:16 Traditional Chinese social shorts for Instagram Reels, YouTube Shorts, and Facebook Reels. Use when Codex must inspect, transcribe, restructure, cut, vary speech speed, create semantic subtitles, apply a reusable style profile, check social safe areas, mix precise sound effects, render a preview, or export a verified vertical final.
---

# TW Social Short Video Editor

Turn a supplied talking-head video into a reviewable vertical short without altering the source. Keep creative decisions explicit, timing evidence-based, and the public skill free of personal media and secrets.

## Read the relevant resources

1. Read [workflow.md](references/workflow.md) for every edit.
2. Read [editing-playbook.md](references/editing-playbook.md) before proposing pacing, captions, effects, sound, or a style profile.
3. Read [project-contract.md](references/project-contract.md) before creating the EDL, preview, QA evidence, or final.

## Execute the workflow

1. Inspect every source with `ffprobe`; record duration, streams, dimensions, frame rate, colour metadata, and decode readability. Never overwrite, rename, move, or delete supplied media.
2. Obtain file-specific consent before uploading media to any transcription service. Mention the provider and possible cost or quota. Cache word-level verbatim timestamps by source hash. Never commit media, transcripts, API keys, `.env` files, or absolute personal paths.
3. Confirm the platforms, target duration, language, and style profile. Reuse answers already supplied in the thread. Use `phoebe-v1` only when requested or when the user supplied that profile.
4. Organize the transcript, identify the strongest quote and repeated or failed material, then propose a 4–8 sentence editing strategy. Wait for approval before choosing cuts, adding effects, changing speed, adding music or sound, or creating a CTA.
5. Build a word-aligned EDL with 30–200 ms edge handles. Prefer a strong cold open, one hook-to-story reset, and straight cuts thereafter. Keep the original meaning and never cut inside a word.
6. Plan variable speed by narrative role. Use `scripts/plan_variable_speed.py` when a target runtime is specified. Keep picture and source audio on the same factor, preserve pitch, and use measured rendered segment durations for every downstream offset.
7. Apply approved captions, effects, stickers, and sound. Break Traditional Chinese subtitles by semantic clause and breath, not character count. Apply captions last. Use `scripts/check_safe_zone.py` for every caption and semantic overlay.
8. Render and inspect a complete 720×1280 preview. Check every cut, caption entry, effect cue, sound cue, first/mid/last sample, colour, loudness, black frames, and full decode. Allow no more than three evidence-led self-fix passes.
9. Wait for explicit preview approval. Rebuild the formal 1080×1920 final from the protected high-resolution source rather than enlarging the preview. Inspect and fully decode the final file before delivery.

## Use the bundled tools

- Run `scripts/plan_variable_speed.py --input speed-plan.json` to solve a role-aware speed plan against a target duration.
- Run `scripts/remap_timeline.py --input timeline.json` to remap captions, effects, and sound cues after per-segment speed changes.
- Run `scripts/check_safe_zone.py --width 1080 --height 1920 --box name=x1,y1,x2,y2` to validate layout geometry.

Treat script output as planning or QA evidence, not as proof that a video was visually inspected.

## Protect portability

- Detect FFmpeg, `ffprobe`, fonts, and the transcription provider instead of hard-coding machine paths.
- Keep provider setup separate from creative editing. Stop and report missing dependencies; do not install or repair tools silently.
- Bundle only original or redistributable assets and retain their licences. Recreate proprietary effect categories with original assets; never claim they are the proprietary originals.
- Keep the core workflow style-neutral. Put reproducible visual choices in named profiles so another creator can replace them without rewriting safety and QA rules.

## Deliver honestly

Report the inspected source, consent state, transcript/cache state, approved strategy, preview and final paths, measured streams and duration, QA evidence, self-fix count, retained artifacts, and unresolved issues. Do not call a planned or unchecked file complete.
