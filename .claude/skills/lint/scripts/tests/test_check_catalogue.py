"""Regression tests for lint's executable catalogue parity gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import check_catalogue as cc  # noqa: E402


def write_registry(path: Path, data: dict[str, str], code: int = 0) -> None:
    path.write_text(
        'import json, sys\n'
        f'print(json.dumps({data!r}))\n'
        f'raise SystemExit({code})\n',
        encoding='utf-8',
    )


def write_catalogue(path: Path, warning: str = 'ordinary') -> None:
    path.write_text(
        '# Checks\n\n'
        '### Script-emitted (`check_wiki.py`)\n\n'
        '#### Critical (script `error`)\n\n'
        '- `critical`: text\n'
        '- `zero_source_page`: text\n\n'
        '#### Warning (script `warning`)\n\n'
        f'- `{warning}`: text\n'
        '- `zero_source_page`: text\n\n'
        '#### Info (script `info`)\n\n'
        '- `informational`: text\n\n'
        '### LLM-walk (Step 2; not script-emitted)\n',
        encoding='utf-8',
    )


def test_current_catalogue_matches_live_registry() -> None:
    repo = Path(__file__).resolve().parents[5]
    registry = repo / '.claude/skills/multi-skill/scripts/check_wiki.py'
    catalogue = repo / '.claude/skills/lint/references/checks.md'
    assert cc.compare(
        registry=cc.load_registry(script=registry),
        catalogue=cc.parse_catalogue(path=catalogue),
    ) == []


def test_missing_extra_and_severity_drift_are_reported(tmp_path: Path) -> None:
    registry_path = tmp_path / 'registry.py'
    catalogue_path = tmp_path / 'checks.md'
    write_registry(
        registry_path,
        {
            'critical': 'error',
            'ordinary': 'info',
            'missing': 'warning',
            'zero_source_page': 'caller-determined',
        },
    )
    write_catalogue(catalogue_path, warning='ordinary')
    findings = cc.compare(
        registry=cc.load_registry(script=registry_path),
        catalogue=cc.parse_catalogue(path=catalogue_path),
    )
    assert {item['kind'] for item in findings} == {
        'extra',
        'missing',
        'severity_drift',
    }


def test_duplicate_ordinary_id_is_parse_failure(tmp_path: Path) -> None:
    catalogue = tmp_path / 'checks.md'
    write_catalogue(catalogue)
    text = catalogue.read_text(encoding='utf-8')
    catalogue.write_text(
        text.replace('- `ordinary`: text', '- `ordinary`: text\n- `ordinary`: text'),
        encoding='utf-8',
    )
    try:
        cc.parse_catalogue(path=catalogue)
    except cc.CatalogueError:
        return
    raise AssertionError('expected duplicate ID to fail closed')


def test_failed_registry_invocation_is_operational_failure(tmp_path: Path) -> None:
    registry = tmp_path / 'registry.py'
    write_registry(registry, {'x': 'warning'}, code=3)
    try:
        cc.load_registry(script=registry)
    except cc.CatalogueError:
        return
    raise AssertionError('expected nonzero registry exit to fail closed')
