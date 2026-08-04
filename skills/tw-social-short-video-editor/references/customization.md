# Customization contract

## Resolve settings

Use three layers in this order:

1. per-video brief;
2. creator style profile;
3. skill defaults and the optional `phoebe-v1` profile.

A higher layer overrides only the fields it states. Treat blank fields, `沿用`, and `請依主題建議` respectively as inherit, inherit, and propose an evidence-based choice. Summarize the resolved settings before proposing the editing strategy. Ask only about a missing choice that materially changes the result.

## Adapt to content

- Permit font family, weight, colour, outline, shadow, scale, caption position, emphasis rules, animation, sticker style, effect family, sound family, cue density, music direction, pacing, and transition density to vary.
- Match choices to the transcript's meaning and the requested audience response. Do not mechanically use every permitted effect.
- Accept colours as plain-language names, HEX values, or reference images. When only a colour name is supplied, propose a readable shade plus a compatible outline or shadow before preview rendering; do not require the creator to know HEX.
- Treat reference videos as direction, not permission to copy protected graphics, music, stickers, or proprietary templates.
- Require uploaded fonts, logos, sounds, music, stickers, and effect assets to be usable for the requested distribution. Fall back to bundled or original assets when rights are unclear.
- If a named font is unavailable, report the substitution before preview rendering.

## Keep non-overridable guardrails

Never let a profile disable source protection, file-specific cloud-upload consent, truthful restructuring, word-aligned cut and caption timing, platform safe-area checks, narration intelligibility, preview approval, final-from-source rendering, or final-file QA.

## Save and reuse

Keep the completed creator profile outside the installed Skill so upgrades do not overwrite it. Give it a stable filename such as `my-video-style.md`. Copy and fill `assets/creator-style-profile-template.md` once, then copy `assets/video-brief-template.md` for each video. Never commit a student's private media, transcript, credentials, or private brand assets to a public repository.
