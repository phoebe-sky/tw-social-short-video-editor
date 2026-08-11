# First-run onboarding

## Detect first use

Before inspecting media, run both read-only checks:

```bash
python scripts/manage_creator_profile.py status
python scripts/setup_runtime.py --check
```

Resolve `scripts/` relative to this Skill. Never make the learner search the installed Skill folder.

## Create the creator profile

When the default profile is absent, offer these routes in conversation:

1. guided setup: ask for the creator's usual font, emphasis colour, caption position, sound/effect direction, pacing, and platforms; use safe defaults for anything they do not know;
2. import: save a completed profile they uploaded;
3. defaults: initialize the bundled template, explain the current defaults, and continue.

Save the result with `manage_creator_profile.py save COMPLETED_FILE`, or initialize an update-safe copy with `manage_creator_profile.py init`. The stable path is outside the installed Skill. Tell the user they can later say 「顯示我的創作者設定」、「修改重點色」 or 「匯出創作者設定檔」; translate those requests into `show`, an edited `save`, or `export` operations.

Never let a profile turn off source protection, content truthfulness, file-specific cloud consent, safe-area checks, preview approval, or formal-file QA.

## Prepare local dependencies

If `setup_runtime.py --check` reports `ready: false`, summarize one combined action: an isolated Python runtime, `faster-whisper`, an FFmpeg/ffprobe fallback only if system copies are missing, and the `small` model will be downloaded to the external data directory. Mention that download size and time vary, no administrator access or modification of the user's existing Python is intended, and models/binaries come from their upstream package sources.

Ask for one confirmation for that combined action. After confirmation, run:

```bash
python scripts/setup_runtime.py --install --confirm-local-downloads --model small
```

Do not ask separate FFmpeg, Python-package, and model questions. Do not run the install flag before confirmation. If installation fails, preserve the original error, report the failed stage, and offer a specific repair; do not loop installs silently.

On later uses, reuse a ready runtime and existing profile without asking again.
