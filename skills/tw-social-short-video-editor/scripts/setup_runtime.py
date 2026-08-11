#!/usr/bin/env python3
"""Inspect or install an isolated FFmpeg + faster-whisper runtime."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import venv
from pathlib import Path

from runtime_paths import data_home, models_dir, runtime_dir, runtime_python, state_path


FASTER_WHISPER_VERSION = "1.2.1"
STATIC_FFMPEG_VERSION = "3.0"


def package_version(python, package):
    if not python.is_file():
        return None
    code = "import importlib.metadata as m; print(m.version(" + repr(package) + "))"
    result = subprocess.run([str(python), "-c", code], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def model_ready(model):
    path = models_dir() / model
    return path.is_dir() and (path / "model.bin").is_file()


def inspect(model="small"):
    python = runtime_python()
    system_ffmpeg = shutil.which("ffmpeg")
    system_ffprobe = shutil.which("ffprobe")
    state = {}
    try:
        state = json.loads(state_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    recorded_ffmpeg = state.get("ffmpeg")
    recorded_ffprobe = state.get("ffprobe")
    ffmpeg = system_ffmpeg or (recorded_ffmpeg if recorded_ffmpeg and Path(recorded_ffmpeg).is_file() else None)
    ffprobe = system_ffprobe or (recorded_ffprobe if recorded_ffprobe and Path(recorded_ffprobe).is_file() else None)
    whisper_version = package_version(python, "faster-whisper")
    return {
        "data_home": str(data_home()),
        "runtime_python": str(python),
        "isolated_runtime": python.is_file(),
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "ffmpeg_source": "system" if system_ffmpeg and system_ffprobe else ("isolated" if ffmpeg and ffprobe else None),
        "faster_whisper_version": whisper_version,
        "model": model,
        "model_path": str(models_dir() / model),
        "model_ready": model_ready(model),
        "ready": bool(ffmpeg and ffprobe and whisper_version and model_ready(model)),
    }


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def run_checked(command):
    subprocess.run(command, check=True)


def install(model):
    if sys.version_info < (3, 9):
        raise RuntimeError("faster-whisper requires Python 3.9 or newer")
    data_home().mkdir(parents=True, exist_ok=True)
    if not runtime_python().is_file():
        venv.EnvBuilder(with_pip=True, clear=False).create(runtime_dir())
    python = runtime_python()
    packages = [f"faster-whisper=={FASTER_WHISPER_VERSION}"]
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        packages.append(f"static-ffmpeg=={STATIC_FFMPEG_VERSION}")
    run_checked([str(python), "-m", "pip", "install", "--disable-pip-version-check", *packages])

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not (ffmpeg and ffprobe):
        resolver = (
            "from static_ffmpeg import run; import json; "
            "a,b=run.get_or_fetch_platform_executables_else_raise(); "
            "print(json.dumps([str(a),str(b)]))"
        )
        result = subprocess.run([str(python), "-c", resolver], check=True, capture_output=True, text=True)
        ffmpeg, ffprobe = json.loads(result.stdout.strip().splitlines()[-1])

    destination = models_dir() / model
    if not model_ready(model):
        destination.mkdir(parents=True, exist_ok=True)
        downloader = (
            "from faster_whisper.utils import download_model; "
            f"download_model({model!r}, output_dir={str(destination)!r})"
        )
        run_checked([str(python), "-c", downloader])

    payload = {
        "schema_version": 1,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ffmpeg": str(ffmpeg),
        "ffprobe": str(ffprobe),
        "faster_whisper_version": FASTER_WHISPER_VERSION,
        "model": model,
        "model_path": str(destination),
    }
    atomic_json(state_path(), payload)
    return inspect(model)


def main():
    parser = argparse.ArgumentParser(description="Check or create the Skill's isolated local media runtime")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Inspect without changing anything (default)")
    action.add_argument("--install", action="store_true", help="Create or repair the isolated runtime")
    parser.add_argument("--confirm-local-downloads", action="store_true", help="Confirm the combined local dependency and model download")
    parser.add_argument("--model", default="small")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.install:
        print(json.dumps(inspect(args.model), ensure_ascii=False, indent=2))
        return 0
    if not args.confirm_local_downloads:
        print(json.dumps({"error": "installation requires one combined confirmation via --confirm-local-downloads"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.dry_run:
        print(json.dumps({
            "will_create": str(runtime_dir()),
            "will_install": [f"faster-whisper=={FASTER_WHISPER_VERSION}", f"static-ffmpeg=={STATIC_FFMPEG_VERSION} when system FFmpeg is unavailable"],
            "will_download_model": args.model,
            "preserved_on_skill_update": str(data_home()),
        }, ensure_ascii=False, indent=2))
        return 0
    try:
        print(json.dumps(install(args.model), ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
