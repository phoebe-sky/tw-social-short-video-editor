# Local runtime contract

## Storage and update behavior

The setup helper creates an isolated virtual environment and stores the creator profiles, `small` model, and runtime state under a stable per-user data directory:

- Windows: `%LOCALAPPDATA%/tw-social-short-video-editor`
- macOS: `~/Library/Application Support/tw-social-short-video-editor`
- Linux: `$XDG_DATA_HOME/tw-social-short-video-editor` or `~/.local/share/tw-social-short-video-editor`
- override for managed or test environments: `TW_SHORT_VIDEO_HOME`

These locations are outside the installed Skill. Reinstalling or updating the GitHub Skill must replace only Skill instructions, references, assets, and scripts; it must not delete profiles, models, transcripts, or the isolated runtime.

## Dependency policy

- Prefer an already working system `ffmpeg` and `ffprobe`.
- If either is unavailable, install the pinned `static-ffmpeg` fallback inside the isolated environment and record its executable paths.
- Install pinned `faster-whisper` inside that same environment and download the `small` model to the external model directory.
- Never install packages into the user's global Python, change the system `PATH`, require administrator access, or bundle downloaded binaries and models in Git.
- `transcribe_video.py` may relaunch itself with the isolated Python; this does not replace or mutate the user's Python installation.

`setup_runtime.py --check` is read-only. `--install` requires the explicit combined flag `--confirm-local-downloads`. Cloud transcription remains a separate, file-specific consent decision and is never enabled by runtime setup.

## Updating the GitHub Skill

A standalone GitHub-installed Skill is a local copy; upstream commits do not automatically rewrite existing installations. To receive a new release, rerun the GitHub Skill installer or the product's update action. The external data directory remains intact, so normal Skill updates do not require recreating the creator profile or redownloading a ready model.
