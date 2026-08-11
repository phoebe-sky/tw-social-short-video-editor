#!/usr/bin/env python3
"""Create and manage creator profiles outside the installed Skill directory."""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from runtime_paths import profiles_dir


def safe_name(value):
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError("profile name may contain only letters, numbers, dot, underscore, and hyphen")
    return value


def profile_path(name):
    return profiles_dir() / f"{safe_name(name)}.md"


def status(name):
    path = profile_path(name)
    return {"name": name, "path": str(path), "exists": path.is_file(), "external_to_skill": True}


def main():
    parser = argparse.ArgumentParser(description="Manage update-safe creator style profiles")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("status", "path", "show", "init"):
        child = subparsers.add_parser(command)
        child.add_argument("--name", default="default")
    save = subparsers.add_parser("save")
    save.add_argument("source")
    save.add_argument("--name", default="default")
    export = subparsers.add_parser("export")
    export.add_argument("destination")
    export.add_argument("--name", default="default")
    args = parser.parse_args()

    try:
        path = profile_path(args.name)
        if args.command == "status":
            print(json.dumps(status(args.name), ensure_ascii=False, indent=2))
        elif args.command == "path":
            print(path)
        elif args.command == "show":
            if not path.is_file():
                raise FileNotFoundError(f"creator profile not found: {path}")
            print(path.read_text(encoding="utf-8"))
        elif args.command == "init":
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                template = Path(__file__).resolve().parents[1] / "assets" / "creator-style-profile-template.md"
                shutil.copyfile(template, path)
            print(json.dumps(status(args.name), ensure_ascii=False, indent=2))
        elif args.command == "save":
            source = Path(args.source).expanduser().resolve()
            if not source.is_file():
                raise FileNotFoundError(f"completed profile not found: {source}")
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, path)
            print(json.dumps(status(args.name), ensure_ascii=False, indent=2))
        elif args.command == "export":
            if not path.is_file():
                raise FileNotFoundError(f"creator profile not found: {path}")
            destination = Path(args.destination).expanduser().resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            print(json.dumps({"exported": str(destination), **status(args.name)}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
