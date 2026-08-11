# Transcription and restructuring

## Route providers safely

Run `scripts/transcribe_video.py` before proposing any talking-head edit. The tool uses this order:

1. Return a valid transcript already cached by the source file SHA-256.
2. Use the isolated `faster-whisper` provider locally (or a compatible provider already available to the running Python).
3. Use OpenAI `whisper-1` only when `OPENAI_API_KEY` exists and the user gave file-specific cloud consent.
4. Stop when neither provider is available. Never claim to have read speech from frames or waveforms.

Cloud consent must name the source file, provider, and possible quota or cost. Pass `--cloud-consent` only after that confirmation. A cached transcript can be reused without requesting upload consent again because no upload occurs.

## Run transcription

Use automatic routing:

```bash
python scripts/transcribe_video.py input.mov \
  --provider auto \
  --language zh \
  --output edit/transcripts/source.json
```

Add `--cloud-consent` only after file-specific approval. Use `--provider local` to prohibit cloud fallback. The first-run flow prepares the local package and `small` model after one combined confirmation, and the transcription script automatically uses that isolated Python. The tool uses local files only by default; outside the first-run helper, pass `--allow-model-download` only after the user approves downloading the named model.

The cloud path extracts mono compressed audio, never the original video stream. OpenAI file transcription has a 25 MB input limit, so the tool keeps uploads below 24 MB and splits longer recordings when required. It requests word timestamps from `whisper-1` for edit boundaries.
The API key is sent only to the fixed official `https://api.openai.com/v1/audio/transcriptions` endpoint; the tool does not accept a custom API base.

## Cache and privacy

- Key transcripts by the full source SHA-256, provider, and model.
- Keep caches in the project `edit/transcripts/` directory.
- Store only the source basename in transcript JSON, never an absolute user path.
- Never commit transcripts, source media, API keys, `.env` files, or completed private creator profiles.
- Use `--force` only when the source or transcription settings require a deliberate refresh.

## Analyze content

After transcription, run:

```bash
python scripts/analyze_transcript.py edit/transcripts/source.json \
  --output edit/story-plan.json \
  --target-seconds 50 \
  --max-speed 1.15 \
  --keyword Skill \
  --keyword GitHub
```

The analyzer produces quote candidates, repeated-idea flags, filler or fragment flags, a source-duration budget, and a proposed hook-first edit order. Treat it as evidence and a first pass. Read the timed transcript yourself, confirm that the moved hook remains truthful, and play every proposed boundary before creating the EDL.

## Handle failure honestly

- If local transcription fails and cloud consent was not given, stop instead of uploading.
- If cloud transcription fails, retain the source and any valid cache; do not fabricate quotes.
- If timing data is missing, request a timed transcript or rerun a provider that returns word or segment timestamps.
- If deterministic analysis misclassifies a sentence, correct the story plan without changing the verbatim transcript.
