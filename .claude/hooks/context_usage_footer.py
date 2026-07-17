#!/usr/bin/env python3
"""Stop hook: stamp a context/usage footer onto any 2-outputs report written this turn.

Claude Code invokes this at the end of every assistant turn (the Stop event), passing a
small JSON object on stdin that includes `transcript_path` and `cwd`. The script reads the
session transcript (and any subagent transcripts beside it), computes reliable per-turn
usage figures, and appends a delimited "Context and usage" footer to each
`2-outputs/**/*.md` file that was written during the just-finished turn — the report a
wiki skill (audit, lint, query, ingest, ...) just produced.

Design notes:
- Turn scoping. A footer is written only to files modified at/after this turn's start
  (the timestamp of the most recent genuine user prompt, distinguished from tool-result
  entries). This errs toward *missing* a footer, never toward stamping a stale/wrong
  number onto an older report.
- Dedup. Streaming writes the same assistant `message.id` to the transcript several times
  with monotonically growing `output_tokens`, so counts are deduped by id (max per id).
  Tool-use blocks are NOT duplicated across a message's streamed entries, so tools are
  counted across every entry.
- Reliability. Subagent transcripts do not record `output_tokens` faithfully (a long final
  answer can log as `output_tokens: 1`), so subagent output tokens are never reported; the
  subagent figure is peak-context footprint, which matches Claude Code's own
  `subagent_tokens` number.
- Fail-soft. Any error is swallowed and the hook exits 0 — telemetry must never disrupt a
  turn or block stopping.

The percentage denominator defaults to 200K; override with CLAUDE_CONTEXT_WINDOW_TOKENS if
the active model's window differs.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any

FOOTER_START = "<!-- context-usage-footer -->"
FOOTER_END = "<!-- /context-usage-footer -->"
DEFAULT_WINDOW = 200_000
# Preservation subfolders (nested under their owning skill: forget/quarantine/,
# supersede/preserve/). Their archived copies must stay byte-identical, so they
# never get a footer stamped. Matched on any path component, since they are no
# longer immediate children of 2-outputs/.
ARCHIVE_DIRS = {"quarantine", "preserve"}
# Files older than the turn are skipped; a small negative slack absorbs clock jitter.
MTIME_SLACK_S = 2.0


def _iso_to_epoch(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _is_user_prompt(obj: dict[str, Any]) -> bool:
    """A genuine user prompt (a turn boundary), not a tool_result echoed as a user entry."""
    if obj.get("type") != "user":
        return False
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return False
    content = msg.get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    return False


def _occupancy(usage: dict[str, Any]) -> int:
    return (
        (usage.get("input_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0)
        + (usage.get("cache_read_input_tokens") or 0)
    )


def _turn_start(entries: list[dict[str, Any]]) -> float | None:
    start: float | None = None
    for obj in entries:
        if _is_user_prompt(obj):
            ep = _iso_to_epoch(obj.get("timestamp"))
            if ep is not None:
                start = ep  # latest genuine prompt wins
    return start


def _metrics(entries: list[dict[str, Any]], since: float) -> dict[str, Any]:
    """Deduped per-turn usage for one transcript. `since` bounds to the current turn (0 = all)."""
    usage_by_id: dict[str, dict[str, Any]] = {}
    tools: dict[str, int] = {}
    end_occ = 0
    end_ts = -1.0
    peak_occ = 0
    model: str | None = None
    timestamps: list[float] = []

    for obj in entries:
        if obj.get("type") != "assistant":
            continue
        ots = _iso_to_epoch(obj.get("timestamp"))
        if ots is not None:
            if ots < since:
                continue
            timestamps.append(ots)
        msg = obj.get("message") or {}
        if not isinstance(msg, dict):
            continue
        model = msg.get("model") or model
        usage = msg.get("usage") or {}
        mid = msg.get("id")
        if isinstance(usage, dict):
            occ = _occupancy(usage)
            if occ > peak_occ:
                peak_occ = occ
            if ots is not None and ots >= end_ts:
                end_ts, end_occ = ots, occ
            if mid:
                prev = usage_by_id.get(mid)
                if prev is None or (usage.get("output_tokens") or 0) >= (prev.get("output_tokens") or 0):
                    usage_by_id[mid] = usage
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    name = block.get("name") or "?"
                    tools[name] = tools.get(name, 0) + 1

    unique = list(usage_by_id.values())
    web_search = sum((u.get("server_tool_use") or {}).get("web_search_requests", 0) or 0 for u in unique)
    web_fetch = sum((u.get("server_tool_use") or {}).get("web_fetch_requests", 0) or 0 for u in unique)
    duration = (max(timestamps) - min(timestamps)) if len(timestamps) >= 2 else 0.0
    return {
        "steps": len(usage_by_id),
        "output_tokens": sum((u.get("output_tokens") or 0) for u in unique),
        "tool_calls": sum(tools.values()),
        "tools": dict(sorted(tools.items(), key=lambda kv: (-kv[1], kv[0]))),
        "end_occupancy": end_occ,
        "peak_occupancy": peak_occ,
        "model": model,
        "web_search": web_search,
        "web_fetch": web_fetch,
        "duration_s": duration,
    }


def _subagent_dir(transcript_path: str) -> str:
    return os.path.join(os.path.splitext(transcript_path)[0], "subagents")


def _subagent_role(agent_path: str) -> str | None:
    meta = os.path.splitext(agent_path)[0] + ".meta.json"
    try:
        with open(meta, encoding="utf-8") as fh:
            return (json.load(fh) or {}).get("agentType")
    except (OSError, json.JSONDecodeError):
        return None


def _collect_subagents(transcript_path: str, since: float) -> list[dict[str, Any]]:
    subdir = _subagent_dir(transcript_path)
    if not os.path.isdir(subdir):
        return []
    agents: list[dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(subdir, "agent-*.jsonl"))):
        try:
            if os.path.getmtime(path) < since - MTIME_SLACK_S:
                continue
        except OSError:
            continue
        try:
            entries = _load_jsonl(path)
        except OSError:
            continue
        m = _metrics(entries, 0.0)
        agents.append({
            "role": _subagent_role(path) or "agent",
            "peak_occupancy": m["peak_occupancy"],
            "tool_calls": m["tool_calls"],
            "tools": m["tools"],
            "duration_s": m["duration_s"],
        })
    return agents


def _fmt_tools(tools: dict[str, int]) -> str:
    return ", ".join(f"{name}×{count}" for name, count in tools.items()) if tools else "none"


def _fmt_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m {seconds % 60:02d}s"


def _window() -> int:
    try:
        w = int(os.environ.get("CLAUDE_CONTEXT_WINDOW_TOKENS", ""))
        return w if w > 0 else DEFAULT_WINDOW
    except (ValueError, TypeError):
        return DEFAULT_WINDOW


def _build_footer(main: dict[str, Any], subagents: list[dict[str, Any]]) -> str:
    window = _window()
    end = main["end_occupancy"]
    pct = (end / window * 100) if window else 0.0
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    peak_note = f"; peak during run {main['peak_occupancy']:,}" if main["peak_occupancy"] != end else ""

    lines = [
        FOOTER_START,
        "## Context and usage (this run)",
        "",
        f"- Main context window at end of run: {end:,} tokens (~{pct:.0f}% of {window // 1000}K){peak_note}",
        f"- Main output generated: {main['output_tokens']:,} tokens across {main['steps']} steps",
        f"- Main tool calls: {main['tool_calls']} — {_fmt_tools(main['tools'])}",
        f"- Duration: {_fmt_duration(main['duration_s'])} on {main['model'] or 'unknown model'}",
        f"- Web tools: {main['web_search']} searches, {main['web_fetch']} fetches",
    ]

    if subagents:
        total_peak = sum(a["peak_occupancy"] for a in subagents)
        total_calls = sum(a["tool_calls"] for a in subagents)
        lines.append(
            f"- Subagents: {len(subagents)} agent(s), {total_peak:,} tokens summed peak-context "
            f"footprint, {total_calls} subagent tool calls"
        )
        for a in subagents:
            lines.append(
                f"    - {a['role']} — {a['peak_occupancy']:,} peak context, "
                f"{_fmt_duration(a['duration_s'])}, {a['tool_calls']} calls ({_fmt_tools(a['tools'])})"
            )
    else:
        lines.append("- Subagents: none this run")

    lines.append(
        f"- Recorded {stamp} by the context-usage Stop hook; subagent output tokens omitted as "
        "unreliable, footprint = peak context (matches Claude Code's own subagent figure)"
    )
    lines.append(FOOTER_END)
    return "\n".join(lines)


def _find_targets(outputs_dir: str, since: float) -> list[str]:
    cutoff = since - MTIME_SLACK_S if since else 0.0
    targets: list[str] = []
    for path in glob.glob(os.path.join(outputs_dir, "**", "*.md"), recursive=True):
        rel = os.path.relpath(path, outputs_dir)
        if any(part in ARCHIVE_DIRS for part in rel.split(os.sep)[:-1]):
            continue
        try:
            if os.path.getmtime(path) >= cutoff:
                targets.append(path)
        except OSError:
            continue
    return targets


_FOOTER_RE = re.compile(re.escape(FOOTER_START) + r".*?" + re.escape(FOOTER_END), re.DOTALL)


def _annotate(path: str, footer: str) -> None:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    text = _FOOTER_RE.sub("", text).rstrip()  # idempotent: replace any prior footer
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text + "\n\n" + footer + "\n")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0

    transcript = data.get("transcript_path")
    cwd = data.get("cwd") or os.getcwd()
    if not transcript or not os.path.isfile(transcript):
        return 0
    outputs_dir = os.path.join(cwd, "2-outputs")
    if not os.path.isdir(outputs_dir):
        return 0

    entries = _load_jsonl(transcript)
    since = _turn_start(entries) or 0.0
    targets = _find_targets(outputs_dir, since)
    if not targets:
        return 0

    main_metrics = _metrics(entries, since)
    if main_metrics["end_occupancy"] <= 0:
        return 0
    subagents = _collect_subagents(transcript, since)
    footer = _build_footer(main_metrics, subagents)

    for path in targets:
        try:
            _annotate(path, footer)
        except OSError:
            continue
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # never disrupt a turn on telemetry failure
        sys.exit(0)
