"""Check lint's Script-emitted catalogue against check_wiki.py's registry."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_START = '### Script-emitted'
SCRIPT_END = '### LLM-walk'
SEVERITY_HEADINGS = {
    'Critical': 'error',
    'Warning': 'warning',
    'Info': 'info',
}
CHECK_LINE = re.compile(r'^- `([^`]+)`(?: [^:]*)?:')


class CatalogueError(ValueError):
    """The registry or Markdown catalogue could not be read reliably."""

    def __init__(self, *, message: str) -> None:
        super().__init__(message)


def load_registry(script: Path) -> dict[str, str]:
    """Return the canonical check registry from check_wiki.py."""
    proc = subprocess.run(
        [sys.executable, str(script), '--list-checks'],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise CatalogueError(
            message=(
                f'{script} --list-checks exited {proc.returncode}: '
                f'{proc.stderr.strip() or "no stderr"}'
            )
        )
    if not proc.stdout.strip():
        raise CatalogueError(
            message=f'{script} --list-checks produced empty stdout'
        )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise CatalogueError(
            message=f'{script} --list-checks produced invalid JSON: {exc}'
        ) from exc
    if not isinstance(data, dict) or not data:
        raise CatalogueError(message='registry JSON must be a nonempty object')
    allowed = {'error', 'warning', 'info', 'caller-determined'}
    if any(not isinstance(k, str) or v not in allowed for k, v in data.items()):
        raise CatalogueError(
            message='registry contains an invalid ID or severity'
        )
    return dict(data)


def parse_catalogue(path: Path) -> dict[str, frozenset[str]]:
    """Parse IDs and heading-derived severities from Script-emitted only."""
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError as exc:
        raise CatalogueError(message=f'cannot read {path}: {exc}') from exc

    starts = [i for i, line in enumerate(lines) if line.startswith(SCRIPT_START)]
    ends = [i for i, line in enumerate(lines) if line.startswith(SCRIPT_END)]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise CatalogueError(
            message=(
                'catalogue needs exactly one ordered Script-emitted and '
                'LLM-walk section'
            )
        )

    current: str | None = None
    seen_headings: set[str] = set()
    found: dict[str, set[str]] = {}
    occurrences: dict[str, int] = {}
    for line in lines[starts[0] + 1 : ends[0]]:
        if line.startswith('#### '):
            name = line[5:].split(' ', 1)[0]
            current = SEVERITY_HEADINGS.get(name)
            if current is not None:
                seen_headings.add(current)
            continue
        match = CHECK_LINE.match(line)
        if not match:
            continue
        if current is None:
            raise CatalogueError(
                message=f'check bullet outside a severity subsection: {line}'
            )
        check_id = match.group(1)
        found.setdefault(check_id, set()).add(current)
        occurrences[check_id] = occurrences.get(check_id, 0) + 1

    if seen_headings != set(SEVERITY_HEADINGS.values()):
        raise CatalogueError(
            message='catalogue is missing a Script-emitted severity heading'
        )
    if not found:
        raise CatalogueError(
            message='Script-emitted catalogue contains no check bullets'
        )
    for check_id, count in occurrences.items():
        allowed = check_id == 'zero_source_page' and count == 2
        if count != 1 and not allowed:
            raise CatalogueError(
                message=f'duplicate Script-emitted check ID: {check_id}'
            )
    if found.get('zero_source_page') not in (None, {'error', 'warning'}):
        raise CatalogueError(
            message=(
                'zero_source_page must appear once under Critical and once '
                'under Warning'
            )
        )
    return {check_id: frozenset(levels) for check_id, levels in found.items()}


def compare(
    registry: dict[str, str],
    catalogue: dict[str, frozenset[str]],
) -> list[dict[str, Any]]:
    """Return deterministic missing, extra, and severity-drift findings."""
    findings: list[dict[str, Any]] = []
    for check_id in sorted(set(registry) | set(catalogue)):
        registered = registry.get(check_id)
        documented = catalogue.get(check_id)
        if registered is None:
            findings.append({'kind': 'extra', 'check_id': check_id})
            continue
        if documented is None:
            findings.append({'kind': 'missing', 'check_id': check_id})
            continue
        expected = (
            frozenset({'error', 'warning'})
            if registered == 'caller-determined'
            else frozenset({registered})
        )
        if documented != expected:
            findings.append(
                {
                    'kind': 'severity_drift',
                    'check_id': check_id,
                    'registry': registered,
                    'catalogue': sorted(documented),
                }
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run the parity check; return 0 clean, 1 drift, or 2 operational."""
    repo = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--check-wiki',
        type=Path,
        default=repo / '.claude/skills/multi-skill/scripts/check_wiki.py',
    )
    parser.add_argument(
        '--catalogue',
        type=Path,
        default=Path(__file__).resolve().parents[1] / 'references/checks.md',
    )
    args = parser.parse_args(argv)
    try:
        findings = compare(
            registry=load_registry(script=args.check_wiki),
            catalogue=parse_catalogue(path=args.catalogue),
        )
    except CatalogueError as exc:
        print(f'catalogue check failed: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(findings, indent=2, sort_keys=True))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
