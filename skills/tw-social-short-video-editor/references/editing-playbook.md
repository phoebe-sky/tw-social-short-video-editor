# Editing playbook and `phoebe-v1` profile

## Narrative default

Use this shape when it fits the transcript:

1. strongest quote or tension in the first 3–7 seconds;
2. one brief reset into the original context;
3. audience problem;
4. creator question or insight;
5. test, process, or proof;
6. compact list or contrast;
7. human review or qualification;
8. payoff and natural invitation.

Move a later quote forward only when it remains truthful and understandable. Do not repeat the full quote later.

## Pacing and duration

- Use variable speed, not one global factor.
- For a 55–60 second information-dense talking-head short, begin with these ranges: hook 1.08–1.12×, context/problem 1.15–1.20×, explanation/process 1.20–1.25×, list 1.15–1.18×, conclusion/CTA 1.18–1.23×.
- Treat 1.25× as the default clarity ceiling. If the target is still infeasible, remove repetition or ask the user to choose a shorter story; do not silently exceed the ceiling.
- Keep important conclusions slower than dense explanation. Compress empty pauses without removing intentional reaction or breath.
- Remap captions, overlays, and SFX from measured output durations after speed changes.

## Traditional Chinese caption composition

- Follow spoken clauses, breath, punctuation, and grammar rather than a fixed character count.
- Keep subject–verb, modifier–noun, number–unit, and Latin tokens with their phrase. Keep units such as `透過 AI` together.
- Use at most two lines. Avoid a second line containing only one short token.
- Prefer balanced width, but never force a semantically incorrect line break.
- Align entries to word-level speech timing; do not accumulate theoretical segment durations.

## `phoebe-v1` visual profile

Use this optional profile to reproduce the style developed through nine review rounds:

- Canvas: 9:16 for IG Reels, YouTube Shorts, and Facebook Reels.
- Font: bundled Mantou Sans (`饅頭黑體`).
- General caption: white `#FFFFFF`, thin black `#202020` outline.
- Emphasis caption: cream apricot `#F3E5AD`, thin dark apricot-brown `#7B5842` outline.
- At 720p, begin near 70 px general / 76 px emphasis with about 2 px outlines. Scale proportionally at 1080p.
- Permit per-line horizontal compression only when the safe polygon requires it.
- Give emphasis a restrained 180–225 ms pop/settle animation. Do not animate every line.
- Allow one hook-to-story transition and straight cuts thereafter with selective reframing.

## Safe polygon

The bundled IG guide is 1081×1921. Normalized boundaries are:

- left `0.0472`, top `0.1187`, upper right `0.9519`;
- lower right `0.8446` after vertical notch `0.6403`;
- bottom `0.8001`.

At 720×1280, use approximately x=34–685 and y=152–1024; at y≥820, keep the right edge at x≤608. Treat the guide as QA-only and never burn it into the export.

## Effects and sound

- Use meaning-matched clusters: concentration lines for the hook, an idea spark for a solution, a calculation/HUD burst plus controlled shake for processing, light ticks for a list, and clipped pastel confetti plus a task-complete cue for payoff.
- Keep most clusters around 0.35–1.2 seconds and behind captions.
- For about 60 seconds, aim for roughly seven to nine cue timings rather than constant sound.
- Give the first seven seconds one low warning/impact cue and optionally one brighter reveal cue.
- Keep narration dominant. Target a final true peak at or below -1.5 dBTP unless the approved delivery standard says otherwise.
- Do not add unrelated fire, knife, romance, failure, big-head, or copyrighted catchphrase effects merely to increase activity.
