import hashlib
import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / 'validate_verification_ledger.py'
SPEC = importlib.util.spec_from_file_location('ledger', SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ledger)


def claim_row(text='> - A claim.', ordinal=1, locators=None):
    row = {
        'schema_version': 1,
        'row_type': 'claim',
        'row_id': 'claim-row',
        'run_id': 'run',
        'page_path': '1-wiki/concepts/example.md',
        'page_type': 'concept',
        'page_title': 'Example',
        'semantic_frontmatter': {'sources': ['Example2026']},
        'callout_type': 'idea',
        'callout_id': 'idea',
        'duplicate_ordinal': ordinal,
        'claim_text': text,
        'claim_bytes': len(text.encode('utf-8')),
        'locators': locators or [],
        'raw_dependencies': [],
        'context_digest': 'a' * 64,
        'classification': 'required',
    }
    row['claim_instance_id'] = ledger.expected_claim_id(row)
    return row


def test_unverified_marker_does_not_change_identity():
    marked = claim_row('> - *[unverified]* A claim.')
    clear = claim_row('> -  A claim.')
    assert marked['claim_instance_id'] == clear['claim_instance_id']


def test_tentative_marker_changes_identity():
    marked = claim_row('> - *[tentative]* A claim.')
    clear = claim_row('> - A claim.')
    assert marked['claim_instance_id'] != clear['claim_instance_id']


def test_long_claim_is_not_truncated():
    text = '> - ' + ('x' * 500) + ' decisive subject'
    row = claim_row(text)
    assert row['claim_bytes'] > 400
    assert ledger.claim_identity_payload(row)['claim_text_canonical'].endswith(
        'decisive subject'
    )


def test_duplicate_ordinal_changes_identity():
    assert (
        claim_row(ordinal=1)['claim_instance_id']
        != claim_row(ordinal=2)['claim_instance_id']
    )


def test_locator_order_changes_identity():
    a = {'raw_path': '0-raw/a.pdf', 'physical_page': 1}
    b = {'raw_path': '0-raw/b.pdf', 'physical_page': 2}
    assert (
        claim_row(locators=[a, b])['claim_instance_id']
        != claim_row(locators=[b, a])['claim_instance_id']
    )


def test_invalid_jsonl_is_rejected():
    text = (
        '---\nresult: incomplete\n---\n'
        f'{ledger.START}\n```jsonl\n{{bad\n```\n{ledger.END}\n'
    )
    try:
        ledger.parse_rows(text)
    except ledger.LedgerError:
        pass
    else:
        raise AssertionError('invalid JSONL was accepted')


def test_complete_requires_zero_pending(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_text('# Example\n', encoding='utf-8')
    claim = claim_row()
    claim_id = claim['claim_instance_id']
    rows = [
        {
            'schema_version': 1,
            'row_type': 'manifest',
            'row_id': 'manifest',
            'run_id': 'run',
            'planned_pages': 1,
            'planned_sources': 0,
            'planned_claims': 1,
            'planned_bullet_roles': 2,
            'planned_page_readers': 0,
            'planned_scanners': 0,
            'planned_status_writes': 0,
        },
        claim,
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': 'loc',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'role': 'locator_bullet',
            'agent_id': 'a',
            'verdict': 'hold',
            'quote': 'q',
            'quote_raw_path': 'raw.txt',
        },
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': 'ent',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'role': 'entailment_bullet',
            'agent_id': 'b',
            'verdict': 'hold',
            'quote': 'q',
            'quote_raw_path': 'raw.txt',
        },
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'term',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'disposition': 'backfilled_hold',
        },
        {
            'schema_version': 1,
            'row_type': 'reconciliation',
            'row_id': 'rec',
            'run_id': 'run',
            'result': 'complete',
            'pending': 1,
            'planned_pages': 1,
            'terminal_pages': 1,
            'pending_pages': 0,
            'planned_sources': 0,
            'terminal_sources': 0,
            'pending_sources': 0,
            'planned_claims': 1,
            'terminal_claims': 1,
            'pending_claims': 0,
            'planned_bullet_roles': 2,
            'terminal_bullet_roles': 2,
            'pending_bullet_roles': 0,
            'planned_page_readers': 0,
            'terminal_page_readers': 0,
            'pending_page_readers': 0,
            'planned_scanners': 0,
            'terminal_scanners': 0,
            'pending_scanners': 0,
            'planned_status_writes': 0,
            'terminal_status_writes': 0,
            'pending_status_writes': 0,
        },
    ]
    report = tmp_path / 'report.md'
    body = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 1\n---\n'
        f'{ledger.START}\n```jsonl\n{body}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as exc:
        assert 'pending' in str(exc)
    else:
        raise AssertionError('complete report with pending work was accepted')


def test_duplicate_group_ordinals_must_be_contiguous():
    first = claim_row(ordinal=1)
    third = claim_row(ordinal=3)
    try:
        ledger.validate_duplicate_ordinals(
            {
                first['claim_instance_id']: first,
                third['claim_instance_id']: third,
            }
        )
    except ledger.LedgerError as exc:
        assert 'contiguous' in str(exc)
    else:
        raise AssertionError('non-contiguous duplicate ordinals were accepted')


def test_reused_pair_requires_role_versions(tmp_path):
    terminal = {
        'producer_report': 'producer.md',
        'producer_blob': 'a' * 40,
        'reused_role_rows': ['locator', 'entailment'],
    }
    try:
        ledger.validate_reused_pair(
            tmp_path,
            'claim-id',
            terminal,
            recheck_quotes=False,
        )
    except ledger.LedgerError as exc:
        assert 'role versions' in str(exc)
    else:
        raise AssertionError('reused pair without role versions was accepted')


def test_minimal_complete_report_validates(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_text('# Example\n', encoding='utf-8')
    raw = tmp_path / '0-raw/example.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('A supporting quote.\n', encoding='utf-8')
    claim = claim_row()
    claim['raw_dependencies'] = [
        {
            'raw_path': '0-raw/example.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
        }
    ]
    claim['claim_instance_id'] = ledger.expected_claim_id(claim)
    claim_id = claim['claim_instance_id']
    rows = [
        {
            'schema_version': 1,
            'row_type': 'manifest',
            'row_id': 'manifest',
            'run_id': 'run',
            'planned_pages': 1,
            'planned_sources': 1,
            'planned_claims': 1,
            'planned_bullet_roles': 2,
            'planned_page_readers': 0,
            'planned_scanners': 0,
            'planned_status_writes': 0,
        },
        claim,
        *[
            {
                'schema_version': 1,
                'row_type': 'bullet_verdict',
                'row_id': role,
                'run_id': 'run',
                'claim_instance_id': claim_id,
                'role': role,
                'agent_id': agent,
                'verdict': 'hold',
                'quote': 'A supporting quote.',
                'quote_raw_path': '0-raw/example.txt',
                'physical_page': None,
            }
            for role, agent in (
                ('locator_bullet', 'locator-agent'),
                ('entailment_bullet', 'entailment-agent'),
            )
        ],
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'terminal',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'disposition': 'backfilled_hold',
        },
        {
            'schema_version': 1,
            'row_type': 'reconciliation',
            'row_id': 'reconciliation',
            'run_id': 'run',
            'result': 'complete',
            'pending': 0,
            'planned_pages': 1,
            'terminal_pages': 1,
            'pending_pages': 0,
            'planned_sources': 1,
            'terminal_sources': 1,
            'pending_sources': 0,
            'planned_claims': 1,
            'terminal_claims': 1,
            'pending_claims': 0,
            'planned_bullet_roles': 2,
            'terminal_bullet_roles': 2,
            'pending_bullet_roles': 0,
            'planned_page_readers': 0,
            'terminal_page_readers': 0,
            'pending_page_readers': 0,
            'planned_scanners': 0,
            'terminal_scanners': 0,
            'pending_scanners': 0,
            'planned_status_writes': 0,
            'terminal_status_writes': 0,
            'pending_status_writes': 0,
        },
    ]
    report = tmp_path / 'report.md'
    body = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{body}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    summary = ledger.validate(report, tmp_path, recheck_quotes=True)
    assert summary == {
        'result': 'complete',
        'rows': 6,
        'claims': 1,
        'page_generations': 0,
        'pending': 0,
    }
