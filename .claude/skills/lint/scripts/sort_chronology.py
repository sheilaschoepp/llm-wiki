#!/usr/bin/env python3
"""Deterministic auto-fix for the `chronology_missing_time` (recoverable case)
and `chronology_out_of_order` lint checks.

Re-sorts the two reverse-chronological files — `1-wiki/log.md` (every `## [date
time] …` entry, with its body) and `1-wiki/hot.md`'s Recent activity bullets —
into descending (date, time) order, newest first (CLAUDE.md → Hot, Index, And
Log). The sort key is the `[YYYY-MM-DD HH:MM]` header only; entry bodies move
with their header and no prose is changed, so the edit is determinate. The sort
is stable: entries sharing a (date, time) keep their original relative order.

Before sorting, recovers a missing `HH:MM` for any untimed entry from the entry's
own linked report filename (`2-outputs/…-YYYY-MM-DD-HHMM-…`) when that is
determinate — exactly one such link whose date matches the entry's date. This
transcribes a time already present in a linked artifact (the date cross-check
guards it); it never invents a time and never consults git (commit time is an
unreliable sort key). An untimed entry with no recoverable link still surfaces as
the `chronology_missing_time` finding: the file is skipped untouched (sorting on
an unknown key would misplace it) and that time must be added by hand first.

Idempotent: an already-sorted, fully-timed file is rewritten byte-identically.

    python3 .claude/skills/lint/scripts/sort_chronology.py [wiki-path]

`wiki-path` defaults to `1-wiki`. Exit code 0 on success (filled and/or sorted, or
already sorted), 1 if a file was skipped for an unrecoverable missing time, 2 on a
usage/path error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

LOG_HEADER_RE = re.compile(r'^## \[(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?\]')
HOT_ENTRY_RE = re.compile(r'^- \[(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?\]')

# A linked report carries the entry's time in its filename, `…-YYYY-MM-DD-HHMM-…`
# (e.g. query-2026-06-23-1045-…). A missing `[date]` time is recoverable from it
# — transcribed, not invented — when the link is determinate. (The check side,
# `check_chronology` in check_wiki.py, points its fix_hint here.)
REPORT_TIME_RE = re.compile(r'2-outputs/[^\s\]|)]*-(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2})')


def recover_time(entry_text: str, entry_date: str) -> str | None:
    """Recover an untimed entry's `HH:MM` from a linked report filename, or None if
    not determinate. Only a `2-outputs/…-YYYY-MM-DD-HHMM-…` link whose date equals
    `entry_date` counts, and exactly one distinct time must be found — zero,
    conflicting, or only date-mismatched links stay manual (None). Never invents a
    time and never consults git (commit time is an unreliable sort key)."""
    times = set()
    for m in REPORT_TIME_RE.finditer(entry_text):
        date, hh, mm = m.group(1), m.group(2), m.group(3)
        if date == entry_date and int(hh) < 24 and int(mm) < 60:
            times.add(f'{hh}:{mm}')
    return times.pop() if len(times) == 1 else None


def sort_log(path: Path) -> str:
    """Return the sorted text of log.md, or raise ValueError if an entry is
    untimed. Preamble (everything before the first dated header) is preserved."""
    lines = path.read_text(encoding='utf-8').split('\n')
    first = next((i for i, l in enumerate(lines) if LOG_HEADER_RE.match(l)), None)
    if first is None:
        return path.read_text(encoding='utf-8')  # nothing to sort
    preamble = lines[:first]
    while preamble and preamble[-1].strip() == '':
        preamble.pop()

    entries = []  # (date, time, header_line, body_lines)
    cur = None
    for ln in lines[first:]:
        m = LOG_HEADER_RE.match(ln)
        if m:
            if cur:
                entries.append(cur)
            cur = [m.group(1), m.group(2), ln, []]
        elif cur is not None:
            cur[3].append(ln)
    if cur:
        entries.append(cur)
    for e in entries:
        while e[3] and e[3][-1].strip() == '':
            e[3].pop()

    # Fill pass: recover a missing time from the entry's linked report filename
    # (determinate only), rewriting the header in place. Raise for any entry that
    # stays untimed — sorting on an unknown key would misplace it, so the file is
    # left untouched and the time must be added by hand first.
    for e in entries:
        if e[1] is None:
            t = recover_time('\n'.join([e[2]] + e[3]), e[0])
            if t is None:
                raise ValueError(f'untimed entry not auto-recoverable: {e[2][:60]}')
            e[1] = t
            e[2] = re.sub(r'^(## \[\d{4}-\d{2}-\d{2})\]', rf'\1 {t}]', e[2], count=1)

    # Stable sort: equal (date, time) keep original order even under reverse.
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)

    out = preamble + ['']
    for _, _, header, body in entries:
        out.append(header)
        out.extend(body)
        out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


def sort_hot(path: Path) -> str:
    """Return the text of hot.md with the Recent activity entries sorted newest-first,
    or raise ValueError if an entry is untimed. Mirrors sort_log so no content is
    dropped: a non-entry line before the first dated bullet (a placeholder, a parked
    note) stays as a preamble, and lines following a bullet (a sub-bullet, a wrapped
    continuation) move with it as its body. Every other section is preserved verbatim."""
    lines = path.read_text(encoding='utf-8').split('\n')
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == '## Recent activity')
    except StopIteration:
        return path.read_text(encoding='utf-8')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')),
               len(lines))
    block = lines[start + 1:end]

    first = next((i for i, l in enumerate(block) if HOT_ENTRY_RE.match(l)), None)
    if first is None:
        return path.read_text(encoding='utf-8')  # no dated entry (e.g. a placeholder) — nothing to sort
    preamble = block[:first]
    while preamble and preamble[0].strip() == '':
        preamble.pop(0)
    while preamble and preamble[-1].strip() == '':
        preamble.pop()

    entries = []  # (date, time, bullet_line, body_lines)
    cur = None
    for ln in block[first:]:
        m = HOT_ENTRY_RE.match(ln)
        if m:
            if cur:
                entries.append(cur)
            cur = [m.group(1), m.group(2), ln, []]
        elif cur is not None:
            cur[3].append(ln)
    if cur:
        entries.append(cur)
    for e in entries:
        while e[3] and e[3][-1].strip() == '':
            e[3].pop()

    # Fill pass: recover a missing time from the entry's linked report filename
    # (determinate only); an entry with no recoverable link stays a manual finding.
    for e in entries:
        if e[1] is None:
            t = recover_time('\n'.join([e[2]] + e[3]), e[0])
            if t is None:
                raise ValueError(
                    f'untimed Recent-activity entry not auto-recoverable: {e[2][:60]}')
            e[1] = t
            e[2] = re.sub(r'^(- \[\d{4}-\d{2}-\d{2})\]', rf'\1 {t}]', e[2], count=1)

    # Stable sort: equal (date, time) keep original order even under reverse.
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)

    new_block = ['']
    if preamble:
        new_block += preamble + ['']
    for _, _, bullet, body in entries:
        new_block.append(bullet)
        new_block.extend(body)
    new_block.append('')
    out = lines[:start + 1] + new_block + lines[end:]
    return '\n'.join(out).rstrip('\n') + '\n'


def main() -> int:
    wiki_root = Path(sys.argv[1] if len(sys.argv) > 1 else '1-wiki').resolve()
    if not wiki_root.exists():
        sys.stderr.write(f'path not found: {wiki_root}\n')
        return 2

    skipped = False
    for name, sorter in (('log.md', sort_log), ('hot.md', sort_hot)):
        path = wiki_root / name
        if not path.exists():
            continue
        before = path.read_text(encoding='utf-8')
        try:
            after = sorter(path=path)
        except ValueError as exc:
            sys.stderr.write(f'{name}: skipped — {exc}; add the time by hand, then re-run.\n')
            skipped = True
            continue
        if after != before:
            path.write_text(after, encoding='utf-8')
            print(f'{name}: re-sorted newest-first.')
        else:
            print(f'{name}: already sorted.')
    return 1 if skipped else 0


if __name__ == '__main__':
    sys.exit(main())
