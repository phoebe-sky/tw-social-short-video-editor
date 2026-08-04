#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROLE_RANGES = {
    "hook": (1.08, 1.12),
    "context": (1.15, 1.20),
    "problem": (1.15, 1.20),
    "explanation": (1.20, 1.25),
    "process": (1.20, 1.25),
    "list": (1.15, 1.18),
    "conclusion": (1.18, 1.23),
    "cta": (1.18, 1.23),
}


def load_plan(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    target = float(data["target_seconds"])
    segments = data["segments"]
    if target <= 0 or not segments:
        raise ValueError("positive target_seconds and at least one segment are required")
    normalized = []
    for index, segment in enumerate(segments):
        duration = float(segment["duration_s"])
        role = segment.get("role", "explanation")
        defaults = ROLE_RANGES.get(role, (1.0, 1.25))
        low = float(segment.get("min_speed", defaults[0]))
        high = float(segment.get("max_speed", defaults[1]))
        if duration <= 0 or low <= 0 or high < low:
            raise ValueError(f"invalid segment at index {index}")
        normalized.append({**segment, "id": segment.get("id", f"segment-{index + 1}"), "duration_s": duration, "role": role, "min_speed": low, "max_speed": high})
    return target, normalized


def runtime(segments, blend):
    return sum(segment["duration_s"] / (segment["min_speed"] + blend * (segment["max_speed"] - segment["min_speed"])) for segment in segments)


def solve(target, segments):
    slowest = runtime(segments, 0.0)
    fastest = runtime(segments, 1.0)
    if not fastest <= target <= slowest:
        return None, fastest, slowest
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if runtime(segments, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2, fastest, slowest


def main():
    parser = argparse.ArgumentParser(description="Plan variable segment speeds for a target runtime")
    parser.add_argument("--input", required=True, help="JSON plan containing target_seconds and segments")
    args = parser.parse_args()
    try:
        target, segments = load_plan(args.input)
        blend, fastest, slowest = solve(target, segments)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    if blend is None:
        print(json.dumps({"feasible": False, "target_seconds": target, "fastest_seconds": fastest, "slowest_seconds": slowest}, indent=2))
        return 1
    output = []
    for segment in segments:
        speed = segment["min_speed"] + blend * (segment["max_speed"] - segment["min_speed"])
        output.append({"id": segment["id"], "role": segment["role"], "source_duration_s": segment["duration_s"], "speed": round(speed, 4), "planned_duration_s": round(segment["duration_s"] / speed, 4)})
    print(json.dumps({"feasible": True, "target_seconds": target, "planned_seconds": round(sum(item["planned_duration_s"] for item in output), 4), "segments": output}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
