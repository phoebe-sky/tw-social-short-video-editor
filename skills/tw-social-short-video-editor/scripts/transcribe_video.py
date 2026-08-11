#!/usr/bin/env python3
"""Transcribe a media file with local faster-whisper first and consent-gated cloud fallback."""

import argparse
import hashlib
import importlib.util
import json
import mimetypes
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from runtime_paths import models_dir, resolve_media_binary, runtime_python


SCHEMA_VERSION = 1
MAX_CLOUD_BYTES = 24 * 1024 * 1024
OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"


def emit_error(message, code=2, **details):
    print(json.dumps({"error": message, **details}, ensure_ascii=False), file=sys.stderr)
    return code


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_cached(cache_dir, source_hash):
    if not cache_dir.exists():
        return None, None
    candidates = sorted(cache_dir.glob(f"{source_hash}.*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("schema_version") == SCHEMA_VERSION and payload.get("source", {}).get("sha256") == source_hash:
            return candidate, payload
    return None, None


def check_binary(name):
    return resolve_media_binary(name)


def maybe_relaunch_in_runtime(requested_provider):
    """Use the Skill's isolated Python without modifying the user's Python environment."""
    if requested_provider not in {"auto", "local"}:
        return
    if importlib.util.find_spec("faster_whisper") is not None:
        return
    python = runtime_python()
    if not python.is_file() or os.environ.get("TW_SHORT_VIDEO_RUNTIME_ACTIVE") == "1":
        return
    environment = os.environ.copy()
    environment["TW_SHORT_VIDEO_RUNTIME_ACTIVE"] = "1"
    os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], environment)


def probe_duration(ffprobe, source):
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def normalize_word(item, offset=0.0):
    text = str(item.get("word", item.get("text", ""))).strip()
    return {
        "start": round(float(item.get("start", 0.0)) + offset, 3),
        "end": round(float(item.get("end", item.get("start", 0.0))) + offset, 3),
        "text": text,
    }


def normalize_segment(item, offset=0.0):
    return {
        "start": round(float(item.get("start", 0.0)) + offset, 3),
        "end": round(float(item.get("end", item.get("start", 0.0))) + offset, 3),
        "text": str(item.get("text", "")).strip(),
    }


def transcribe_local(source, model_name, language, prompt, compute_type, allow_model_download):
    from faster_whisper import WhisperModel

    downloaded_model = models_dir() / model_name
    model_reference = str(downloaded_model) if (downloaded_model / "model.bin").is_file() else model_name

    model = WhisperModel(
        model_reference,
        device="auto",
        compute_type=compute_type,
        download_root=str(models_dir()),
        local_files_only=not allow_model_download,
    )
    segments_iter, info = model.transcribe(
        str(source),
        language=language or None,
        initial_prompt=prompt or None,
        vad_filter=True,
        word_timestamps=True,
    )
    segments, words = [], []
    for segment in segments_iter:
        segments.append({"start": round(segment.start, 3), "end": round(segment.end, 3), "text": segment.text.strip()})
        for word in segment.words or []:
            words.append({"start": round(word.start, 3), "end": round(word.end, 3), "text": word.word.strip()})
    return {
        "provider": "faster-whisper",
        "model": model_name,
        "language": getattr(info, "language", language),
        "language_probability": getattr(info, "language_probability", None),
        "segments": segments,
        "words": words,
        "text": "".join(segment["text"] for segment in segments),
    }


def multipart_body(fields, file_field, file_path):
    boundary = f"----tw-short-video-{uuid.uuid4().hex}"
    pieces = []
    for name, value in fields:
        pieces.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            str(value).encode("utf-8"),
            b"\r\n",
        ])
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    pieces.extend([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode(),
        f"Content-Type: {mime}\r\n\r\n".encode(),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    return boundary, b"".join(pieces)


def cloud_request(audio_path, api_key, model, language, prompt, timeout):
    fields = [("model", model), ("response_format", "verbose_json"), ("timestamp_granularities[]", "word")]
    if language:
        fields.append(("language", language))
    if prompt:
        fields.append(("prompt", prompt))
    boundary, body = multipart_body(fields, "file", audio_path)
    request = urllib.request.Request(
        OPENAI_TRANSCRIPTIONS_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"cloud transcription failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cloud transcription connection failed: {exc.reason}") from exc


def extract_cloud_chunks(source, ffmpeg, ffprobe, output_dir, chunk_seconds):
    duration = probe_duration(ffprobe, source)
    audio = output_dir / "audio.mp3"
    subprocess.run(
        [ffmpeg, "-v", "error", "-y", "-i", str(source), "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "48k", str(audio)],
        check=True,
    )
    if audio.stat().st_size <= MAX_CLOUD_BYTES:
        return [(0.0, audio)]
    audio.unlink()
    pattern = output_dir / "audio-%03d.mp3"
    subprocess.run(
        [
            ffmpeg, "-v", "error", "-y", "-i", str(source), "-map", "0:a:0", "-ac", "1", "-ar", "16000",
            "-c:a", "libmp3lame", "-b:a", "48k", "-f", "segment", "-segment_time", str(chunk_seconds),
            "-reset_timestamps", "1", str(pattern),
        ],
        check=True,
    )
    chunks = sorted(output_dir.glob("audio-*.mp3"))
    if not chunks or any(path.stat().st_size > MAX_CLOUD_BYTES for path in chunks):
        raise RuntimeError("unable to create cloud chunks below the 25 MB service limit")
    return [(index * float(chunk_seconds), path) for index, path in enumerate(chunks) if index * chunk_seconds < duration + chunk_seconds]


def transcribe_openai(source, ffmpeg, ffprobe, api_key, model, language, prompt, timeout, chunk_seconds):
    segments, words, texts = [], [], []
    with tempfile.TemporaryDirectory(prefix="tw-short-transcribe-") as temp_dir:
        for offset, chunk in extract_cloud_chunks(source, ffmpeg, ffprobe, Path(temp_dir), chunk_seconds):
            response = cloud_request(chunk, api_key, model, language, prompt, timeout)
            texts.append(str(response.get("text", "")).strip())
            words.extend(normalize_word(item, offset) for item in response.get("words", []))
            segments.extend(normalize_segment(item, offset) for item in response.get("segments", []))
    if not segments and words:
        segments = [{"start": words[0]["start"], "end": words[-1]["end"], "text": "".join(item["text"] for item in words)}]
    return {
        "provider": "openai",
        "model": model,
        "language": language,
        "segments": segments,
        "words": words,
        "text": "\n".join(text for text in texts if text),
    }


def choose_provider(requested, cloud_consent):
    local_available = importlib.util.find_spec("faster_whisper") is not None
    cloud_available = bool(os.environ.get("OPENAI_API_KEY")) and cloud_consent
    if requested == "local":
        if not local_available:
            raise RuntimeError("faster-whisper is not installed")
        return "local"
    if requested == "openai":
        if not cloud_consent:
            raise RuntimeError("cloud upload requires --cloud-consent for this source file")
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return "openai"
    if local_available:
        return "local"
    if cloud_available:
        return "openai"
    raise RuntimeError("no transcription provider available; install faster-whisper or configure OPENAI_API_KEY and pass --cloud-consent")


def main():
    parser = argparse.ArgumentParser(description="Transcribe media with hash cache, local-first routing, and consent-gated cloud fallback")
    parser.add_argument("source")
    parser.add_argument("--provider", choices=["auto", "local", "openai"], default="auto")
    parser.add_argument("--cache-dir")
    parser.add_argument("--output")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--prompt", default="繁體中文口播，保留原句、停頓、填充詞、專有名詞與英文產品名稱。")
    parser.add_argument("--local-model", default=os.environ.get("FASTER_WHISPER_MODEL", "small"))
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--allow-model-download", action="store_true", help="Allow faster-whisper to download the named model")
    parser.add_argument("--openai-model", default="whisper-1")
    parser.add_argument("--cloud-consent", action="store_true", help="Confirm file-specific consent for cloud upload")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--chunk-seconds", type=int, default=840)
    args = parser.parse_args()

    maybe_relaunch_in_runtime(args.provider)

    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        return emit_error("source file does not exist", source=source.name)
    cache_dir = Path(args.cache_dir).expanduser() if args.cache_dir else source.parent / "edit" / "transcripts"
    source_hash = sha256_file(source)
    if not args.force:
        cached_path, cached = load_cached(cache_dir, source_hash)
        if cached:
            if args.output:
                atomic_json(Path(args.output), cached)
            print(json.dumps({"cache_hit": True, "provider": cached.get("provider"), "path": str(cached_path)}, ensure_ascii=False))
            return 0

    try:
        ffprobe = check_binary("ffprobe")
        duration = probe_duration(ffprobe, source)
        provider = choose_provider(args.provider, args.cloud_consent)
        if provider == "local":
            try:
                result = transcribe_local(
                    source,
                    args.local_model,
                    args.language,
                    args.prompt,
                    args.compute_type,
                    args.allow_model_download,
                )
            except Exception as exc:
                if args.provider == "auto" and args.cloud_consent and os.environ.get("OPENAI_API_KEY"):
                    ffmpeg = check_binary("ffmpeg")
                    result = transcribe_openai(
                        source, ffmpeg, ffprobe, os.environ["OPENAI_API_KEY"], args.openai_model,
                        args.language, args.prompt, args.timeout, args.chunk_seconds,
                    )
                    result["fallback_reason"] = f"local provider failed: {type(exc).__name__}"
                else:
                    raise RuntimeError(f"local transcription failed: {exc}") from exc
        else:
            ffmpeg = check_binary("ffmpeg")
            result = transcribe_openai(
                source, ffmpeg, ffprobe, os.environ["OPENAI_API_KEY"], args.openai_model,
                args.language, args.prompt, args.timeout, args.chunk_seconds,
            )
    except (RuntimeError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        return emit_error(str(exc), code=3, source=source.name)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": {"name": source.name, "sha256": source_hash, "duration_s": round(duration, 3)},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **result,
    }
    safe_model = str(payload.get("model", "unknown")).replace("/", "-")
    cache_path = cache_dir / f"{source_hash}.{payload['provider']}.{safe_model}.json"
    atomic_json(cache_path, payload)
    if args.output:
        atomic_json(Path(args.output), payload)
    print(json.dumps({"cache_hit": False, "provider": payload["provider"], "path": str(cache_path), "words": len(payload.get("words", []))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
