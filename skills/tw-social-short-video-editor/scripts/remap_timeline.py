#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def offsets(durations):
    result, running = [], 0.0
    for duration in durations:
        result.append(running)
        running += duration
    return result


def main():
    parser = argparse.ArgumentParser(description="Remap output-timeline events after per-segment speed changes")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        old_durations = [float(value) for value in data["old_segment_durations"]]
        new_durations = [float(value) for value in data["new_segment_durations"]]
        speeds = [float(value) for value in data["speeds"]]
        if not old_durations or not (len(old_durations) == len(new_durations) == len(speeds)):
            raise ValueError("duration and speed arrays must have the same non-zero length")
        if any(value <= 0 for value in old_durations + new_durations + speeds):
            raise ValueError("durations and speeds must be positive")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    old_offsets = offsets(old_durations)
    new_offsets = offsets(new_durations)

    def remap(value):
        value = float(value)
        segment = len(old_durations) - 1
        for index, start in enumerate(old_offsets):
            if value < start + old_durations[index] - 1e-9:
                segment = index
                break
        return new_offsets[segment] + (value - old_offsets[segment]) / speeds[segment]

    events = [{**event, "time": round(remap(event["time"]), 6)} for event in data.get("events", [])]
    intervals = [{**interval, "start": round(remap(interval["start"]), 6), "end": round(remap(interval["end"]), 6)} for interval in data.get("intervals", [])]
    print(json.dumps({"new_segment_offsets": new_offsets, "new_total_duration": sum(new_durations), "events": events, "intervals": intervals}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
