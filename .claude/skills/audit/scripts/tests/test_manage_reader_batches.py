from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'manage_reader_batches.py'
SPEC = importlib.util.spec_from_file_location('manage_reader_batches', SCRIPT)
batcher = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(batcher)


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _unit(identity: str, group: int, *, scope: str = 'ordinary') -> dict:
    manifest = [{
        'raw_path': f'0-raw/papers/raw-{group:03d}.pdf',
        'sha256': _digest(f'raw-{group}'),
    }]
    return {
        'unit_id': identity,
        'page_generation': _digest('page-' + identity),
        'raw_manifest': manifest,
        'verification_scope': scope,
        'quantified_population': (
            {
                'raw_paths': [item['raw_path'] for item in manifest],
                'members': [{
                    'member_id': f'source-{group}',
                    'raw_paths': [item['raw_path'] for item in manifest],
                }],
            }
            if scope == 'exhaustive_negative'
            else None
        ),
    }


def _input(*, bullets: list[dict] | None = None, pages: list[dict] | None = None) -> dict:
    return {
        'schema_version': 1,
        'run_id': 'audit-run',
        'relationship_epoch': 'READY(1)',
        'bullet_units': bullets or [],
        'page_units': pages or [],
    }


def test_94_pages_over_31_raw_groups_are_62_calls_and_188_rows() -> None:
    pages = [_unit(f'1-wiki/concepts/page-{i:03d}.md', i % 31) for i in range(94)]
    plan = batcher.build_plan(_input(pages=pages))
    assert plan['planned_calls'] == 62
    assert plan['planned_waves'] == 16
    assert plan['planned_page_records'] == 188
    assert sum(batch['size'] for batch in plan['batches']) == 188


def test_394_claims_over_42_raw_groups_are_84_calls() -> None:
    bullets = [_unit(_digest(f'claim-{i}'), i % 42) for i in range(394)]
    plan = batcher.build_plan(_input(bullets=bullets))
    assert plan['planned_calls'] == 84
    assert plan['planned_bullet_records'] == 788


def test_plan_is_deterministic_when_input_units_are_reordered() -> None:
    units = [_unit(_digest(f'claim-{i}'), i % 3) for i in range(11)]
    forward = batcher.build_plan(_input(bullets=units))
    reverse = batcher.build_plan(_input(bullets=list(reversed(units))))
    assert reverse == forward


def test_cli_returns_one_compact_receipt_not_full_units(tmp_path: Path) -> None:
    claim_id = _digest('private-full-claim')
    input_path = tmp_path / 'input.json'
    output_path = tmp_path / 'plan.json'
    input_path.write_text(json.dumps(_input(bullets=[_unit(claim_id, 1)])))
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), 'plan', str(input_path), str(output_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert len(proc.stdout.splitlines()) == 1
    receipt = json.loads(proc.stdout)
    assert set(receipt) == {
        'calls', 'output', 'plan_sha256', 'records', 'result', 'waves'
    }
    assert claim_id not in proc.stdout
    assert output_path.exists()


def _record(batch: dict, unit: dict, *, agent: str) -> dict:
    common = {
        'schema_version': 1,
        'row_id': f'{batch["batch_id"]}-{unit["unit_id"]}',
        'run_id': 'audit-run',
        'relationship_epoch': 'READY(1)',
        'role': batch['role'],
        'agent_id': agent,
        'blind_to': [batch['counterpart_role']],
        'verdict': 'hold',
    }
    if batch['kind'] == 'bullet':
        return {
            **common,
            'row_type': 'bullet_verdict',
            'claim_instance_id': unit['unit_id'],
            'role_version': 'reader-v1',
            'quote': 'literal evidence',
            'reasoning': 'The complete evidence entails this exact claim.',
            'confidence': 'high',
            'correction': None,
            'quote_validated': True,
        }
    return {
        **common,
        'row_type': 'page_reader',
        'page_path': unit['unit_id'],
        'page_generation': unit['page_generation'],
        'raw_manifest': unit['raw_manifest'],
        'defects': [],
        'evidence': 'Read the full page and complete raw manifest.',
    }


def _write_artifacts(plan: dict, folder: Path) -> None:
    folder.mkdir()
    for index, batch in enumerate(plan['batches']):
        agent = f'agent-{index}'
        payload = {
            'schema_version': 1,
            'run_id': plan['run_id'],
            'relationship_epoch': plan['relationship_epoch'],
            'batch_id': batch['batch_id'],
            'plan_sha256': plan['plan_sha256'],
            'input_sha256': plan['input_sha256'],
            'role': batch['role'],
            'agent_id': agent,
            'reader_run_id': f'reader-run-{index}',
            'unit_ids': [unit['unit_id'] for unit in batch['units']],
            'records': [_record(batch, unit, agent=agent) for unit in batch['units']],
        }
        (folder / f'{batch["batch_id"]}.json').write_text(json.dumps(payload))


def test_collect_accepts_exact_full_sidecars(tmp_path: Path) -> None:
    plan = batcher.build_plan(_input(
        bullets=[_unit(_digest('claim'), 1)],
        pages=[_unit('1-wiki/concepts/page.md', 1)],
    ))
    folder = tmp_path / 'artifacts'
    _write_artifacts(plan, folder)
    collected = batcher.collect_artifacts(plan, folder)
    assert collected['terminal_calls'] == 4
    assert collected['terminal_records'] == 4
    assert len(collected['records_sha256']) == 64


def _write_collected_execution(
    tmp_path: Path, *, identity: str = 'journal-claim'
) -> tuple[Path, Path, dict]:
    plan = batcher.build_plan(_input(
        bullets=[_unit(_digest(identity), 1)]
    ))
    folder = tmp_path / f'{identity}-sidecars'
    _write_artifacts(plan, folder)
    collected = batcher.collect_artifacts(plan, folder)
    plan_path = tmp_path / f'{identity}-plan.json'
    collected_path = tmp_path / f'{identity}-collected.json'
    batcher._atomic_write(plan_path, plan)
    batcher._atomic_write(collected_path, collected)
    return plan_path, collected_path, plan


def test_execution_journal_initializes_once_and_appends_exact_execution(
    tmp_path: Path,
) -> None:
    journal_path = tmp_path / 'execution-journal.json'
    baseline_sha = _digest('warning-baseline')
    initialized = batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=baseline_sha,
    )
    assert initialized['entries'] == []
    with pytest.raises(batcher.BatchError, match='refusing'):
        batcher.init_execution_journal(
            path=journal_path,
            run_id='audit-run',
            warning_baseline_sha256=baseline_sha,
        )
    plan_path, collected_path, plan = _write_collected_execution(tmp_path)
    appended = batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    assert len(appended['entries']) == 1
    assert appended['entries'][0]['plan_sha256'] == plan['plan_sha256']
    batcher.validate_execution_journal(
        json.loads(journal_path.read_text())
    )


def test_execution_journal_rejects_rehashed_history_tamper_before_append(
    tmp_path: Path,
) -> None:
    journal_path = tmp_path / 'execution-journal.json'
    batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=_digest('warning-baseline'),
    )
    plan_path, collected_path, _ = _write_collected_execution(
        tmp_path, identity='first'
    )
    batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    journal = json.loads(journal_path.read_text())
    journal['entries'][0]['collected_sha256'] = '0' * 64
    journal['journal_sha256'] = batcher._sha256({
        key: value for key, value in journal.items()
        if key != 'journal_sha256'
    })
    journal_path.write_text(json.dumps(journal))
    next_plan, next_collected, _ = _write_collected_execution(
        tmp_path, identity='second'
    )
    with pytest.raises(batcher.BatchError, match='breaks the hash chain'):
        batcher.append_execution_journal(
            path=journal_path,
            plan_path=next_plan,
            collected_path=next_collected,
        )


def test_execution_journal_rejects_duplicate_plan_append(
    tmp_path: Path,
) -> None:
    journal_path = tmp_path / 'execution-journal.json'
    batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=_digest('warning-baseline'),
    )
    plan_path, collected_path, _ = _write_collected_execution(tmp_path)
    batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    with pytest.raises(batcher.BatchError, match='already journaled'):
        batcher.append_execution_journal(
            path=journal_path,
            plan_path=plan_path,
            collected_path=collected_path,
        )


def test_execution_anchors_prevent_deleted_journal_reinitialization(
    tmp_path: Path,
) -> None:
    journal_path = tmp_path / 'run' / 'execution-journal.json'
    baseline_sha = _digest('warning-baseline')
    batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=baseline_sha,
    )
    plan_path, collected_path, _ = _write_collected_execution(tmp_path)
    batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    journal_path.unlink()
    with pytest.raises(batcher.BatchError, match='already has state'):
        batcher.init_execution_journal(
            path=journal_path,
            run_id='audit-run',
            warning_baseline_sha256=baseline_sha,
        )


def test_execution_append_recovers_anchor_ahead_of_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal_path = tmp_path / 'run' / 'execution-journal.json'
    batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=_digest('warning-baseline'),
    )
    plan_path, collected_path, _ = _write_collected_execution(tmp_path)
    original_atomic_write = batcher._atomic_write

    def fail_journal_replace(*, path: Path, value: object) -> None:
        raise OSError('simulated journal replace failure')

    monkeypatch.setattr(batcher, '_atomic_write', fail_journal_replace)
    with pytest.raises(OSError, match='simulated'):
        batcher.append_execution_journal(
            path=journal_path,
            plan_path=plan_path,
            collected_path=collected_path,
        )
    assert len(list((journal_path.parent / 'execution-anchors').iterdir())) == 1
    monkeypatch.setattr(batcher, '_atomic_write', original_atomic_write)
    recovered = batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    assert len(recovered['entries']) == 1
    batcher._load_execution_anchors(
        journal_path=journal_path, journal=recovered
    )


def test_execution_append_recovers_interrupted_anchor_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal_path = tmp_path / 'run' / 'execution-journal.json'
    batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=_digest('warning-baseline'),
    )
    plan_path, collected_path, _ = _write_collected_execution(tmp_path)
    original_dump = batcher.json.dump

    def fail_after_partial_write(value: object, handle: object, **kwargs) -> None:
        handle.write('{"schema_version":')
        raise OSError('simulated anchor short write')

    monkeypatch.setattr(batcher.json, 'dump', fail_after_partial_write)
    with pytest.raises(OSError, match='simulated anchor short write'):
        batcher.append_execution_journal(
            path=journal_path,
            plan_path=plan_path,
            collected_path=collected_path,
        )
    anchor_directory = journal_path.parent / 'execution-anchors'
    assert list(anchor_directory.iterdir()) == []

    interrupted_temp = anchor_directory / '.execution-001.json.interrupted'
    interrupted_temp.write_text('{"schema_version":')
    monkeypatch.setattr(batcher.json, 'dump', original_dump)
    recovered = batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    assert len(recovered['entries']) == 1
    assert not interrupted_temp.exists()
    batcher._load_execution_anchors(
        journal_path=journal_path, journal=recovered
    )


def test_execution_append_recovers_published_anchor_temp_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal_path = tmp_path / 'run' / 'execution-journal.json'
    batcher.init_execution_journal(
        path=journal_path,
        run_id='audit-run',
        warning_baseline_sha256=_digest('warning-baseline'),
    )
    plan_path, collected_path, _ = _write_collected_execution(tmp_path)
    original_unlink = batcher.os.unlink

    def fail_anchor_temp_unlink(path: object, *args, **kwargs) -> None:
        if Path(path).name.startswith('.execution-001.json.'):
            raise OSError('simulated anchor temp cleanup failure')
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(batcher.os, 'unlink', fail_anchor_temp_unlink)
    with pytest.raises(OSError, match='simulated anchor temp cleanup failure'):
        batcher.append_execution_journal(
            path=journal_path,
            plan_path=plan_path,
            collected_path=collected_path,
        )
    journal = json.loads(journal_path.read_text())
    assert journal['entries'] == []
    anchor_directory = journal_path.parent / 'execution-anchors'
    assert len(list(anchor_directory.iterdir())) == 2

    monkeypatch.setattr(batcher.os, 'unlink', original_unlink)
    recovered = batcher.append_execution_journal(
        path=journal_path,
        plan_path=plan_path,
        collected_path=collected_path,
    )
    assert len(recovered['entries']) == 1
    assert {path.name for path in anchor_directory.iterdir()} == {
        'execution-001.json'
    }
    batcher._load_execution_anchors(
        journal_path=journal_path, journal=recovered
    )


def test_collect_rejects_self_rehashed_plan_with_dropped_batch(
    tmp_path: Path,
) -> None:
    plan = batcher.build_plan(_input(
        bullets=[_unit(_digest('claim-a'), 1), _unit(_digest('claim-b'), 1)]
    ))
    plan['batches'][0]['units'] = plan['batches'][0]['units'][:1]
    plan['batches'][0]['size'] = 1
    plan['batches'][0]['batch_id'] = batcher._batch_id(
        run_id=plan['run_id'],
        epoch=plan['relationship_epoch'],
        input_sha256=plan['input_sha256'],
        kind=plan['batches'][0]['kind'],
        role=plan['batches'][0]['role'],
        manifest_sha256=plan['batches'][0]['manifest_sha256'],
        batch_number=plan['batches'][0]['batch_number'],
        units=plan['batches'][0]['units'],
    )
    plan['plan_sha256'] = batcher._sha256({
        key: value for key, value in plan.items() if key != 'plan_sha256'
    })
    folder = tmp_path / 'artifacts'
    folder.mkdir()
    with pytest.raises(batcher.BatchError, match='both roles|reconstruct'):
        batcher.collect_artifacts(plan, folder)


def test_collect_rejects_self_rehashed_empty_plan(tmp_path: Path) -> None:
    plan = batcher.build_plan(_input(bullets=[_unit(_digest('claim'), 1)]))
    plan['batches'] = []
    for key in (
        'planned_groups', 'planned_bullet_records', 'planned_page_records',
        'planned_calls', 'planned_waves',
    ):
        plan[key] = 0
    plan['input_sha256'] = batcher._sha256(_input())
    plan['plan_sha256'] = batcher._sha256({
        key: value for key, value in plan.items() if key != 'plan_sha256'
    })
    with pytest.raises(batcher.BatchError, match='no executable batches'):
        batcher.collect_artifacts(plan, tmp_path)


@pytest.mark.parametrize('defect', ['missing', 'pooled', 'wrong_hash', 'wrong_role'])
def test_collect_rejects_incomplete_or_stale_sidecars(tmp_path: Path, defect: str) -> None:
    units = [_unit(_digest(f'claim-{i}'), 1) for i in range(2)]
    plan = batcher.build_plan(_input(bullets=units))
    folder = tmp_path / 'artifacts'
    _write_artifacts(plan, folder)
    path = folder / f'{plan["batches"][0]["batch_id"]}.json'
    payload = json.loads(path.read_text())
    if defect == 'missing':
        path.unlink()
    elif defect == 'pooled':
        payload['records'] = payload['records'][:1]
        path.write_text(json.dumps(payload))
    elif defect == 'wrong_hash':
        payload['plan_sha256'] = '0' * 64
        path.write_text(json.dumps(payload))
    else:
        payload['records'][0]['role'] = payload['blind_to'][0] if 'blind_to' in payload else 'entailment_bullet'
        path.write_text(json.dumps(payload))
    with pytest.raises(batcher.BatchError):
        batcher.collect_artifacts(plan, folder)


def test_collect_rejects_one_agent_reused_across_blind_roles(tmp_path: Path) -> None:
    plan = batcher.build_plan(_input(bullets=[_unit(_digest('claim'), 1)]))
    folder = tmp_path / 'artifacts'
    _write_artifacts(plan, folder)
    for path in folder.glob('*.json'):
        payload = json.loads(path.read_text())
        payload['agent_id'] = 'same-agent'
        payload['records'][0]['agent_id'] = 'same-agent'
        path.write_text(json.dumps(payload))
    with pytest.raises(batcher.BatchError, match='reuses one agent'):
        batcher.collect_artifacts(plan, folder)


def test_exhaustive_negative_hold_requires_complete_population(tmp_path: Path) -> None:
    unit = _unit(_digest('negative-claim'), 1, scope='exhaustive_negative')
    second_path = '0-raw/papers/raw-002.pdf'
    unit['raw_manifest'].append({
        'raw_path': second_path,
        'sha256': _digest('raw-2'),
    })
    unit['quantified_population']['raw_paths'].append(second_path)
    unit['quantified_population']['members'] = [
        {
            'member_id': 'source-a',
            'raw_paths': [unit['quantified_population']['raw_paths'][0]],
        },
        {
            'member_id': 'source-b',
            'raw_paths': [unit['quantified_population']['raw_paths'][1]],
        },
    ]
    plan = batcher.build_plan(_input(bullets=[unit]))
    folder = tmp_path / 'artifacts'
    _write_artifacts(plan, folder)
    for path in folder.glob('*.json'):
        payload = json.loads(path.read_text())
        payload['records'][0]['quantified_scope'] = {
            'raw_population': unit['quantified_population']['raw_paths'],
            'population': ['source-a', 'source-b'],
            'searched_members': ['source-a'],
            'counterexamples': [],
            'search_summary': 'Only one source was searched.',
        }
        path.write_text(json.dumps(payload))
    with pytest.raises(batcher.BatchError, match='not exhaustive'):
        batcher.collect_artifacts(plan, folder)


def test_exhaustive_negative_rejects_self_asserted_partial_population() -> None:
    unit = _unit(_digest('negative-two-raw'), 1, scope='exhaustive_negative')
    unit['raw_manifest'].append({
        'raw_path': '0-raw/papers/raw-002.pdf',
        'sha256': _digest('raw-2'),
    })
    with pytest.raises(batcher.BatchError, match='raw population differs'):
        batcher.build_plan(_input(bullets=[unit]))


def test_exhaustive_negative_rejects_one_member_for_two_raws() -> None:
    unit = _unit(_digest('negative-collapsed-members'), 1,
                 scope='exhaustive_negative')
    second_path = '0-raw/papers/raw-002.pdf'
    unit['raw_manifest'].append({
        'raw_path': second_path,
        'sha256': _digest('raw-2'),
    })
    unit['quantified_population']['raw_paths'].append(second_path)
    unit['quantified_population']['members'] = [{
        'member_id': 'claimed-complete-universe',
        'raw_paths': list(unit['quantified_population']['raw_paths']),
    }]
    with pytest.raises(batcher.BatchError, match='raw-complete'):
        batcher.build_plan(_input(bullets=[unit]))


def test_exhaustive_population_allows_multiple_semantic_members_per_raw() -> None:
    unit = _unit(_digest('ten-conditions'), 1,
                 scope='exhaustive_negative')
    raw_path = unit['raw_manifest'][0]['raw_path']
    unit['quantified_population']['members'] = [
        {'member_id': f'condition-{index:02d}', 'raw_paths': [raw_path]}
        for index in range(1, 11)
    ]
    plan = batcher.build_plan(_input(bullets=[unit]))
    assert plan['planned_bullet_records'] == 2


@pytest.mark.parametrize(
    ('keyword', 'value'),
    [
        ('max_bullet_units', batcher.HARD_MAX_BULLET_UNITS + 1),
        ('max_page_units', batcher.HARD_MAX_PAGE_UNITS + 1),
        ('max_concurrent_calls', batcher.HARD_MAX_CONCURRENT_CALLS + 1),
        ('max_concurrent_calls', True),
    ],
)
def test_hard_batch_and_concurrency_caps_cannot_be_overridden(
    keyword: str, value: int,
) -> None:
    options = {keyword: value}
    with pytest.raises(batcher.BatchError, match='hard maxima'):
        batcher.build_plan(
            _input(bullets=[_unit(_digest('claim'), 1)]), **options
        )


def test_collect_rejects_symlinked_sidecar(tmp_path: Path) -> None:
    plan = batcher.build_plan(_input(bullets=[_unit(_digest('claim'), 1)]))
    folder = tmp_path / 'artifacts'
    _write_artifacts(plan, folder)
    path = folder / f'{plan["batches"][0]["batch_id"]}.json'
    outside = tmp_path / 'outside.json'
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(batcher.BatchError, match='symlink'):
        batcher.collect_artifacts(plan, folder)


def test_collect_rejects_truncated_bullet_schema(tmp_path: Path) -> None:
    plan = batcher.build_plan(_input(bullets=[_unit(_digest('claim'), 1)]))
    folder = tmp_path / 'artifacts'
    _write_artifacts(plan, folder)
    path = folder / f'{plan["batches"][0]["batch_id"]}.json'
    payload = json.loads(path.read_text())
    del payload['records'][0]['role_version']
    path.write_text(json.dumps(payload))
    with pytest.raises(batcher.BatchError, match='incomplete'):
        batcher.collect_artifacts(plan, folder)
