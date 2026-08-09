#!/usr/bin/env python3
"""Create a reviewable quote, repetition, and narrative-restructure plan from a timed transcript."""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path


FILLERS = {"嗯", "呃", "啊", "就是", "然後", "那個", "這個", "對", "好"}
HOOK_TERMS = {"不用", "不要", "為什麼", "怎麼", "每次", "真正", "其實", "根本", "只要", "最", "竟然", "問題", "重點"}
CTA_TERMS = {"留言", "私訊", "追蹤", "下載", "連結", "收藏", "分享", "試試看", "告訴我"}
PROCESS_TERMS = {"第一", "第二", "第三", "步驟", "接著", "再來", "打開", "點擊", "複製", "貼上", "安裝", "設定", "填寫"}
RESULT_TERMS = {"完成", "結果", "之後", "最後", "就可以", "省下", "不用再", "直接"}


def compact(text):
    return re.sub(r"[\s，。！？、；：,.!?;:\-—（）()\[\]【】『』「」]", "", text).lower()


def similarity(left, right):
    a, b = compact(left), compact(right)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def classify(text):
    if any(term in text for term in CTA_TERMS):
        return "cta"
    if any(term in text for term in PROCESS_TERMS):
        return "process"
    if any(term in text for term in RESULT_TERMS):
        return "payoff"
    if any(mark in text for mark in ("？", "?")) or any(term in text for term in HOOK_TERMS):
        return "hook"
    return "explanation"


def quote_score(segment, keywords):
    text = segment["text"]
    duration = max(0.01, segment["end"] - segment["start"])
    score = 0.0
    score += 2.5 if any(term in text for term in HOOK_TERMS) else 0.0
    score += 1.5 if "？" in text or "?" in text else 0.0
    score += 1.0 if any(char.isdigit() for char in text) else 0.0
    score += min(2.0, sum(1 for keyword in keywords if keyword and keyword in text) * 0.75)
    score += 1.5 if 2.0 <= duration <= 8.0 else 0.0
    score += 0.5 if 8 <= len(compact(text)) <= 42 else 0.0
    score -= 2.0 if compact(text) in FILLERS else 0.0
    score -= 1.0 if duration < 0.8 or not compact(text) else 0.0
    return round(score, 3)


def group_words(words, max_seconds=9.0):
    groups, current = [], []
    for word in words:
        item = {"start": float(word["start"]), "end": float(word["end"]), "text": str(word.get("text", word.get("word", ""))).strip()}
        if not item["text"]:
            continue
        if current and (item["start"] - current[-1]["end"] > 0.75 or item["end"] - current[0]["start"] > max_seconds):
            groups.append(current)
            current = []
        current.append(item)
        if re.search(r"[。！？!?]$", item["text"]):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return [
        {"start": group[0]["start"], "end": group[-1]["end"], "text": "".join(item["text"] for item in group)}
        for group in groups
    ]


def load_segments(payload):
    segments = []
    for item in payload.get("segments", []):
        text = str(item.get("text", "")).strip()
        if text:
            segments.append({"start": float(item["start"]), "end": float(item["end"]), "text": text})
    if not segments:
        segments = group_words(payload.get("words", []))
    if not segments and payload.get("text"):
        raise ValueError("transcript has text but no timing data; word or segment timestamps are required")
    if not segments:
        raise ValueError("transcript contains no timed speech")
    return segments


def mark_segments(segments, keywords, duplicate_threshold):
    marked = []
    for index, segment in enumerate(segments):
        duration = segment["end"] - segment["start"]
        text_key = compact(segment["text"])
        item = {
            "id": f"segment-{index + 1}",
            **segment,
            "duration_s": round(duration, 3),
            "role": classify(segment["text"]),
            "quote_score": quote_score(segment, keywords),
            "duplicate_of": None,
            "flags": [],
        }
        if text_key in FILLERS or (duration < 0.8 and len(text_key) <= 4):
            item["flags"].append("filler_or_fragment")
        for previous in marked:
            if len(text_key) >= 8 and similarity(item["text"], previous["text"]) >= duplicate_threshold:
                item["duplicate_of"] = previous["id"]
                item["flags"].append("repeated_idea")
                break
        marked.append(item)
    return marked


def select_edit(marked, target_seconds, max_speed):
    usable = [item for item in marked if not item["flags"] and item["duration_s"] > 0]
    if not usable:
        raise ValueError("no usable speech segments remain after analysis")
    hook = max(usable, key=lambda item: (item["quote_score"], -item["start"]))
    source_budget = target_seconds * max_speed
    selected = [hook]
    used = hook["duration_s"]
    roles = {hook["role"]}

    remaining = [item for item in usable if item["id"] != hook["id"]]
    for item in remaining:
        if used + item["duration_s"] <= source_budget:
            selected.append(item)
            used += item["duration_s"]
            roles.add(item["role"])

    for desired in ("process", "payoff", "cta"):
        if desired in roles:
            continue
        candidates = [item for item in remaining if item["role"] == desired and item not in selected]
        if not candidates:
            continue
        candidate = max(candidates, key=lambda item: item["quote_score"])
        replaceable = sorted([item for item in selected[1:] if item["role"] == "explanation"], key=lambda item: item["quote_score"])
        for old in replaceable:
            if used - old["duration_s"] + candidate["duration_s"] <= source_budget:
                selected.remove(old)
                selected.append(candidate)
                used = used - old["duration_s"] + candidate["duration_s"]
                roles.add(desired)
                break

    chronological = sorted([item for item in selected if item["id"] != hook["id"]], key=lambda item: item["start"])
    order = [hook] + chronological
    return hook, order, used


def main():
    parser = argparse.ArgumentParser(description="Find quote candidates, repeated material, and a reviewable short-video edit order")
    parser.add_argument("transcript")
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-seconds", type=float, default=50.0)
    parser.add_argument("--max-speed", type=float, default=1.15)
    parser.add_argument("--duplicate-threshold", type=float, default=0.72)
    parser.add_argument("--keyword", action="append", default=[])
    args = parser.parse_args()
    if args.target_seconds <= 0 or args.max_speed <= 0 or not 0.5 <= args.duplicate_threshold <= 1.0:
        parser.error("target, max speed, and duplicate threshold must be positive and valid")
    try:
        payload = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
        segments = load_segments(payload)
        marked = mark_segments(segments, args.keyword, args.duplicate_threshold)
        hook, order, source_seconds = select_edit(marked, args.target_seconds, args.max_speed)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    selected_ids = {item["id"] for item in order}
    decisions = []
    for item in marked:
        if item["id"] in selected_ids:
            reason = "strongest self-contained hook" if item["id"] == hook["id"] else f"retained {item['role']} beat within target budget"
            decision = "keep"
        elif "repeated_idea" in item["flags"]:
            reason, decision = f"repeats {item['duplicate_of']}", "drop"
        elif "filler_or_fragment" in item["flags"]:
            reason, decision = "filler or incomplete fragment", "drop"
        else:
            reason, decision = "outside target source-duration budget; review manually", "hold"
        decisions.append({**item, "decision": decision, "reason": reason})

    plan = {
        "schema_version": 1,
        "source": payload.get("source", {}),
        "target_seconds": args.target_seconds,
        "max_speed": args.max_speed,
        "source_budget_seconds": round(args.target_seconds * args.max_speed, 3),
        "selected_source_seconds": round(source_seconds, 3),
        "estimated_fastest_seconds": round(source_seconds / args.max_speed, 3),
        "hook": {"id": hook["id"], "start": hook["start"], "end": hook["end"], "text": hook["text"], "score": hook["quote_score"]},
        "edit_order": [
            {"position": index + 1, "id": item["id"], "source_start": item["start"], "source_end": item["end"], "role": item["role"], "text": item["text"]}
            for index, item in enumerate(order)
        ],
        "segments": decisions,
        "review_required": [
            "Confirm the selected hook remains truthful after moving it forward.",
            "Play every kept boundary before turning this plan into an EDL.",
            "Use semantic judgment to refine deterministic scores; never treat them as final approval.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "hook": hook["id"], "kept": len(order), "dropped": sum(item["decision"] == "drop" for item in decisions)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
