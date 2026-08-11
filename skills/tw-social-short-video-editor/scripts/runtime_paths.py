#!/usr/bin/env python3
"""Stable paths and dependency discovery for the Skill's isolated runtime."""

import json
import os
import shutil
import sys
from pathlib import Path


APP_NAME = "tw-social-short-video-editor"


def data_home():
    override = os.environ.get("TW_SHORT_VIDEO_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_NAME


def runtime_dir():
    return data_home() / "runtime"


def runtime_python():
    if sys.platform == "win32":
        return runtime_dir() / "Scripts" / "python.exe"
    return runtime_dir() / "bin" / "python"


def profiles_dir():
    return data_home() / "profiles"


def models_dir():
    return data_home() / "models"


def state_path():
    return data_home() / "runtime-state.json"


def read_state():
    try:
        return json.loads(state_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def resolve_media_binary(name):
    """Prefer an existing system binary, then the isolated runtime's recorded binary."""
    system_path = shutil.which(name)
    if system_path:
        return system_path
    candidate = read_state().get(name)
    if candidate and Path(candidate).is_file():
        return candidate
    raise RuntimeError(
        f"missing required executable: {name}; run setup_runtime.py --install --confirm-local-downloads"
    )
