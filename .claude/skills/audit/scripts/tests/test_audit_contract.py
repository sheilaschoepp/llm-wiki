import importlib.util
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).parents[1]
REPO_ROOT = Path(__file__).parents[5]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


completion = _load(
    'audit_completion_validator', SCRIPTS / 'validate_audit_completion.py'
)
enumerator = _load(
    'audit_occurrence_enumerator', SCRIPTS / 'enumerate_unlinked_mentions.py'
)
batcher = _load(
    'audit_suppression_batcher', SCRIPTS / 'build_suppression_batches.py'
)
baseline_capture = _load(
    'audit_warning_baseline_capture',
    SCRIPTS / 'capture_warning_baseline.py',
)
reader_batcher = _load(
    'audit_reader_batcher', SCRIPTS / 'manage_reader_batches.py'
)
page_checkpoint = _load(
    'audit_page_checkpoint', SCRIPTS / 'capture_page_checkpoint.py'
)
checker = _load(
    'audit_contract_check_wiki',
    REPO_ROOT / '.claude/skills/multi-skill/scripts/check_wiki.py',
)


RULE_BYTES = b'rule\n'
RELATIONSHIP_BYTES = b'relationship\n'
IGNORE_BYTES = (
    b'# ignore\n\n## verified-ignore\n\n'
    b'## vague-source-referent-verified-ignore\n'
)
TARGET_BYTES = b'---\ntype: concept\nstatus: draft\n---\nTarget.\n'
HOST_BYTES = b'target\n' * 700
CHECKER_BYTES = (
    b'import json\nUNLINKED_MENTION_IGNORE=[]\n'
    b'if __name__ == "__main__": print(json.dumps([]))\n'
)


def _context_for(occurrences):
    target_paths = sorted(
        {row['target_path'] for row in occurrences if row['origin'] == 'initial'}
    )
    payload = {
        'canonical_rule_hashes': {
            path: hashlib.sha256(RULE_BYTES).hexdigest()
            for path in baseline_capture.CANONICAL_RULE_PATHS
        },
        'relationship_rule_hashes': {
            path: hashlib.sha256(RELATIONSHIP_BYTES).hexdigest()
            for path in baseline_capture.RELATIONSHIP_RULE_PATHS
        },
        'target_page_hashes': {
            path: hashlib.sha256(TARGET_BYTES).hexdigest()
            for path in target_paths
        },
        'initial_ignore_sha256': hashlib.sha256(IGNORE_BYTES).hexdigest(),
    }
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(',', ':')
        ).encode()
    ).hexdigest()


def _write_baseline(
    tmp_path, rec, *, frozen_occurrences=None, page_preimages=None
):
    warnings = rec.get('warning_fingerprints', [])
    occurrences = rec.get('mention_occurrences', [])
    initial_warnings = [row for row in warnings if row['origin'] == 'initial']
    terminal_initial_occurrences = [
        row for row in occurrences if row['origin'] == 'initial'
    ]
    if frozen_occurrences is None:
        frozen_occurrences = [
            {key: row[key] for key in batcher.CANDIDATE_FIELDS}
            for row in terminal_initial_occurrences
        ]
    checker_findings = [
        {
            'severity': 'warning',
            'check_id': row['check_id'],
            'file': row['page_path'],
            'target': row['target'],
            'message': row['resolution'],
            'fix_hint': 'fix',
        }
        for row in initial_warnings
    ]
    groups = {}
    for row in frozen_occurrences:
        groups[(row['page_path'], row['target_stem'])] = (
            groups.get((row['page_path'], row['target_stem']), 0) + 1
        )
    checker_findings.extend(
        {
            'severity': 'warning',
            'check_id': 'unlinked_page_mention',
            'file': page,
            'message': (
                'Existing page `{}` is mentioned unlinked {}× in this page'
            ).format(target, groups[(page, target)]),
            'fix_hint': 'enumerate',
        }
        for page, target in sorted(groups)
    )
    affected = {}
    for row in initial_warnings:
        data = ('warning-' + row['page_path']).encode()
        affected[row['page_path']] = {
            'sha256': hashlib.sha256(data).hexdigest(),
            'bytes_base64': base64.b64encode(data).decode(),
            'status': 'draft',
            'verified_hash': '',
        }
    for row in frozen_occurrences:
        data = HOST_BYTES
        affected[row['page_path']] = {
            'sha256': hashlib.sha256(data).hexdigest(),
            'bytes_base64': base64.b64encode(data).decode(),
            'status': 'draft',
            'verified_hash': '',
        }
    if page_preimages:
        affected.update(page_preimages)

    for path in baseline_capture.CANONICAL_RULE_PATHS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(RULE_BYTES)
    for path in baseline_capture.RELATIONSHIP_RULE_PATHS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(RELATIONSHIP_BYTES)
    checker_path = tmp_path / baseline_capture.CANONICAL_CHECKER_PATH
    checker_path.parent.mkdir(parents=True, exist_ok=True)
    checker_path.write_bytes(CHECKER_BYTES)
    ignore = tmp_path / baseline_capture.IGNORE_PATH
    ignore.parent.mkdir(parents=True, exist_ok=True)
    mention_entries = [
        row['ignore_entry']
        for row in occurrences
        if row.get('ignore_entry') is not None
    ]
    vague_entries = [
        row['ignore_entry']
        for row in warnings
        if row.get('ignore_entry') is not None
    ]
    section = b'## vague-source-referent-verified-ignore\n'
    before, after = IGNORE_BYTES.split(section, 1)
    ignore.write_bytes(
        before
        + ''.join(entry + '\n' for entry in mention_entries).encode()
        + section
        + after
        + ''.join(entry + '\n' for entry in vague_entries).encode()
    )
    frozen_target_paths = sorted(
        {row['target_path'] for row in frozen_occurrences}
        | set(page_preimages or {})
    )
    for path in frozen_target_paths:
        if page_preimages and path in page_preimages:
            continue
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(TARGET_BYTES)

    canonical_hashes = {
        path: hashlib.sha256(RULE_BYTES).hexdigest()
        for path in baseline_capture.CANONICAL_RULE_PATHS
    }
    relationship_hashes = {
        path: hashlib.sha256(RELATIONSHIP_BYTES).hexdigest()
        for path in baseline_capture.RELATIONSHIP_RULE_PATHS
    }
    target_hashes = {
        path: (
            page_preimages[path]['sha256']
            if page_preimages and path in page_preimages
            else hashlib.sha256(TARGET_BYTES).hexdigest()
        )
        for path in frozen_target_paths
    }
    context_payload = {
        'canonical_rule_hashes': canonical_hashes,
        'relationship_rule_hashes': relationship_hashes,
        'target_page_hashes': target_hashes,
        'initial_ignore_sha256': hashlib.sha256(IGNORE_BYTES).hexdigest(),
    }
    context = hashlib.sha256(
        json.dumps(
            context_payload, sort_keys=True, separators=(',', ':')
        ).encode()
    ).hexdigest()
    payload = {
        'schema_version': 1,
        'kind': 'audit-warning-baseline',
        'run_id': 'run',
        'baseline_id': 'baseline-run',
        'git_pre_edit': {
            'head': 'unavailable',
            'status_sha256': hashlib.sha256(b'').hexdigest(),
            'status_bytes_base64': '',
        },
        'checker': {
            'path': baseline_capture.CANONICAL_CHECKER_PATH,
            'sha256': hashlib.sha256(CHECKER_BYTES).hexdigest(),
            'status': 0,
            'findings': checker_findings,
            'warning_findings': checker_findings,
        },
        'warning_fingerprints': [
            {key: row[key] for key in completion.WARNING_ID_FIELDS}
            for row in initial_warnings
        ],
        'enumerator': {
            'status': 'ok',
            'groups': [
                {
                    'page_path': page,
                    'target_stem': target,
                    'exact_occurrences': count,
                }
                for (page, target), count in sorted(groups.items())
            ],
            'occurrences': frozen_occurrences,
            'mention_groups': len(groups),
            'exact_occurrences': len(frozen_occurrences),
            'zero_match_scanner_defects': 0,
        },
        'affected_page_preimages': affected,
        'ignore_file': {
            'path': baseline_capture.IGNORE_PATH,
            'sha256': hashlib.sha256(IGNORE_BYTES).hexdigest(),
            'bytes_base64': base64.b64encode(IGNORE_BYTES).decode(),
        },
        'canonical_rule_hashes': canonical_hashes,
        'relationship_rule_hashes': relationship_hashes,
        'target_page_hashes': target_hashes,
        'evidence_context_sha256': context,
    }
    data = json.dumps(
        payload, sort_keys=True, separators=(',', ':')
    ).encode() + b'\n'
    path = tmp_path / baseline_capture.BASELINE_DIRECTORY / 'baseline.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return (
        path.relative_to(tmp_path).as_posix(),
        hashlib.sha256(data).hexdigest(),
        context,
    )


def _write_preverification_checkpoint(
    tmp_path,
    *,
    baseline_path,
    baseline_sha,
    page_preimages=None,
):
    baseline = json.loads((tmp_path / baseline_path).read_text())
    pages = {}
    for relative in sorted(baseline['target_page_hashes']):
        if page_preimages and relative in page_preimages:
            record = dict(page_preimages[relative])
        else:
            data = (tmp_path / relative).read_bytes()
            text = data.decode()
            record = {
                'sha256': hashlib.sha256(data).hexdigest(),
                'bytes_base64': base64.b64encode(data).decode(),
                'status': page_checkpoint._frontmatter_value(
                    text=text, key='status'
                ),
                'verified_hash': page_checkpoint._frontmatter_value(
                    text=text, key='verified_hash'
                ),
            }
        pages[relative] = record
    payload = {
        'schema_version': 1,
        'kind': 'audit-preverification-page-checkpoint',
        'run_id': 'run',
        'warning_baseline_sha256': baseline_sha,
        'pages': pages,
    }
    data = json.dumps(payload, sort_keys=True, indent=2).encode() + b'\n'
    path = (
        tmp_path / baseline_capture.BASELINE_DIRECTORY
        / 'audit-run-preverification.json'
    )
    path.write_bytes(data)
    return {
        'preverification_checkpoint_path': path.relative_to(
            tmp_path
        ).as_posix(),
        'preverification_checkpoint_sha256': hashlib.sha256(data).hexdigest(),
    }


def _write_execution_journal(
    tmp_path, *, executions, baseline_sha='b' * 64,
):
    genesis = hashlib.sha256(completion._canonical_json(value={
        'kind': 'audit-reader-execution-journal-genesis',
        'run_id': 'run',
        'warning_baseline_sha256': baseline_sha,
    })).hexdigest()
    previous_entry = genesis
    previous_anchor = genesis
    entries = []
    anchor_directory = (
        tmp_path
        / '2-outputs/audit/reader-artifacts/run/execution-anchors'
    )
    anchor_directory.mkdir(parents=True, exist_ok=True)
    for index, execution in enumerate(executions, 1):
        anchor = {
            'schema_version': 1,
            'run_id': 'run',
            'warning_baseline_sha256': baseline_sha,
            'execution_number': index,
            'plan_sha256': execution['plan_sha256'],
            'collected_sha256': execution['collected_sha256'],
            'previous_anchor_sha256': previous_anchor,
        }
        anchor['anchor_sha256'] = hashlib.sha256(
            completion._canonical_json(value=anchor)
        ).hexdigest()
        (anchor_directory / f'execution-{index:03d}.json').write_text(
            json.dumps(anchor)
        )
        entry = {
            'execution_number': index,
            'plan_sha256': execution['plan_sha256'],
            'collected_sha256': execution['collected_sha256'],
            'previous_entry_sha256': previous_entry,
            'anchor_sha256': anchor['anchor_sha256'],
        }
        entry['entry_sha256'] = hashlib.sha256(
            completion._canonical_json(value=entry)
        ).hexdigest()
        entries.append(entry)
        previous_entry = entry['entry_sha256']
        previous_anchor = anchor['anchor_sha256']
    journal = {
        'schema_version': 1,
        'run_id': 'run',
        'warning_baseline_sha256': baseline_sha,
        'entries': entries,
    }
    journal['journal_sha256'] = hashlib.sha256(
        completion._canonical_json(value=journal)
    ).hexdigest()
    data = json.dumps(journal).encode()
    path = (
        tmp_path
        / '2-outputs/audit/reader-artifacts/run/execution-journal.json'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        'warning_baseline_sha256': baseline_sha,
        'reader_execution_journal_path': (
            '2-outputs/audit/reader-artifacts/run/execution-journal.json'
        ),
        'reader_execution_journal_sha256': hashlib.sha256(data).hexdigest(),
    }


def _reader_execution(tmp_path, *, kind='page', verdict='hold'):
    generation = hashlib.sha256(b'page').hexdigest()
    unit = {
        'unit_id': (
            hashlib.sha256(b'claim').hexdigest()
            if kind == 'bullet'
            else '1-wiki/concepts/example.md'
        ),
        'page_generation': generation,
        'raw_manifest': [],
        'verification_scope': 'ordinary',
        'quantified_population': None,
    }
    plan = reader_batcher.build_plan({
        'schema_version': 1,
        'run_id': 'run',
        'relationship_epoch': 'READY(1)',
        'bullet_units': [unit] if kind == 'bullet' else [],
        'page_units': [unit] if kind == 'page' else [],
    })
    folder = (
        tmp_path / '2-outputs/audit/reader-artifacts/run/execution-001'
    )
    sidecars = folder / 'sidecars'
    sidecars.mkdir(parents=True)
    for index, batch in enumerate(plan['batches']):
        unit = batch['units'][0]
        agent = f'agent-{index}'
        record_verdict = (
            verdict[batch['role']] if isinstance(verdict, dict) else verdict
        )
        common = {
            'schema_version': 1,
            'row_id': batch['batch_id'],
            'run_id': 'run',
            'relationship_epoch': 'READY(1)',
            'role': batch['role'],
            'agent_id': agent,
            'blind_to': [batch['counterpart_role']],
            'verdict': record_verdict,
        }
        if kind == 'bullet':
            record = {
                **common,
                'row_type': 'bullet_verdict',
                'claim_instance_id': unit['unit_id'],
                'role_version': 'reader-v1',
                'quote': 'Literal evidence.',
                'reasoning': 'The exact evidence entails the claim.',
                'confidence': 'high',
                'correction': (
                    None
                    if record_verdict == 'hold'
                    else 'Remove unsupported claim.'
                ),
                'quote_validated': True,
            }
        else:
            record = {
                **common,
                'row_type': 'page_reader',
                'page_path': unit['unit_id'],
                'page_generation': generation,
                'raw_manifest': [],
                'defects': (
                    [] if record_verdict == 'hold'
                    else [{'scope': 'page_only', 'detail': 'Test defect.'}]
                ),
                'evidence': 'Full final page and complete manifest reviewed.',
            }
        artifact = {
            'schema_version': 1,
            'run_id': 'run',
            'relationship_epoch': 'READY(1)',
            'batch_id': batch['batch_id'],
            'plan_sha256': plan['plan_sha256'],
            'input_sha256': plan['input_sha256'],
            'role': batch['role'],
            'agent_id': agent,
            'reader_run_id': f'reader-run-{index}',
            'unit_ids': [unit['unit_id']],
            'records': [record],
        }
        (sidecars / f'{batch["batch_id"]}.json').write_text(
            json.dumps(artifact), encoding='utf-8'
        )
    plan_path = folder / 'plan.json'
    plan_path.write_text(json.dumps(plan), encoding='utf-8')
    collected = reader_batcher.collect_artifacts(plan, sidecars)
    collected_path = folder / 'collected.json'
    collected_path.write_text(json.dumps(collected), encoding='utf-8')
    execution = {
        'execution_number': 1,
        'plan_path': (
            '2-outputs/audit/reader-artifacts/run/execution-001/plan.json'
        ),
        'plan_sha256': plan['plan_sha256'],
        'input_sha256': plan['input_sha256'],
        'planned_groups': plan['planned_groups'],
        'planned_calls': plan['planned_calls'],
        'planned_waves': plan['planned_waves'],
        'planned_records': (
            plan['planned_bullet_records']
            if kind == 'bullet'
            else plan['planned_page_records']
        ),
        'artifact_dir': (
            '2-outputs/audit/reader-artifacts/run/execution-001/sidecars'
        ),
        'collected_path': (
            '2-outputs/audit/reader-artifacts/run/execution-001/collected.json'
        ),
        'collected_sha256': hashlib.sha256(
            collected_path.read_bytes()
        ).hexdigest(),
        'terminal_calls': collected['terminal_calls'],
        'terminal_records': collected['terminal_records'],
        'terminal_row_ids': [row['row_id'] for row in collected['records']],
        'superseded_rows': [],
        'records_sha256': collected['records_sha256'],
    }
    adjudications = [
        {
            'schema_version': 1,
            'row_id': f'adjudication-{index}',
            'run_id': 'run',
            'record_row_id': row['row_id'],
            'record_sha256': hashlib.sha256(
                completion._canonical_json(value=row)
            ).hexdigest(),
            'coordinator_id': 'coordinator',
            'coordinator_run_id': 'coordinator-run',
            'evidence_rechecked': True,
            'quote_reextracted': row['row_type'] == 'bullet_verdict',
            'semantic_decision': row['verdict'],
            'reasoning': 'Coordinator independently rechecked the full page.',
        }
        for index, row in enumerate(collected['records'], 1)
    ]
    journal = _write_execution_journal(
        tmp_path, executions=[execution]
    )
    return execution, collected['records'], sidecars, adjudications, journal


def test_reader_execution_authenticates_plan_sidecars_and_ledger(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(tmp_path)
    failures, count = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert failures == []
    assert count == 1


def test_reader_execution_cannot_be_omitted_or_lose_a_sidecar(tmp_path):
    execution, records, sidecars, adjudications, journal = _reader_execution(
        tmp_path
    )
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('do not exactly equal' in item for item in failures)
    next(sidecars.glob('*.json')).unlink()
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('cannot be authenticated' in item for item in failures)


def test_reader_execution_directory_cannot_be_omitted(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(tmp_path)
    extra = (
        tmp_path / '2-outputs/audit/reader-artifacts/run/execution-002'
    )
    extra.mkdir()
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('directory inventory differs' in item for item in failures)


def test_reader_execution_rejects_ignored_suffix_child(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(tmp_path)
    extra = (
        tmp_path / '2-outputs/audit/reader-artifacts/run/execution-001.old'
    )
    extra.mkdir()
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('directory inventory differs' in item for item in failures)


def test_reader_execution_rejects_symlinked_execution_directory(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(tmp_path)
    execution_path = (
        tmp_path / '2-outputs/audit/reader-artifacts/run/execution-001'
    )
    outside = tmp_path / 'moved-execution'
    execution_path.rename(outside)
    execution_path.symlink_to(outside, target_is_directory=True)
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any(
        'symlink' in item or 'not a real directory' in item
        for item in failures
    )


def test_reader_execution_journal_rejects_rehashed_entry_tamper(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(tmp_path)
    journal_path = tmp_path / journal['reader_execution_journal_path']
    payload = json.loads(journal_path.read_text())
    payload['entries'][0]['collected_sha256'] = '0' * 64
    payload['journal_sha256'] = hashlib.sha256(
        completion._canonical_json(value={
            key: value for key, value in payload.items()
            if key != 'journal_sha256'
        })
    ).hexdigest()
    data = json.dumps(payload).encode()
    journal_path.write_bytes(data)
    journal['reader_execution_journal_sha256'] = hashlib.sha256(data).hexdigest()
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('hash-chain link' in item for item in failures)


def test_execution_anchors_reject_journal_truncation_while_census_remains(
    tmp_path,
):
    executions = [
        {
            'plan_sha256': hashlib.sha256(f'plan-{index}'.encode()).hexdigest(),
            'collected_sha256': hashlib.sha256(
                f'collected-{index}'.encode()
            ).hexdigest(),
        }
        for index in (1, 2)
    ]
    reconciliation = _write_execution_journal(
        tmp_path, executions=executions
    )
    journal_path = tmp_path / reconciliation['reader_execution_journal_path']
    journal = json.loads(journal_path.read_text())
    retained = dict(journal['entries'][1])
    retained['execution_number'] = 1
    retained['previous_entry_sha256'] = hashlib.sha256(
        completion._canonical_json(value={
            'kind': 'audit-reader-execution-journal-genesis',
            'run_id': 'run',
            'warning_baseline_sha256': 'b' * 64,
        })
    ).hexdigest()
    retained['entry_sha256'] = hashlib.sha256(
        completion._canonical_json(value={
            key: value for key, value in retained.items()
            if key != 'entry_sha256'
        })
    ).hexdigest()
    journal['entries'] = [retained]
    journal['journal_sha256'] = hashlib.sha256(
        completion._canonical_json(value={
            key: value for key, value in journal.items()
            if key != 'journal_sha256'
        })
    ).hexdigest()
    data = json.dumps(journal).encode()
    journal_path.write_bytes(data)
    reconciliation['reader_execution_journal_sha256'] = hashlib.sha256(
        data
    ).hexdigest()
    failures = completion._validate_execution_journal(
        root=tmp_path,
        reconciliation=reconciliation,
        executions=[executions[1]],
        run_id='run',
    )
    assert any('anchor census' in item for item in failures)


def test_reader_execution_requires_digest_bound_coordinator_review(tmp_path):
    execution, records, _, _, journal = _reader_execution(tmp_path)
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': [],
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('do not cover every retained' in item for item in failures)


def test_counterpart_readers_cannot_impersonate_the_coordinator(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(tmp_path)
    adjudications[0]['coordinator_id'] = records[1]['agent_id']
    adjudications[1]['coordinator_id'] = records[0]['agent_id']
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('independent coordinator identity/run' in item
               for item in failures)


def test_terminal_bullet_plan_must_equal_current_claim_dependencies(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(
        tmp_path, kind='bullet'
    )
    claim_id = records[0]['claim_instance_id']
    claim = {
        'schema_version': 1,
        'row_type': 'claim',
        'row_id': 'claim-row',
        'run_id': 'run',
        'claim_instance_id': claim_id,
        'context_digest': hashlib.sha256(b'page').hexdigest(),
        'raw_dependencies': [{
            'raw_path': '0-raw/papers/required.pdf',
            'sha256': hashlib.sha256(b'required raw').hexdigest(),
        }],
        'verification_scope': 'ordinary',
        'quantified_population': None,
    }
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=[claim, *records],
        run_id='run',
    )
    assert any('terminal bullet unit differs' in item for item in failures)


def test_removed_refute_pair_requires_third_destructive_review(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(
        tmp_path, kind='bullet', verdict='refute'
    )
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('do not cover every removed REFUTE pair' in item
               for item in failures)


def test_removed_refute_pair_accepts_exact_third_reader_sidecar(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(
        tmp_path, kind='bullet', verdict='refute'
    )
    claim_id = records[0]['claim_instance_id']
    review = {
        'schema_version': 1,
        'row_id': 'destructive-review',
        'run_id': 'run',
        'claim_instance_id': claim_id,
        'prior_role_row_ids': [row['row_id'] for row in records],
        'prior_role_sha256': [
            hashlib.sha256(
                completion._canonical_json(value=row)
            ).hexdigest()
            for row in records
        ],
        'agent_id': 'third-reader',
        'reader_run_id': 'third-reader-run',
        'blind_to': ['locator_bullet', 'entailment_bullet'],
        'decision': 'approve',
        'correction': 'Remove unsupported claim.',
        'reasoning': 'Both exact REFUTE records support this correction.',
    }
    directory = (
        tmp_path
        / '2-outputs/audit/reader-artifacts/run/destructive-reviews'
    )
    directory.mkdir()
    artifact = directory / f'{claim_id}.json'
    artifact.write_text(json.dumps(review))
    review['artifact_path'] = (
        f'2-outputs/audit/reader-artifacts/run/destructive-reviews/'
        f'{claim_id}.json'
    )
    review['artifact_sha256'] = hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
    execution['terminal_row_ids'] = []
    execution['terminal_records'] = 0
    execution['superseded_rows'] = [
        {
            'row_id': row['row_id'],
            'superseded_by': review['row_id'],
        }
        for row in records
    ]
    failures, count = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [review],
            **journal,
        },
        ledger_rows=[],
        run_id='run',
    )
    assert failures == []
    assert count == 1


def test_mixed_hold_refute_pair_cannot_be_removed(tmp_path):
    execution, records, _, adjudications, journal = _reader_execution(
        tmp_path,
        kind='bullet',
        verdict={
            'locator_bullet': 'refute',
            'entailment_bullet': 'hold',
        },
    )
    failures, _ = completion._validate_reader_executions(
        root=tmp_path,
        reconciliation={
            'reader_executions': [execution],
            'reader_adjudications': adjudications,
            'destructive_correction_reviews': [],
            **journal,
        },
        ledger_rows=records,
        run_id='run',
    )
    assert any('lacks unanimous' in item for item in failures)


def test_incomplete_infrastructure_report_proves_exact_rollback(tmp_path):
    preimage = (
        b'---\ntype: concept\nstatus: needs-update\n---\n'
        b'> [!idea]\n> - *[unverified]* Claim.\n> ^claim\n'
    )
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_bytes(preimage + b'changed')
    rollback = {
        'page_path': '1-wiki/concepts/example.md',
        'preimage_existed': True,
        'preimage_sha256': hashlib.sha256(preimage).hexdigest(),
        'preimage_bytes_base64': base64.b64encode(preimage).decode(),
        'before_status': 'needs-update',
        'before_verified_hash': None,
        'process_marker_count': 1,
        'rollback_required': True,
    }
    report = _report(
        tmp_path,
        result='incomplete',
        rec={
            'content_rollback_preimages': [rollback],
            'infrastructure_failure_pages': ['1-wiki/concepts/example.md'],
        },
        page_preimages={
            '1-wiki/concepts/example.md': {
                'sha256': hashlib.sha256(preimage).hexdigest(),
                'bytes_base64': base64.b64encode(preimage).decode(),
                'status': 'needs-update',
                'verified_hash': '',
            }
        },
    )
    valid, result = completion.validate_incomplete_rollback(
        report, repo_root=tmp_path
    )
    assert valid is False
    assert any('do not equal rollback preimage' in item
               for item in result['failures'])
    page.write_bytes(preimage)
    valid, result = completion.validate_incomplete_rollback(
        report, repo_root=tmp_path
    )
    assert valid is True, result['failures']


def test_incomplete_rollback_cannot_omit_a_changed_baseline_page(tmp_path):
    preimage = b'---\ntype: concept\nstatus: draft\n---\nOriginal.\n'
    page_path = '1-wiki/concepts/changed.md'
    page = tmp_path / page_path
    page.parent.mkdir(parents=True)
    page.write_bytes(preimage + b'Undeclared change.\n')
    report = _report(
        tmp_path,
        result='incomplete',
        rec={
            'content_rollback_preimages': [],
            'infrastructure_failure_pages': [],
        },
        page_preimages={
            page_path: {
                'sha256': hashlib.sha256(preimage).hexdigest(),
                'bytes_base64': base64.b64encode(preimage).decode(),
                'status': 'draft',
                'verified_hash': '',
            }
        },
    )
    valid, result = completion.validate_incomplete_rollback(
        report, repo_root=tmp_path
    )
    assert valid is False
    assert any('undeclared page change' in item for item in result['failures'])


def test_incomplete_rollback_rejects_post_edit_bytes_as_preimage(tmp_path):
    baseline_bytes = b'---\ntype: concept\nstatus: draft\n---\nOriginal.\n'
    post_edit = b'---\ntype: concept\nstatus: draft\n---\nPost-edit.\n'
    page_path = '1-wiki/concepts/forged.md'
    page = tmp_path / page_path
    page.parent.mkdir(parents=True)
    page.write_bytes(post_edit)
    report = _report(
        tmp_path,
        result='incomplete',
        rec={
            'content_rollback_preimages': [{
                'page_path': page_path,
                'preimage_existed': True,
                'preimage_sha256': hashlib.sha256(post_edit).hexdigest(),
                'preimage_bytes_base64': base64.b64encode(post_edit).decode(),
                'before_status': 'draft',
                'before_verified_hash': None,
                'process_marker_count': 0,
                'rollback_required': True,
            }],
            'infrastructure_failure_pages': [page_path],
        },
        page_preimages={
            page_path: {
                'sha256': hashlib.sha256(baseline_bytes).hexdigest(),
                'bytes_base64': base64.b64encode(baseline_bytes).decode(),
                'status': 'draft',
                'verified_hash': '',
            }
        },
    )
    valid, result = completion.validate_incomplete_rollback(
        report, repo_root=tmp_path
    )
    assert valid is False
    assert any('baseline binding is invalid' in item
               for item in result['failures'])


def test_new_page_has_authenticated_did_not_exist_rollback_state(tmp_path):
    page_path = '1-wiki/concepts/new-split.md'
    page = tmp_path / page_path
    page.parent.mkdir(parents=True)
    page.write_text('---\ntype: concept\nstatus: draft\n---\nNew page.\n')
    rollback = {
        'page_path': page_path,
        'preimage_existed': False,
        'preimage_sha256': hashlib.sha256(b'').hexdigest(),
        'preimage_bytes_base64': '',
        'before_status': None,
        'before_verified_hash': None,
        'process_marker_count': 0,
        'rollback_required': False,
    }
    ledger_rows = [{
        'row_type': 'status_write',
        'run_id': 'run',
        'page_path': page_path,
    }]
    reconciliation = {
        'content_rollback_preimages': [rollback],
        'infrastructure_failure_pages': [],
    }
    assert completion._validate_content_rollback_preimages(
        root=tmp_path,
        reconciliation=reconciliation,
        ledger_rows=ledger_rows,
        run_id='run',
        require_restored=False,
        expected_preimage_hashes={},
    ) == []
    page.unlink()
    rollback['rollback_required'] = True
    reconciliation['infrastructure_failure_pages'] = [page_path]
    assert completion._validate_content_rollback_preimages(
        root=tmp_path,
        reconciliation=reconciliation,
        ledger_rows=ledger_rows,
        run_id='run',
        require_restored=True,
        expected_preimage_hashes={},
    ) == []


def test_existing_page_cannot_claim_did_not_exist_at_baseline(tmp_path):
    page_path = '1-wiki/concepts/existing.md'
    rollback = {
        'page_path': page_path,
        'preimage_existed': False,
        'preimage_sha256': hashlib.sha256(b'').hexdigest(),
        'preimage_bytes_base64': '',
        'before_status': None,
        'before_verified_hash': None,
        'process_marker_count': 0,
        'rollback_required': False,
    }
    failures = completion._validate_content_rollback_preimages(
        root=tmp_path,
        reconciliation={
            'content_rollback_preimages': [rollback],
            'infrastructure_failure_pages': [],
        },
        ledger_rows=[{
            'row_type': 'status_write',
            'run_id': 'run',
            'page_path': page_path,
        }],
        run_id='run',
        require_restored=False,
        expected_preimage_hashes={page_path: 'a' * 64},
    )
    assert any('did-not-exist state' in item for item in failures)


def test_preverification_checkpoint_accepts_legitimate_step4a_page_change(
    tmp_path,
):
    original = b'---\ntype: concept\nstatus: draft\n---\nTeh claim.\n'
    corrected = b'---\ntype: concept\nstatus: draft\n---\nThe claim.\n'
    page_path = '1-wiki/concepts/step4a.md'
    page = tmp_path / page_path
    page.parent.mkdir(parents=True)
    page.write_bytes(corrected)
    report = _report(
        tmp_path,
        result='incomplete',
        rec={
            'content_rollback_preimages': [],
            'infrastructure_failure_pages': [],
        },
        page_preimages={
            page_path: {
                'sha256': hashlib.sha256(original).hexdigest(),
                'bytes_base64': base64.b64encode(original).decode(),
                'status': 'draft',
                'verified_hash': '',
            }
        },
        checkpoint_preimages={
            page_path: {
                'sha256': hashlib.sha256(corrected).hexdigest(),
                'bytes_base64': base64.b64encode(corrected).decode(),
                'status': 'draft',
                'verified_hash': '',
            }
        },
    )
    valid, result = completion.validate_incomplete_rollback(
        report, repo_root=tmp_path
    )
    assert valid is True, result['failures']


def test_preverification_checkpoint_capture_is_exclusive(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_text('---\ntype: concept\nstatus: draft\n---\nClaim.\n')
    output = (
        tmp_path / baseline_capture.BASELINE_DIRECTORY
        / 'audit-run-preverification.json'
    )
    receipt = page_checkpoint.capture_checkpoint(
        output=output,
        repo_root=tmp_path,
        run_id='run',
        warning_baseline_sha256='a' * 64,
    )
    assert receipt['pages'] == 1
    try:
        page_checkpoint.capture_checkpoint(
            output=output,
            repo_root=tmp_path,
            run_id='run',
            warning_baseline_sha256='a' * 64,
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError('checkpoint capture overwrote an existing file')


def _report(
    tmp_path,
    *,
    result='complete',
    pending=0,
    markers_pending=0,
    scanner=None,
    rec=None,
    inherited_cleared='0 of 0',
    frozen_occurrences=None,
    page_preimages=None,
    checkpoint_preimages=None,
):
    scanner_row = {
        'schema_version': 1,
        'row_type': 'scanner',
        'row_id': 'scanner',
        'run_id': 'run',
        'scanner': 'final_lint_post_bookkeeping',
        'target': '1-wiki',
        'relationship_epoch': 'READY(1)',
        'status': 0,
        'result': 'clean',
        'lint_result': 'clean',
        'audit_blocking_count': 0,
        'stdout_json': True,
        'stderr_runtime_error': False,
        'warning_count': 0,
        'carried_warning_count': 0,
        'introduced_warning_count': 0,
        'stale_target_applications': 0,
        'terminal': True,
    }
    if scanner:
        scanner_row.update(scanner)
    reconciliation = {
        'schema_version': 1,
        'row_type': 'reconciliation',
        'row_id': 'reconciliation',
        'run_id': 'run',
        'result': result,
        'pending': pending,
        'planned_pages': 0,
        'terminal_pages': 0,
        'pending_pages': 0,
        'planned_sources': 0,
        'terminal_sources': 0,
        'pending_sources': 0,
        'planned_claims': 0,
        'terminal_claims': 0,
        'pending_claims': 0,
        'planned_bullet_roles': 0,
        'terminal_bullet_roles': 0,
        'pending_bullet_roles': 0,
        'planned_page_readers': 0,
        'terminal_page_readers': 0,
        'pending_page_readers': 0,
        'planned_scanners': 1,
        'terminal_scanners': 1,
        'pending_scanners': 0,
        'planned_status_writes': 0,
        'terminal_status_writes': 0,
        'pending_status_writes': 0,
        'initial_warning_findings': 0,
        'initial_nonmention_warning_fingerprints': 0,
        'initial_mention_groups': 0,
        'expanded_mention_occurrences': 0,
        'zero_match_scanner_defects': 0,
        'introduced_warning_findings': 0,
        'introduced_nonmention_warning_fingerprints': 0,
        'introduced_mention_groups': 0,
        'introduced_mention_occurrences': 0,
        'terminal_nonmention_warning_fingerprints': 0,
        'pending_nonmention_warning_fingerprints': 0,
        'terminal_mention_occurrences': 0,
        'pending_mention_occurrences': 0,
        'warning_fingerprints': [],
        'mention_occurrences': [],
        'suppression_batches': [],
        'suppression_reader_verdicts': [],
        'neutral_page_transactions': [],
        'reader_executions': [],
        'reader_adjudications': [],
        'destructive_correction_reviews': [],
        'content_rollback_preimages': [],
        'infrastructure_failure_pages': [],
    }
    if rec:
        reconciliation.update(rec)
    baseline_path, baseline_sha, context = _write_baseline(
        tmp_path,
        reconciliation,
        frozen_occurrences=frozen_occurrences,
        page_preimages=page_preimages,
    )
    reconciliation['warning_baseline_path'] = baseline_path
    reconciliation['warning_baseline_sha256'] = baseline_sha
    reconciliation['warning_baseline_id'] = 'baseline-run'
    reconciliation['evidence_context_sha256'] = context
    reconciliation.update(
        _write_preverification_checkpoint(
            tmp_path,
            baseline_path=baseline_path,
            baseline_sha=baseline_sha,
            page_preimages=(
                checkpoint_preimages
                if checkpoint_preimages is not None
                else page_preimages
            ),
        )
    )
    reconciliation.update(
        _write_execution_journal(
            tmp_path, executions=[], baseline_sha=baseline_sha
        )
    )
    manifest = {
        'schema_version': 1,
        'row_type': 'manifest',
        'row_id': 'manifest',
        'run_id': 'run',
        'mode': 'partial',
        'relationship_epoch': 'READY(1)',
        'planned_pages': 0,
        'planned_sources': 0,
        'planned_claims': 0,
        'planned_bullet_roles': 0,
        'planned_page_readers': 0,
        'planned_scanners': 1,
        'planned_status_writes': 0,
    }
    rows = '\n'.join(
        json.dumps(row, sort_keys=True)
        for row in (manifest, scanner_row, reconciliation)
    )
    path = tmp_path / 'audit.md'
    path.write_text(
        '---\ntype: audit\nmode: partial\nresult: '
        f'{result}\nledger_schema: 1\npending: {pending}\n'
        f'markers_pending: {markers_pending}\n'
        f'inherited_cleared: "{inherited_cleared}"\n---\n'
        f'{completion.START}\n```jsonl\n{rows}\n```\n{completion.END}\n',
        encoding='utf-8',
    )
    return path


def test_complete_zero_warning_report_passes_both_validators(tmp_path):
    report = _report(tmp_path)
    valid, result = completion.validate(report)
    assert valid is True
    assert result['status'] == 'ok'

    shared_scripts = (
        tmp_path / '.claude/skills/multi-skill/scripts'
    )
    shared_scripts.mkdir(parents=True, exist_ok=True)
    (shared_scripts / 'validate_verification_ledger.py').write_text(
        'import json\nprint(json.dumps({"result":"complete","pending":0}))\n',
        encoding='utf-8',
    )
    (shared_scripts / 'check_wiki.py').write_text(
        CHECKER_BYTES.decode(), encoding='utf-8'
    )
    (tmp_path / '1-wiki').mkdir(exist_ok=True)

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / 'validate_audit_completion.py'),
            str(report),
            '--repo-root',
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_residual_mention_occurrences_block_completion(tmp_path):
    report = _report(
        tmp_path,
        result='incomplete',
        pending=45,
        scanner={
            'status': 1,
            'lint_result': 'blocking',
            'audit_blocking_count': 45,
            'warning_count': 45,
            'carried_warning_count': 45,
        },
        rec={
            'initial_warning_findings': 1,
            'initial_mention_groups': 1,
            'expanded_mention_occurrences': 45,
            'terminal_mention_occurrences': 0,
            'pending_mention_occurrences': 45,
        },
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert 'pending mention occurrences is non-zero' in result['failures']
    assert 'final scanner status is not 0' in result['failures']


def test_live_checker_stderr_blocks_clean_gate():
    live = {'status': 0, 'warning_count': 0, 'stderr': 'runtime warning'}
    assert completion._live_checker_is_clean(live=live) is False
    live['stderr'] = ''
    assert completion._live_checker_is_clean(live=live) is True


def test_full_ledger_gate_requires_silent_parseable_terminal_output():
    clean = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"result":"complete","pending":0}',
        stderr='',
    )
    assert completion._full_ledger_is_clean(
        full=clean, expected_result='complete'
    ) is True
    unconverged = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"result":"unconverged","pending":0}',
        stderr='',
    )
    assert completion._full_ledger_is_clean(
        full=unconverged, expected_result='unconverged'
    ) is True
    assert completion._full_ledger_is_clean(
        full=unconverged, expected_result='complete'
    ) is False
    noisy = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=clean.stdout,
        stderr='runtime warning',
    )
    assert completion._full_ledger_is_clean(
        full=noisy, expected_result='complete'
    ) is False
    malformed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='not json',
        stderr='',
    )
    assert completion._full_ledger_is_clean(
        full=malformed, expected_result='complete'
    ) is False


def test_frontmatter_and_reconciliation_must_match(tmp_path):
    report = _report(tmp_path, rec={'result': 'incomplete'})
    valid, result = completion.validate(report)
    assert valid is False
    assert (
        'frontmatter and reconciliation results do not match'
        in result['failures']
    )


def test_completion_rejects_padded_placeholder_run_id(tmp_path):
    report = _report(
        tmp_path,
        scanner={'run_id': ' ... '},
        rec={'run_id': ' ... '},
    )
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'baseline run ID differs' in str(error)
    else:
        raise AssertionError('placeholder run ID was accepted')


def test_every_native_mention_group_must_expand(tmp_path):
    report = _report(
        tmp_path,
        rec={
            'initial_warning_findings': 1,
            'initial_mention_groups': 1,
            'expanded_mention_occurrences': 0,
        },
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert (
        'initial mention groups were not fully expanded' in result['failures']
    )


def test_pending_markers_and_negative_counts_block_completion(tmp_path):
    report = _report(
        tmp_path,
        markers_pending=1,
        rec={
            'initial_warning_findings': -1,
            'initial_nonmention_warning_fingerprints': -1,
            'initial_mention_groups': 0,
            'expanded_mention_occurrences': 0,
            'introduced_warning_findings': 0,
            'introduced_nonmention_warning_fingerprints': 0,
            'introduced_mention_groups': 0,
            'introduced_mention_occurrences': 0,
            'terminal_nonmention_warning_fingerprints': -1,
            'terminal_mention_occurrences': 0,
        },
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert 'frontmatter markers_pending is non-zero' in result['failures']
    assert 'initial_warning_findings is negative' in result['failures']


def test_occurrence_enumerator_has_native_parity_and_exact_utf8_spans(
    tmp_path,
):
    wiki = tmp_path / '1-wiki'
    wiki.mkdir()
    (wiki / 'index.md').write_text('# Index\n', encoding='utf-8')
    concepts = wiki / 'concepts'
    concepts.mkdir()
    (concepts / 'alpha-page.md').write_text(
        '---\ntype: concept\naliases: [alpha page]\nstatus: draft\n---\n'
        '# Alpha Page\n\n> [!idea]\n> Alpha definition.\n> ^idea\n',
        encoding='utf-8',
    )
    host = concepts / 'host-note.md'
    host.write_text(
        '---\ntype: concept\naliases: [host note]\nstatus: draft\n---\n'
        '# Host Note\n\n> [!idea]\n> Café names alpha page once; '
        'alpha page appears again.\n> ^idea\n\n'
        'Existing [[1-wiki/concepts/alpha-page.md|alpha page]] is masked.\n',
        encoding='utf-8',
    )

    result = enumerator.enumerate_occurrences(checker=checker, wiki_root=wiki)
    assert result['groups'] == [
        {
            'page_path': '1-wiki/concepts/host-note.md',
            'target_stem': 'alpha-page',
            'exact_occurrences': 2,
        }
    ]
    occurrences = result['occurrences']
    assert len(occurrences) == 2
    assert len({row['occurrence_id'] for row in occurrences}) == 2
    host_bytes = host.read_bytes()
    for row in occurrences:
        assert host_bytes[row['start_byte'] : row['end_byte']] == b'alpha page'
        assert row['callout_id'] == 'idea'

    live = completion._run_live_checker(
        checker=REPO_ROOT / '.claude/skills/multi-skill/scripts/check_wiki.py',
        wiki_root=wiki,
    )
    assert live['warning_count'] > 0


def test_suppression_batches_are_maximal_ordered_and_digest_stable():
    rows = [_candidate(number) for number in range(52)]
    context = 'a' * 64
    batches = batcher.build_batches(
        rows=rows, evidence_context_sha256=context
    )
    assert [batch['size'] for batch in batches] == [25, 25, 2]
    assert [
        identity for batch in batches for identity in batch['occurrence_ids']
    ] == [row['occurrence_id'] for row in rows]
    assert batches == batcher.build_batches(
        rows=rows, evidence_context_sha256=context
    )
    expected_input = batcher.expected_input_sha256(
        rows=rows,
        review_kind='generic_suppression',
        evidence_context_sha256=context,
    )
    assert {batch['input_sha256'] for batch in batches} == {expected_input}
    changed = [dict(row) for row in rows]
    changed[-1]['matched_text'] = 'changed'
    changed[-1]['occurrence_id'] = batcher.expected_occurrence_id(
        row=changed[-1]
    )
    assert batcher.expected_input_sha256(
        rows=changed,
        review_kind='generic_suppression',
        evidence_context_sha256=context,
    ) != expected_input


def test_suppression_batch_cli_exposes_full_input_hash(tmp_path):
    rows = [_candidate(number) for number in range(52)]
    input_path = tmp_path / 'candidates.json'
    input_path.write_text(json.dumps(rows), encoding='utf-8')
    context = 'a' * 64
    process = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / 'build_suppression_batches.py'),
            str(input_path),
            '--evidence-context-sha256',
            context,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    payload = json.loads(process.stdout)
    assert payload['input_sha256'] == batcher.expected_input_sha256(
        rows=rows,
        review_kind='generic_suppression',
        evidence_context_sha256=context,
    )
    assert [batch['size'] for batch in payload['batches']] == [25, 25, 2]
    assert {
        batch['input_sha256'] for batch in payload['batches']
    } == {payload['input_sha256']}


def test_suppression_batches_reject_duplicate_occurrence_ids():
    row = _candidate(1)
    rows = [row, dict(row)]
    try:
        batcher.build_batches(rows=rows, evidence_context_sha256='a' * 64)
    except ValueError as error:
        assert 'not unique' in str(error)
    else:
        raise AssertionError('duplicate suppression candidate was accepted')


def test_candidate_rejects_target_path_stem_mismatch():
    row = _candidate(1)
    row['target_path'] = '1-wiki/concepts/wrong-target.md'
    row['occurrence_id'] = batcher.expected_occurrence_id(row=row)
    try:
        batcher.validate_candidate(row=row)
    except ValueError as error:
        assert 'target_path does not match target_stem' in str(error)
    else:
        raise AssertionError('mismatched target path and stem were accepted')


def _candidate(number):
    row = {
        'check_id': 'unlinked_page_mention',
        'page_path': '1-wiki/concepts/host.md',
        'page_preimage_sha256': hashlib.sha256(HOST_BYTES).hexdigest(),
        'target_path': '1-wiki/concepts/target.md',
        'target_stem': 'target',
        'matched_text': 'target',
        'start_byte': number * 7,
        'end_byte': number * 7 + 6,
        'line_sha256': hashlib.sha256(b'target').hexdigest(),
        'callout_id': 'idea',
        'occurrence_ordinal': number + 1,
    }
    row['occurrence_id'] = batcher.expected_occurrence_id(row=row)
    return row


def _warning(number=1, *, origin='initial'):
    resolution = 'required section restored and final scanner is clean'
    row = {
        'schema_version': 1,
        'row_id': f'warning-{number}',
        'run_id': 'run',
        'origin': origin,
        'check_id': 'missing_required_section',
        'page_path': f'1-wiki/concepts/page-{number}.md',
        'target': 'Examples',
        'message_sha256': hashlib.sha256(resolution.encode()).hexdigest(),
        'disposition': 'fixed',
        'resolution': resolution,
        'ignore_entry': None,
        'reader_verdicts': [],
    }
    row['warning_id'] = completion.expected_warning_id(row=row)
    return row


def _occurrence(
    number=0,
    *,
    origin='initial',
    disposition='graph_repair',
    review_kind='none',
):
    candidate = _candidate(number)
    ignore_entry = None
    if disposition in {'accepted_suppression', 'graph_ignore'}:
        ignore_entry = '- {} :: {} :: {}'.format(
            candidate['page_path'],
            candidate['target_stem'],
            candidate['matched_text'],
        )
    return {
        'schema_version': 1,
        'row_id': f'occurrence-{number}',
        'run_id': 'run',
        **candidate,
        'origin': origin,
        'disposition': disposition,
        'review_kind': review_kind,
        'resolution': 'exact occurrence reached its terminal disposition',
        'ignore_entry': ignore_entry,
    }


def _batch_rows(occurrences):
    rows = []
    context = _context_for(occurrences)
    for review_kind in sorted(batcher.REVIEW_KINDS):
        candidates = [
            {key: occurrence[key] for key in batcher.CANDIDATE_FIELDS}
            for occurrence in occurrences
            if occurrence['review_kind'] == review_kind
        ]
        for batch in batcher.build_batches(
            rows=candidates,
            review_kind=review_kind,
            evidence_context_sha256=context,
        ):
            rows.append(
                {
                    'schema_version': 1,
                    'row_id': (f'batch-{review_kind}-{batch["batch_number"]}'),
                    'run_id': 'run',
                    **{
                        key: batch[key]
                        for key in (
                            'review_kind',
                            'evidence_context_sha256',
                            'input_sha256',
                            'batch_number',
                            'batch_digest',
                            'size',
                            'occurrence_ids',
                        )
                    },
                }
            )
    return rows


def _reader_rows(occurrence, batch):
    question = completion.QUESTION_VERSIONS[occurrence['review_kind']]
    return [
        {
            'schema_version': 1,
            'row_id': f'reader-{role}-{occurrence["occurrence_id"][:8]}',
            'run_id': 'run',
            'occurrence_id': occurrence['occurrence_id'],
            'review_kind': occurrence['review_kind'],
            'evidence_context_sha256': batch['evidence_context_sha256'],
            'input_sha256': batch['input_sha256'],
            'batch_number': batch['batch_number'],
            'batch_digest': batch['batch_digest'],
            'reader_role': role,
            'agent_id': agent,
            'reader_run_id': 'run-' + role,
            'blind_to': [other],
            'verdict': 'hold',
            'question_version': question,
            'reasoning': 'host and target context independently support HOLD',
        }
        for role, other, agent in (
            ('reader_a', 'reader_b', 'agent-a'),
            ('reader_b', 'reader_a', 'agent-b'),
        )
    ]


def _worklist_rec(warnings=None, occurrences=None, batches=None, readers=None):
    warnings = warnings or []
    occurrences = occurrences or []
    batches = batches or []
    readers = readers or []
    initial_warnings = [row for row in warnings if row['origin'] == 'initial']
    introduced_warnings = [
        row for row in warnings if row['origin'] == 'introduced'
    ]
    initial_occurrences = [
        row for row in occurrences if row['origin'] == 'initial'
    ]
    introduced_occurrences = [
        row for row in occurrences if row['origin'] == 'introduced'
    ]
    initial_groups = {
        (row['page_path'], row['target_stem']) for row in initial_occurrences
    }
    introduced_groups = {
        (row['page_path'], row['target_stem'])
        for row in introduced_occurrences
    }
    return {
        'initial_warning_findings': len(initial_warnings)
        + len(initial_groups),
        'initial_nonmention_warning_fingerprints': len(initial_warnings),
        'initial_mention_groups': len(initial_groups),
        'expanded_mention_occurrences': len(initial_occurrences),
        'introduced_warning_findings': len(introduced_warnings)
        + len(introduced_groups),
        'introduced_nonmention_warning_fingerprints': len(introduced_warnings),
        'introduced_mention_groups': len(introduced_groups),
        'introduced_mention_occurrences': len(introduced_occurrences),
        'terminal_nonmention_warning_fingerprints': len(warnings),
        'terminal_mention_occurrences': len(occurrences),
        'warning_fingerprints': warnings,
        'mention_occurrences': occurrences,
        'suppression_batches': batches,
        'suppression_reader_verdicts': readers,
        'reader_executions': [],
        'reader_adjudications': [],
        'destructive_correction_reviews': [],
        'content_rollback_preimages': [],
        'infrastructure_failure_pages': [],
    }


def test_counts_alone_cannot_close_warning_or_occurrence_work(tmp_path):
    report = _report(
        tmp_path,
        rec={
            'initial_warning_findings': 700,
            'initial_nonmention_warning_fingerprints': 52,
            'initial_mention_groups': 648,
            'expanded_mention_occurrences': 648,
            'terminal_nonmention_warning_fingerprints': 52,
            'terminal_mention_occurrences': 648,
        },
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert any(
        'does not match exact worklist rows' in failure
        for failure in result['failures']
    )


def test_exact_warning_and_occurrence_terminal_rows_close(tmp_path):
    rec = _worklist_rec(
        warnings=[_warning()],
        occurrences=[_occurrence()],
    )
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is True, result['failures']


def test_vague_source_ignore_requires_two_blind_holds_and_exact_phrase(tmp_path):
    phrase = 'The paper does not measure latency.'
    warning = _warning()
    warning.update({
        'check_id': 'vague_source_referent',
        'page_path': '1-wiki/concepts/page-1.md',
        'target': '',
        'message_sha256': hashlib.sha256(phrase.encode()).hexdigest(),
        'disposition': 'standing_ignore',
        'resolution': phrase,
        'ignore_entry': f'- 1-wiki/concepts/page-1.md :: {phrase}',
        'reader_verdicts': [
            {
                'reader_role': role,
                'agent_id': agent,
                'reader_run_id': run,
                'blind_to': [other],
                'verdict': 'hold',
                'question_version': 'vague-source-ignore-v1',
                'reasoning': 'The phrase is a non-attribution false positive.',
            }
            for role, other, agent, run in (
                ('reader_a', 'reader_b', 'agent-a', 'reader-a-run'),
                ('reader_b', 'reader_a', 'agent-b', 'reader-b-run'),
            )
        ],
    })
    warning['warning_id'] = completion.expected_warning_id(row=warning)
    data = (
        '---\ntype: concept\nstatus: draft\n---\n' + phrase + '\n'
    ).encode()
    page_preimages = {
        warning['page_path']: {
            'sha256': hashlib.sha256(data).hexdigest(),
            'bytes_base64': base64.b64encode(data).decode(),
            'status': 'draft',
            'verified_hash': '',
        }
    }
    rec = _worklist_rec(warnings=[warning])
    valid, result = completion.validate(
        _report(tmp_path, rec=rec, page_preimages=page_preimages)
    )
    assert valid is True, result['failures']
    parsed = checker._load_vague_source_ignore(
        tmp_path / baseline_capture.IGNORE_PATH
    )
    assert [(item['page'], item['phrase']) for item in parsed] == [
        (warning['page_path'], phrase)
    ]

    warning['reader_verdicts'][1]['agent_id'] = 'agent-a'
    valid, result = completion.validate(
        _report(tmp_path, rec=_worklist_rec(warnings=[warning]),
                page_preimages=page_preimages)
    )
    assert valid is False
    assert any('not independent' in failure for failure in result['failures'])

    broad = 'The paper reports latency and the study uses held-out data.'
    warning['reader_verdicts'][1]['agent_id'] = 'agent-b'
    warning['resolution'] = broad
    warning['message_sha256'] = hashlib.sha256(broad.encode()).hexdigest()
    warning['ignore_entry'] = (
        f'- 1-wiki/concepts/page-1.md :: {broad}'
    )
    warning['warning_id'] = completion.expected_warning_id(row=warning)
    broad_bytes = (
        '---\ntype: concept\nstatus: draft\n---\n' + broad + '\n'
    ).encode()
    page_preimages[warning['page_path']] = {
        'sha256': hashlib.sha256(broad_bytes).hexdigest(),
        'bytes_base64': base64.b64encode(broad_bytes).decode(),
        'status': 'draft',
        'verified_hash': '',
    }
    valid, result = completion.validate(
        _report(
            tmp_path,
            rec=_worklist_rec(warnings=[warning]),
            page_preimages=page_preimages,
        )
    )
    assert valid is False
    assert any(
        'does not cover exactly one vague referent' in failure
        for failure in result['failures']
    )


def test_suppression_requires_exact_two_reader_quorum(tmp_path):
    occurrence = _occurrence(
        disposition='accepted_suppression',
        review_kind='generic_suppression',
    )
    batches = _batch_rows([occurrence])
    readers = _reader_rows(occurrence, batches[0])
    rec = _worklist_rec(
        occurrences=[occurrence], batches=batches, readers=readers
    )
    report = _report(tmp_path, rec=rec)
    valid, result = completion.validate(report)
    assert valid is True, result['failures']
    parsed = checker._load_unlinked_mention_ignore(
        tmp_path / baseline_capture.IGNORE_PATH
    )
    assert [
        (entry['page'], entry['target'], entry['phrase']) for entry in parsed
    ] == [
        (
            occurrence['page_path'],
            occurrence['target_stem'],
            occurrence['matched_text'],
        )
    ]

    rec['suppression_reader_verdicts'] = readers[:1]
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is False
    assert any(
        'lacks exactly two reader roles' in failure
        for failure in result['failures']
    )


def test_suppression_rejects_same_agent_and_outcome_leak(tmp_path):
    occurrence = _occurrence(
        disposition='accepted_suppression',
        review_kind='generic_suppression',
    )
    batches = _batch_rows([occurrence])
    readers = _reader_rows(occurrence, batches[0])
    readers[1]['agent_id'] = readers[0]['agent_id']
    readers[1]['verdict'] = 'refute'
    rec = _worklist_rec(
        occurrences=[occurrence], batches=batches, readers=readers
    )
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is False
    assert any('not independent' in failure for failure in result['failures'])
    assert any(
        'split or contains CANNOT_CONFIRM' in failure
        for failure in result['failures']
    )


def test_suppression_entry_cannot_cover_another_occurrence(tmp_path):
    accepted = _occurrence(
        number=0,
        disposition='accepted_suppression',
        review_kind='generic_suppression',
    )
    accepted['ignore_entry'] = (
        '- 1-wiki/concepts/host.md :: target :: target target'
    )
    other = _occurrence(number=1, disposition='graph_repair')
    occurrences = [accepted, other]
    batches = _batch_rows(occurrences)
    readers = _reader_rows(accepted, batches[0])
    rec = _worklist_rec(
        occurrences=occurrences, batches=batches, readers=readers
    )
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is False
    assert 'accepted ignore entry covers another occurrence' in result[
        'failures'
    ]


def test_enumerated_occurrence_cannot_claim_standing_ignore(tmp_path):
    occurrence = _occurrence()
    occurrence['disposition'] = 'standing_ignore'
    rec = _worklist_rec(occurrences=[occurrence])
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is False
    assert any(
        'nonterminal disposition' in failure for failure in result['failures']
    )


def test_inherited_cleared_uses_check_wiki_c_of_i_form(tmp_path):
    valid, result = completion.validate(
        _report(tmp_path, inherited_cleared='1 of 1')
    )
    assert valid is True, result['failures']

    valid, result = completion.validate(
        _report(tmp_path, inherited_cleared='0 of 1')
    )
    assert valid is False
    assert (
        'frontmatter inherited markers are not all cleared'
        in result['failures']
    )

    valid, result = completion.validate(
        _report(tmp_path, inherited_cleared='0')
    )
    assert valid is False
    assert (
        'frontmatter inherited_cleared is not canonical "C of I"'
        in result['failures']
    )


def test_batch_digest_binds_reader_question_kind():
    row = _candidate(1)
    generic = batcher.build_batches(
        rows=[row],
        review_kind='generic_suppression',
        evidence_context_sha256='a' * 64,
    )
    graph = batcher.build_batches(
        rows=[row],
        review_kind='graph_ignore',
        evidence_context_sha256='a' * 64,
    )
    assert generic[0]['batch_digest'] != graph[0]['batch_digest']


def test_suppression_candidate_rejects_coordinator_answer_fields():
    row = _candidate(1)
    row['proposed_verdict'] = 'hold'
    try:
        batcher.build_batches(
            rows=[row], evidence_context_sha256='a' * 64
        )
    except ValueError as error:
        assert 'unexpected fields' in str(error)
    else:
        raise AssertionError('coordinator answer leaked into reader slate')


def test_occurrence_id_binds_check_id_and_target_path():
    row = _candidate(1)
    original = row['occurrence_id']
    changed_check = dict(row, check_id='different_check')
    changed_target = dict(row, target_path='1-wiki/concepts/other.md')
    assert batcher.expected_occurrence_id(changed_check) != original
    assert batcher.expected_occurrence_id(changed_target) != original


def test_suppression_batches_reject_truncated_candidate():
    row = _candidate(1)
    del row['page_preimage_sha256']
    try:
        batcher.build_batches(
            rows=[row], evidence_context_sha256='a' * 64
        )
    except ValueError as error:
        assert 'missing identity fields' in str(error)
    else:
        raise AssertionError('truncated suppression candidate was accepted')


def test_suppression_batches_reject_reordered_candidates():
    rows = [_candidate(2), _candidate(1)]
    try:
        batcher.build_batches(
            rows=rows, evidence_context_sha256='a' * 64
        )
    except ValueError as error:
        assert 'canonical occurrence-ledger order' in str(error)
    else:
        raise AssertionError('reordered suppression candidates were accepted')


def test_ledger_block_and_fence_must_be_unique_and_line_anchored(tmp_path):
    report = _report(tmp_path)
    report.write_text(
        report.read_text(encoding='utf-8')
        + '\n{}\n'.format(completion.START),
        encoding='utf-8',
    )
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'exactly one ledger marker pair' in str(error)
    else:
        raise AssertionError('duplicate ledger marker was accepted')


def test_warning_baseline_capture_is_exclusive_and_complete(tmp_path):
    subprocess.run(
        ['git', 'init', str(tmp_path)],
        capture_output=True,
        check=True,
    )
    for relative in baseline_capture.CANONICAL_RULE_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(RULE_BYTES)
    for relative in baseline_capture.RELATIONSHIP_RULE_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(RELATIONSHIP_BYTES)
    ignore = tmp_path / baseline_capture.IGNORE_PATH
    ignore.parent.mkdir(parents=True, exist_ok=True)
    ignore.write_bytes(IGNORE_BYTES)
    (tmp_path / '1-wiki/concepts').mkdir(parents=True)
    checker_path = tmp_path / baseline_capture.CANONICAL_CHECKER_PATH
    checker_path.parent.mkdir(parents=True, exist_ok=True)
    checker_path.write_bytes(CHECKER_BYTES)
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            'add',
            baseline_capture.CANONICAL_CHECKER_PATH,
            baseline_capture.IGNORE_PATH,
        ],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            '-c',
            'user.name=Audit Test',
            '-c',
            'user.email=audit-test',
            'commit',
            '-m',
            'fixture',
        ],
        capture_output=True,
        check=True,
    )
    output = (
        tmp_path / baseline_capture.BASELINE_DIRECTORY / 'baseline.json'
    )
    result = baseline_capture.capture_baseline(
        output=output,
        repo_root=tmp_path,
        checker_path=checker_path,
        run_id='run',
    )
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert result['sha256'] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert payload['checker']['findings'] == []
    assert payload['enumerator']['occurrences'] == []
    assert payload['affected_page_preimages'] == {}
    assert payload['ignore_file']['bytes_base64'] == base64.b64encode(
        IGNORE_BYTES
    ).decode()
    captured_status = base64.b64decode(
        payload['git_pre_edit']['status_bytes_base64']
    )
    assert b'2-outputs/audit/baselines/baseline.json' not in captured_status
    assert set(payload['canonical_rule_hashes']) == set(
        baseline_capture.CANONICAL_RULE_PATHS
    )
    assert set(payload['relationship_rule_hashes']) == set(
        baseline_capture.RELATIONSHIP_RULE_PATHS
    )
    try:
        baseline_capture.capture_baseline(
            output=output,
            repo_root=tmp_path,
            checker_path=checker_path,
            run_id='run',
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError('baseline capture replaced an existing artifact')

    dirty_ignore = IGNORE_BYTES + b'dirty pre-capture entry\n'
    ignore.write_bytes(dirty_ignore)
    dirty_output = output.with_name('dirty-input.json')
    baseline_capture.capture_baseline(
        output=dirty_output,
        repo_root=tmp_path,
        checker_path=checker_path,
        run_id='run',
    )
    dirty_payload = json.loads(dirty_output.read_text(encoding='utf-8'))
    assert base64.b64decode(
        dirty_payload['ignore_file']['bytes_base64']
    ) == dirty_ignore

    checker_path.write_bytes(CHECKER_BYTES + b'# dirty checker\n')
    try:
        baseline_capture.capture_baseline(
            output=output.with_name('dirty-checker.json'),
            repo_root=tmp_path,
            checker_path=checker_path,
            run_id='run',
        )
    except RuntimeError as error:
        assert 'dirty protected inputs' in str(error)
    else:
        raise AssertionError('dirty canonical checker produced a baseline')


def test_warning_baseline_capture_rejects_failed_checker_exit(tmp_path):
    checker = tmp_path / 'failed_checker.py'
    checker.write_text(
        'import sys\nprint("[]")\nsys.exit(2)\n', encoding='utf-8'
    )
    try:
        baseline_capture._run_checker(checker=checker, wiki_root=tmp_path)
    except RuntimeError as error:
        assert 'failed with exit 2' in str(error)
    else:
        raise AssertionError('failed checker run was accepted as a baseline')


def test_warning_baseline_capture_rejects_noncanonical_checker(tmp_path):
    checker = tmp_path / 'custom_checker.py'
    checker.write_bytes(CHECKER_BYTES)
    output = tmp_path / baseline_capture.BASELINE_DIRECTORY / 'baseline.json'
    try:
        baseline_capture.capture_baseline(
            output=output,
            repo_root=tmp_path,
            checker_path=checker,
            run_id='run',
        )
    except ValueError as error:
        assert 'canonical checker' in str(error)
    else:
        raise AssertionError('noncanonical checker produced a baseline')


def test_report_rejects_baseline_tampering_and_rule_drift(tmp_path):
    report = _report(tmp_path)
    baseline = (
        tmp_path / baseline_capture.BASELINE_DIRECTORY / 'baseline.json'
    )
    baseline.write_bytes(baseline.read_bytes() + b' ')
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'SHA-256 does not match' in str(error)
    else:
        raise AssertionError('tampered baseline artifact was accepted')

    report = _report(tmp_path)
    rule = tmp_path / baseline_capture.CANONICAL_RULE_PATHS[0]
    rule.write_text('changed\n', encoding='utf-8')
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'evidence context changed' in str(error)
    else:
        raise AssertionError('canonical-rule drift was accepted')


def test_completion_rejects_blocking_initial_checker_status(tmp_path):
    report = _report(tmp_path)
    baseline = (
        tmp_path / baseline_capture.BASELINE_DIRECTORY / 'baseline.json'
    )
    payload = json.loads(baseline.read_text(encoding='utf-8'))
    payload['checker']['status'] = 1
    data = json.dumps(
        payload, sort_keys=True, separators=(',', ':')
    ).encode() + b'\n'
    baseline.write_bytes(data)
    report.write_text(
        report.read_text(encoding='utf-8').replace(
            hashlib.sha256(
                json.dumps(
                    dict(payload, checker=dict(payload['checker'], status=0)),
                    sort_keys=True,
                    separators=(',', ':'),
                ).encode()
                + b'\n'
            ).hexdigest(),
            hashlib.sha256(data).hexdigest(),
        ),
        encoding='utf-8',
    )
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'canonical checker' in str(error)
    else:
        raise AssertionError('blocking initial checker status was accepted')


def test_report_rejects_noncanonical_baseline_path_and_checker_drift(tmp_path):
    report = _report(tmp_path)
    report.write_text(
        report.read_text(encoding='utf-8').replace(
            '2-outputs/audit/baselines/baseline.json', 'baseline.json'
        ),
        encoding='utf-8',
    )
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'canonical baseline directory' in str(error)
    else:
        raise AssertionError('noncanonical baseline path was accepted')

    report = _report(tmp_path)
    checker_path = tmp_path / baseline_capture.CANONICAL_CHECKER_PATH
    checker_path.write_bytes(CHECKER_BYTES + b'# drift\n')
    try:
        completion.validate(report)
    except ValueError as error:
        assert 'canonical checker' in str(error)
    else:
        raise AssertionError('canonical-checker drift was accepted')


def test_unaccounted_ignore_addition_blocks_completion(tmp_path):
    report = _report(tmp_path)
    ignore = tmp_path / baseline_capture.IGNORE_PATH
    ignore.write_text(
        ignore.read_text(encoding='utf-8')
        + '1-wiki/concepts/x.md :: target :: unreviewed phrase\n',
        encoding='utf-8',
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert 'ignore file contains unaccounted additions' in result['failures']


def test_removed_frozen_ignore_entry_blocks_completion(tmp_path):
    report = _report(tmp_path)
    (tmp_path / baseline_capture.IGNORE_PATH).write_bytes(b'')
    valid, result = completion.validate(report)
    assert valid is False
    assert (
        'ignore file removed a frozen standing-ignore entry'
        in result['failures']
    )


def test_needs_update_is_a_terminal_nonmention_disposition(tmp_path):
    warning = _warning()
    warning['disposition'] = 'needs_update'
    rec = _worklist_rec(warnings=[warning])
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is True, result['failures']


def test_unconverged_is_a_terminal_completion_result(tmp_path):
    valid, result = completion.validate(
        _report(tmp_path, result='unconverged')
    )
    assert valid is True, result['failures']


def _neutral_wrap_fixture(tmp_path, status='verified'):
    body_before = (
        '# Host\n\n> [!idea]\n> - A target appears here.\n> ^idea\n'
    )
    body_after = body_before.replace(
        'target', '[[1-wiki/concepts/target.md|target]]'
    )
    before_hash = hashlib.sha256(body_before.encode()).hexdigest()
    after_hash = hashlib.sha256(body_after.encode()).hexdigest()
    before_stamp = (
        'verified_hash: {}\n'.format(before_hash)
        if status == 'verified'
        else ''
    )
    after_stamp = (
        'verified_hash: {}\n'.format(after_hash)
        if status == 'verified'
        else ''
    )
    preimage = (
        '---\ntype: concept\nstatus: {}\nupdated: 2026-08-01\n'
        '{}---\n{}'.format(status, before_stamp, body_before)
    ).encode()
    retained = (
        '---\ntype: concept\nstatus: {}\nupdated: 2026-08-05\n'
        '{}---\n{}'.format(status, after_stamp, body_after)
    ).encode()
    page_path = '1-wiki/concepts/host.md'
    target_path = '1-wiki/concepts/target.md'
    start = preimage.index(b'target')
    end = start + len(b'target')
    line_start = preimage.rfind(b'\n', 0, start) + 1
    line_end = preimage.find(b'\n', end)
    candidate = {
        'check_id': 'unlinked_page_mention',
        'page_path': page_path,
        'page_preimage_sha256': hashlib.sha256(preimage).hexdigest(),
        'target_path': target_path,
        'target_stem': 'target',
        'matched_text': 'target',
        'start_byte': start,
        'end_byte': end,
        'line_sha256': hashlib.sha256(
            preimage[line_start:line_end]
        ).hexdigest(),
        'callout_id': 'idea',
        'occurrence_ordinal': 1,
    }
    candidate['occurrence_id'] = batcher.expected_occurrence_id(row=candidate)
    occurrence = {
        'schema_version': 1,
        'row_id': 'neutral-occurrence',
        'run_id': 'run',
        **candidate,
        'origin': 'initial',
        'disposition': 'genuine_wrap',
        'review_kind': 'none',
        'resolution': 'replayed exact frozen span',
        'ignore_entry': None,
    }
    transaction = {
        'schema_version': 1,
        'row_id': 'neutral-page-host',
        'run_id': 'run',
        'page_path': page_path,
        'preimage_sha256': hashlib.sha256(preimage).hexdigest(),
        'postimage_sha256': hashlib.sha256(retained).hexdigest(),
        'postimage_bytes_base64': base64.b64encode(retained).decode(),
        'before_status': status,
        'after_status': status,
        'verified_hash': after_hash if status == 'verified' else None,
        'baseline_occurrence_ids': [candidate['occurrence_id']],
    }
    host = tmp_path / page_path
    host.parent.mkdir(parents=True, exist_ok=True)
    host.write_bytes(retained)
    rec = _worklist_rec(occurrences=[occurrence])
    rec['neutral_page_transactions'] = [transaction]
    preimages = {
        page_path: {
            'sha256': hashlib.sha256(preimage).hexdigest(),
            'bytes_base64': base64.b64encode(preimage).decode(),
            'status': status,
            'verified_hash': before_hash if status == 'verified' else '',
        }
    }
    return occurrence, candidate, rec, preimages


def test_verified_genuine_wrap_requires_executable_neutral_transaction(
    tmp_path,
):
    occurrence, candidate, rec, preimages = _neutral_wrap_fixture(tmp_path)
    report = _report(
        tmp_path,
        rec=rec,
        frozen_occurrences=[candidate],
        page_preimages=preimages,
    )
    valid, result = completion.validate(report)
    assert valid is True, result['failures']

    rec_without_transaction = dict(rec, neutral_page_transactions=[])
    missing_report = _report(
        tmp_path,
        rec=rec_without_transaction,
        frozen_occurrences=[candidate],
        page_preimages=preimages,
    )
    valid, result = completion.validate(missing_report)
    assert valid is False
    assert any(
        'transaction inventory is incomplete' in failure
        for failure in result['failures']
    )

    report = _report(
        tmp_path,
        rec=rec,
        frozen_occurrences=[candidate],
        page_preimages=preimages,
    )

    host = tmp_path / occurrence['page_path']
    host.write_text(
        host.read_text(encoding='utf-8').replace(
            'appears here', 'changes meaning here'
        ),
        encoding='utf-8',
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert any(
        'neutral-only final page differs' in failure
        for failure in result['failures']
    )


def test_baseline_rejects_duplicate_physical_occurrence_span(tmp_path):
    _, candidate, rec, preimages = _neutral_wrap_fixture(tmp_path)
    duplicate = dict(candidate)
    duplicate['occurrence_ordinal'] = 2
    duplicate['occurrence_id'] = batcher.expected_occurrence_id(row=duplicate)
    rec['initial_mention_groups'] = 1
    rec['expanded_mention_occurrences'] = 2
    rec['terminal_mention_occurrences'] = 2
    try:
        completion.validate(
            _report(
                tmp_path,
                rec=rec,
                frozen_occurrences=[candidate, duplicate],
                page_preimages=preimages,
            )
        )
    except ValueError as error:
        assert 'occurrence span is duplicated' in str(error)
    else:
        raise AssertionError('duplicate physical occurrence span was accepted')


def test_draft_and_needs_update_genuine_wraps_require_transactions(tmp_path):
    for status in ('draft', 'needs-update'):
        case = tmp_path / status
        case.mkdir()
        occurrence, candidate, rec, preimages = _neutral_wrap_fixture(
            case, status=status
        )
        report = _report(
            case,
            rec=rec,
            frozen_occurrences=[candidate],
            page_preimages=preimages,
        )
        valid, result = completion.validate(report)
        assert valid is True, (status, result['failures'])
        assert rec['neutral_page_transactions'][0]['verified_hash'] is None
        missing = dict(rec, neutral_page_transactions=[])
        valid, result = completion.validate(
            _report(
                case,
                rec=missing,
                frozen_occurrences=[candidate],
                page_preimages=preimages,
            )
        )
        assert valid is False
        assert any(
            'transaction inventory is incomplete' in failure
            for failure in result['failures']
        )


def test_verified_neutral_host_can_also_be_a_reviewed_target(tmp_path):
    neutral, neutral_candidate, neutral_rec, preimages = (
        _neutral_wrap_fixture(tmp_path)
    )
    reviewed = _occurrence(
        number=20,
        disposition='accepted_suppression',
        review_kind='generic_suppression',
    )
    reviewed.update(
        {
            'row_id': 'reviewed-host-target',
            'page_path': '1-wiki/concepts/reviewer.md',
            'target_path': neutral['page_path'],
            'target_stem': 'host',
            'occurrence_ordinal': 1,
        }
    )
    reviewed['occurrence_id'] = batcher.expected_occurrence_id(row=reviewed)
    reviewed['ignore_entry'] = '- {} :: {} :: {}'.format(
        reviewed['page_path'], reviewed['target_stem'], reviewed['matched_text']
    )
    target_hashes = {
        neutral['target_path']: hashlib.sha256(TARGET_BYTES).hexdigest(),
        neutral['page_path']: preimages[neutral['page_path']]['sha256'],
    }
    context_payload = {
        'canonical_rule_hashes': {
            path: hashlib.sha256(RULE_BYTES).hexdigest()
            for path in baseline_capture.CANONICAL_RULE_PATHS
        },
        'relationship_rule_hashes': {
            path: hashlib.sha256(RELATIONSHIP_BYTES).hexdigest()
            for path in baseline_capture.RELATIONSHIP_RULE_PATHS
        },
        'target_page_hashes': target_hashes,
        'initial_ignore_sha256': hashlib.sha256(IGNORE_BYTES).hexdigest(),
    }
    context = hashlib.sha256(
        json.dumps(
            context_payload, sort_keys=True, separators=(',', ':')
        ).encode()
    ).hexdigest()
    candidate = {
        key: reviewed[key] for key in batcher.CANDIDATE_FIELDS
    }
    generated = batcher.build_batches(
        rows=[candidate], evidence_context_sha256=context
    )[0]
    batch = {
        'schema_version': 1,
        'row_id': 'batch-reviewed-host',
        'run_id': 'run',
        **{
            key: generated[key]
            for key in (
                'review_kind',
                'evidence_context_sha256',
                'input_sha256',
                'batch_number',
                'batch_digest',
                'size',
                'occurrence_ids',
            )
        },
    }
    readers = _reader_rows(reviewed, batch)
    rec = _worklist_rec(
        occurrences=[neutral, reviewed],
        batches=[batch],
        readers=readers,
    )
    rec['neutral_page_transactions'] = neutral_rec[
        'neutral_page_transactions'
    ]
    frozen = [
        neutral_candidate,
        {key: reviewed[key] for key in batcher.CANDIDATE_FIELDS},
    ]
    report = _report(
        tmp_path,
        rec=rec,
        frozen_occurrences=frozen,
        page_preimages=preimages,
    )
    valid, result = completion.validate(report)
    assert valid is True, result['failures']


def test_rekeyed_occurrence_closes_one_frozen_identity_once(tmp_path):
    body = '# Host\n\n> [!idea]\n> - alpha then beta.\n> ^idea\n'
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    preimage = (
        '---\ntype: concept\nstatus: verified\n'
        'verified_hash: {}\n---\n{}'.format(body_hash, body)
    ).encode()

    def frozen_candidate(matched, target):
        start = preimage.index(matched.encode())
        end = start + len(matched.encode())
        line_start = preimage.rfind(b'\n', 0, start) + 1
        line_end = preimage.find(b'\n', end)
        row = {
            'check_id': 'unlinked_page_mention',
            'page_path': '1-wiki/concepts/host.md',
            'page_preimage_sha256': hashlib.sha256(preimage).hexdigest(),
            'target_path': '1-wiki/concepts/{}.md'.format(target),
            'target_stem': target,
            'matched_text': matched,
            'start_byte': start,
            'end_byte': end,
            'line_sha256': hashlib.sha256(
                preimage[line_start:line_end]
            ).hexdigest(),
            'callout_id': 'idea',
            'occurrence_ordinal': 1,
        }
        row['occurrence_id'] = batcher.expected_occurrence_id(row=row)
        return row

    alpha = frozen_candidate('alpha', 'alpha')
    beta = frozen_candidate('beta', 'beta')
    linked = b'[[1-wiki/concepts/alpha.md|alpha]]'
    postimage = (
        preimage[: alpha['start_byte']]
        + linked
        + preimage[alpha['end_byte'] :]
    )
    post_body = completion._frontmatter_and_body(postimage)[1]
    post_hash = hashlib.sha256(post_body).hexdigest()
    postimage = postimage.replace(body_hash.encode(), post_hash.encode(), 1)
    shifted = dict(beta)
    shifted['page_preimage_sha256'] = hashlib.sha256(postimage).hexdigest()
    delta = len(linked) - len(b'alpha')
    shifted['start_byte'] += delta
    shifted['end_byte'] += delta
    line_start = postimage.rfind(b'\n', 0, shifted['start_byte']) + 1
    line_end = postimage.find(b'\n', shifted['end_byte'])
    shifted['line_sha256'] = hashlib.sha256(
        postimage[line_start:line_end]
    ).hexdigest()
    shifted['occurrence_id'] = batcher.expected_occurrence_id(row=shifted)
    alpha_terminal = {
        'schema_version': 1,
        'row_id': 'alpha-occurrence',
        'run_id': 'run',
        **alpha,
        'origin': 'initial',
        'disposition': 'genuine_wrap',
        'review_kind': 'none',
        'resolution': 'exact alpha wrap',
        'ignore_entry': None,
    }
    superseded = {
        'schema_version': 1,
        'row_id': 'superseded-occurrence',
        'run_id': 'run',
        **beta,
        'origin': 'initial',
        'disposition': 'superseded',
        'review_kind': 'none',
        'resolution': 'old exact identity superseded after page-local edit',
        'ignore_entry': None,
        'rekeyed_to': shifted['occurrence_id'],
    }
    rekeyed = {
        'schema_version': 1,
        'row_id': 'rekeyed-occurrence',
        'run_id': 'run',
        **shifted,
        'origin': 'initial',
        'disposition': 'rekeyed',
        'review_kind': 'none',
        'resolution': 'new exact identity terminally adjudicated',
        'ignore_entry': None,
        'rekeyed_from': beta['occurrence_id'],
        'final_disposition': 'graph_repair',
    }
    transaction = {
        'schema_version': 1,
        'row_id': 'neutral-rekey-page',
        'run_id': 'run',
        'page_path': alpha['page_path'],
        'preimage_sha256': hashlib.sha256(preimage).hexdigest(),
        'postimage_sha256': hashlib.sha256(postimage).hexdigest(),
        'postimage_bytes_base64': base64.b64encode(postimage).decode(),
        'before_status': 'verified',
        'after_status': 'verified',
        'verified_hash': post_hash,
        'baseline_occurrence_ids': [alpha['occurrence_id']],
    }
    host = tmp_path / alpha['page_path']
    host.parent.mkdir(parents=True, exist_ok=True)
    host.write_bytes(postimage)
    rec = _worklist_rec(
        occurrences=[alpha_terminal, superseded, rekeyed]
    )
    rec['expanded_mention_occurrences'] = 2
    rec['terminal_mention_occurrences'] = 2
    rec['neutral_page_transactions'] = [transaction]
    preimages = {
        alpha['page_path']: {
            'sha256': hashlib.sha256(preimage).hexdigest(),
            'bytes_base64': base64.b64encode(preimage).decode(),
            'status': 'verified',
            'verified_hash': body_hash,
        }
    }
    report = _report(
        tmp_path,
        rec=rec,
        frozen_occurrences=[alpha, beta],
        page_preimages=preimages,
    )
    valid, result = completion.validate(report)
    assert valid is True, result['failures']

    rec_without_transaction = dict(rec, neutral_page_transactions=[])
    report = _report(
        tmp_path,
        rec=rec_without_transaction,
        frozen_occurrences=[alpha, beta],
        page_preimages=preimages,
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert any(
        'rekeyed occurrence preimage lacks one proven transaction postimage'
        in failure
        for failure in result['failures']
    )

    duplicate = dict(rekeyed, row_id='duplicate-rekey')
    rec = _worklist_rec(
        occurrences=[alpha_terminal, superseded, rekeyed, duplicate]
    )
    rec['expanded_mention_occurrences'] = 2
    rec['terminal_mention_occurrences'] = 2
    rec['neutral_page_transactions'] = [transaction]
    report = _report(
        tmp_path,
        rec=rec,
        frozen_occurrences=[alpha, beta],
        page_preimages=preimages,
    )
    valid, result = completion.validate(report)
    assert valid is False
    assert any(
        'duplicate occurrence_id' in failure
        or 'reciprocal' in failure
        for failure in result['failures']
    )


def test_suppression_evidence_binds_context_and_reader_run(tmp_path):
    occurrence = _occurrence(
        disposition='accepted_suppression',
        review_kind='generic_suppression',
    )
    batches = _batch_rows([occurrence])
    readers = _reader_rows(occurrence, batches[0])
    readers[0]['evidence_context_sha256'] = 'f' * 64
    readers[1]['reader_run_id'] = '...'
    rec = _worklist_rec(
        occurrences=[occurrence], batches=batches, readers=readers
    )
    valid, result = completion.validate(_report(tmp_path, rec=rec))
    assert valid is False
    assert any('exact batch' in failure for failure in result['failures'])
    assert any('invalid reader_run_id' in failure for failure in result['failures'])


def test_648_suppression_candidates_form_maximal_batches():
    rows = [_candidate(number) for number in range(648)]
    batches = batcher.build_batches(
        rows=rows, evidence_context_sha256='a' * 64
    )
    assert len(batches) == 26
    assert [batch['size'] for batch in batches] == [25] * 25 + [23]
    expected_input = batcher.expected_input_sha256(
        rows=rows,
        review_kind='generic_suppression',
        evidence_context_sha256='a' * 64,
    )
    assert {batch['input_sha256'] for batch in batches} == {expected_input}


def test_reviewed_target_edit_requires_an_exact_neutral_transaction(tmp_path):
    target_path = '1-wiki/concepts/target.md'
    before = b'before target bytes'
    after = b'after target bytes'
    target = tmp_path / target_path
    target.parent.mkdir(parents=True)
    target.write_bytes(after)
    occurrence = _occurrence(
        disposition='accepted_suppression',
        review_kind='generic_suppression',
    )
    baseline = {
        'target_page_hashes': {
            target_path: hashlib.sha256(before).hexdigest()
        }
    }
    transaction = {
        'page_path': target_path,
        'preimage_sha256': hashlib.sha256(before).hexdigest(),
        'postimage_sha256': hashlib.sha256(after).hexdigest(),
    }
    assert completion._validate_review_target_context(
        root=tmp_path,
        baseline=baseline,
        occurrence_rows=[occurrence],
        transaction_rows=[transaction],
    ) == []
    assert completion._validate_review_target_context(
        root=tmp_path,
        baseline=baseline,
        occurrence_rows=[occurrence],
        transaction_rows=[],
    ) == ['suppression reader target bytes differ from frozen context']
