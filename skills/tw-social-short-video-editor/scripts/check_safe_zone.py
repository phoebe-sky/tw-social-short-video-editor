#!/usr/bin/env python3
import argparse
import json
import sys


RATIOS = {
    "left": 51 / 1081,
    "top": 228 / 1921,
    "upper_right": 1029 / 1081,
    "lower_right": 913 / 1081,
    "notch": 1230 / 1921,
    "bottom": 1537 / 1921,
}


def parse_box(value: str):
    try:
        name, coords = value.split("=", 1)
        x1, y1, x2, y2 = (float(item) for item in coords.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use name=x1,y1,x2,y2") from exc
    if not name or x2 < x1 or y2 < y1:
        raise argparse.ArgumentTypeError("box name and ordered coordinates are required")
    return name, (x1, y1, x2, y2)


def limits(width: int, height: int):
    return {key: ratio * (width if key in {"left", "upper_right", "lower_right"} else height) for key, ratio in RATIOS.items()}


def check(box, safe):
    x1, y1, x2, y2 = box
    right = safe["lower_right"] if y2 >= safe["notch"] else safe["upper_right"]
    problems = []
    if x1 < safe["left"]:
        problems.append("left")
    if x2 > right:
        problems.append("right")
    if y1 < safe["top"]:
        problems.append("top")
    if y2 > safe["bottom"]:
        problems.append("bottom")
    return problems


def main():
    parser = argparse.ArgumentParser(description="Check boxes against the bundled IG safe polygon")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--box", action="append", type=parse_box, required=True, help="name=x1,y1,x2,y2")
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0:
        parser.error("width and height must be positive")
    safe = limits(args.width, args.height)
    results = []
    failed = False
    for name, box in args.box:
        problems = check(box, safe)
        failed |= bool(problems)
        results.append({"name": name, "box": box, "pass": not problems, "outside": problems})
    print(json.dumps({"width": args.width, "height": args.height, "safe": safe, "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
