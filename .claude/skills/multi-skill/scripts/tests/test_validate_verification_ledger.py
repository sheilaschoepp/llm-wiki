import base64
import hashlib
import importlib.util
import json
import os
import re
import subprocess
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
    clear = claim_row('> - A claim.')
    assert marked['claim_instance_id'] == clear['claim_instance_id']


def test_fenced_marker_literal_is_not_counted_or_stripped():
    text = '```markdown\n> - *[unverified]* example\n```\n'
    assert ledger.count_process_markers(text=text) == 0
    assert ledger.strip_process_marker(text=text) == text


def test_html_comments_are_ignored_by_markers_and_claim_inventory(tmp_path):
    text = (
        '<!--\n*[unverified]*\n> [!idea]\n> - Hidden claim.\n'
        '> ^hidden\n-->\n'
    )
    page = tmp_path / 'page.md'
    page.write_text(text, encoding='utf-8')
    assert ledger.count_process_markers(text=text) == 0
    assert ledger.strip_process_marker(text=text) == text
    assert ledger.extract_claim_records(page=page) == []


def test_trailing_html_comment_preserves_visible_claim(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '> [!idea]\n> - Visible claim. <!-- internal note -->\n> ^idea\n',
        encoding='utf-8',
    )
    assert ledger.extract_claim_records(page=page) == [
        {
            'claim_text': '> - Visible claim. ',
            'callout_type': 'idea',
            'callout_id': 'idea',
        }
    ]


def test_backticks_in_info_string_do_not_open_a_fence(tmp_path):
    text = (
        '```literal```\n'
        '> [!idea]\n'
        '> - *[unverified]* Pending.\n'
        '> ^idea\n'
    )
    page = tmp_path / 'page.md'
    page.write_text(text, encoding='utf-8')
    assert ledger.count_process_markers(text=text) == 1
    assert '*[unverified]*' not in ledger.strip_process_marker(text=text)
    assert [
        row['claim_text'] for row in ledger.extract_claim_records(page=page)
    ] == ['> - *[unverified]* Pending.']


def test_tentative_marker_changes_identity():
    marked = claim_row('> - *[tentative]* A claim.')
    clear = claim_row('> - A claim.')
    assert marked['claim_instance_id'] != clear['claim_instance_id']


def test_inline_code_marker_literal_remains_semantic(tmp_path):
    literal = claim_row('> - A `*[unverified]*` claim.')
    changed = claim_row('> - A `` claim.')
    assert literal['claim_instance_id'] != changed['claim_instance_id']

    page = tmp_path / 'page.md'
    page.write_text('> - A `*[unverified]*` claim.\n', encoding='utf-8')
    before = ledger.semantic_page_digest(page=page)
    page.write_text('> - A `` claim.\n', encoding='utf-8')
    assert ledger.semantic_page_digest(page=page) != before


def test_fenced_code_marker_literal_remains_semantic(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '```text\n> - *[unverified]* literal example\n```\n',
        encoding='utf-8',
    )
    before = ledger.semantic_page_digest(page=page)
    page.write_text(
        '```text\n> - literal example\n```\n',
        encoding='utf-8',
    )
    assert ledger.semantic_page_digest(page=page) != before


def test_blockquoted_fenced_marker_literal_remains_semantic(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '> ```markdown\n> - *[unverified]* literal example\n> ```\n',
        encoding='utf-8',
    )
    before = ledger.semantic_page_digest(page=page)
    page.write_text(
        '> ```markdown\n> - literal example\n> ```\n',
        encoding='utf-8',
    )
    assert ledger.semantic_page_digest(page=page) != before


def test_fence_like_content_does_not_close_code_block(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '```markdown\n```not-a-closing-fence\n'
        '> - *[unverified]* literal example\n```\n',
        encoding='utf-8',
    )
    before = ledger.semantic_page_digest(page=page)
    page.write_text(
        '```markdown\n```not-a-closing-fence\n'
        '> - literal example\n```\n',
        encoding='utf-8',
    )
    assert ledger.semantic_page_digest(page=page) != before


def test_different_blockquote_container_does_not_close_fence(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '```markdown\n> ``` \n> - *[unverified]* literal example\n```\n',
        encoding='utf-8',
    )
    before = ledger.semantic_page_digest(page=page)
    page.write_text(
        '```markdown\n> ``` \n> - literal example\n```\n',
        encoding='utf-8',
    )
    assert ledger.semantic_page_digest(page=page) != before


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


def test_boolean_claim_ordinal_is_rejected():
    row = claim_row(ordinal=1)
    row['duplicate_ordinal'] = True
    try:
        ledger.validate_duplicate_ordinals({row['claim_instance_id']: row})
    except ledger.LedgerError as exc:
        assert 'invalid duplicate ordinal' in str(exc)
    else:
        raise AssertionError('boolean duplicate ordinal was accepted')


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


def test_ledger_boundaries_must_be_complete_lines():
    row = json.dumps(claim_row(), sort_keys=True)
    cases = (
        f'prefix {ledger.START}\n```jsonl\n{row}\n```\n{ledger.END}\n',
        f'{ledger.START}\n```jsonl\n{row}\n```\nsuffix {ledger.END}\n',
    )
    for text in cases:
        try:
            ledger.parse_rows(text)
        except ledger.LedgerError as error:
            assert 'boundary' in str(error)
        else:
            raise AssertionError('inline ledger boundary was accepted')


def test_duplicate_ledger_blocks_and_fences_are_rejected():
    row = json.dumps(claim_row(), sort_keys=True)
    ledger_block = (
        f'{ledger.START}\n```jsonl\n{row}\n```\n{ledger.END}\n'
    )
    for text in (
        ledger_block + ledger_block,
        (
            f'{ledger.START}\n```jsonl\n{row}\n```\n'
            f'```jsonl\n{row}\n```\n{ledger.END}\n'
        ),
    ):
        try:
            ledger.parse_rows(text)
        except ledger.LedgerError as error:
            assert 'exactly one' in str(error)
        else:
            raise AssertionError('duplicate ledger proof was accepted')


def test_json_string_fence_text_does_not_close_ledger():
    row = claim_row(
        '> - Example:\n> ```python\n> value = 1\n> ```'
    )
    text = (
        '---\nresult: incomplete\n---\n'
        f'{ledger.START}\n```jsonl\n'
        f'{json.dumps(row, sort_keys=True)}\n'
        f'```\n{ledger.END}\n'
    )
    assert ledger.parse_rows(text)[0]['claim_text'] == row['claim_text']


def test_boolean_schema_version_is_rejected(tmp_path):
    rows = _audit_rows(tmp_path)
    rows[0]['schema_version'] = True
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'schema_version 1' in str(error)
    else:
        raise AssertionError('Boolean schema version was accepted as 1')


def test_complete_requires_zero_pending(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_text(
        '# Example\n\n> [!idea]\n> - A claim.\n> ^idea\n',
        encoding='utf-8',
    )
    raw = tmp_path / '0-raw/raw.txt'
    raw.parent.mkdir()
    raw.write_text('## Evidence\nq\n', encoding='utf-8')
    claim = claim_row(
        locators=[
            {'raw_path': '0-raw/raw.txt', 'structural_anchor': 'Evidence'}
        ]
    )
    claim['raw_dependencies'] = [
        {
            'raw_path': '0-raw/raw.txt',
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
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': 'loc',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'role': 'locator_bullet',
            'role_version': '1',
            'agent_id': 'a',
            'blind_to': ['entailment_bullet'],
            'verdict': 'hold',
            'quote': 'q',
            'quote_raw_path': '0-raw/raw.txt',
            'structural_anchor': 'Evidence',
            'reasoning': 'The located quote supports the claim.',
            'confidence': 'high',
            'correction': None,
            'quote_validated': True,
        },
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': 'ent',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'role': 'entailment_bullet',
            'role_version': '1',
            'agent_id': 'b',
            'blind_to': ['locator_bullet'],
            'verdict': 'hold',
            'quote': 'q',
            'quote_raw_path': '0-raw/raw.txt',
            'structural_anchor': 'Evidence',
            'reasoning': 'The quote entails the claim.',
            'confidence': 'high',
            'correction': None,
            'quote_validated': True,
        },
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'term',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'disposition': 'backfilled_hold',
            'role_rows': ['loc', 'ent'],
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


def test_duplicate_ordinals_must_follow_body_encounter_order():
    second = claim_row(ordinal=2)
    first = claim_row(ordinal=1)
    try:
        ledger.validate_duplicate_ordinals(
            {
                second['claim_instance_id']: second,
                first['claim_instance_id']: first,
            }
        )
    except ledger.LedgerError as error:
        assert 'body order' in str(error)
    else:
        raise AssertionError('sorted but reversed duplicate ordinals passed')


def test_reused_pair_requires_role_versions(tmp_path):
    terminal = {
        'producer_report': '2-outputs/audit/producer.md',
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

    terminal['role_versions'] = {
        'locator_bullet': None,
        'entailment_bullet': None,
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
        raise AssertionError('null reused role versions were accepted')


def test_reused_pair_restricts_producer_path_and_report_type(tmp_path):
    terminal = {
        'producer_report': '2-outputs/other/producer.md',
        'producer_blob': 'a' * 40,
        'reused_role_rows': ['locator', 'entailment'],
        'role_versions': {
            'locator_bullet': '1',
            'entailment_bullet': '1',
        },
    }
    try:
        ledger.validate_reused_pair(
            tmp_path, 'claim-id', terminal, recheck_quotes=False
        )
    except ledger.LedgerError as error:
        assert 'outside audit/ingest outputs' in str(error)
    else:
        raise AssertionError('producer outside canonical outputs was accepted')

    report = tmp_path / '2-outputs/audit/producer.md'
    report.parent.mkdir(parents=True)
    manifest = {
        'schema_version': 1,
        'row_type': 'manifest',
        'row_id': 'manifest',
        'run_id': 'run',
        **{
            f'planned_{prefix}': 0
            for prefix in ledger.RECONCILIATION_UNITS
        },
    }
    reconciliation = {
        'schema_version': 1,
        'row_type': 'reconciliation',
        'row_id': 'reconciliation',
        'run_id': 'run',
        'result': 'complete',
        'pending': 0,
    }
    for prefix in ledger.RECONCILIATION_UNITS:
        reconciliation[f'planned_{prefix}'] = 0
        reconciliation[f'terminal_{prefix}'] = 0
        reconciliation[f'pending_{prefix}'] = 0
    rows = '\n'.join(
        json.dumps(row, sort_keys=True)
        for row in (manifest, reconciliation)
    )
    report.write_text(
        '---\ntype: unrelated-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{rows}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.email', 'audit-test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'producer'], check=True
    )
    terminal['producer_report'] = '2-outputs/audit/producer.md'
    terminal['producer_blob'] = ledger.run_git(
        tmp_path, ['rev-parse', 'HEAD:2-outputs/audit/producer.md']
    )
    try:
        ledger.validate_reused_pair(
            tmp_path, 'claim-id', terminal, recheck_quotes=False
        )
    except ledger.LedgerError as error:
        assert 'producer report is not terminal' in str(error)
    else:
        raise AssertionError('producer with an unrelated report type passed')


def test_exact_reused_claim_survives_unrelated_producer_rows(tmp_path):
    raw = tmp_path / '0-raw/evidence.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('## Evidence\nSupporting quote.\n', encoding='utf-8')
    target = claim_row(
        locators=[
            {
                'raw_path': '0-raw/evidence.txt',
                'structural_anchor': 'Evidence',
            }
        ]
    )
    target['run_id'] = 'producer-run'
    target['raw_dependencies'] = [
        {
            'raw_path': '0-raw/evidence.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
        }
    ]
    target['claim_instance_id'] = ledger.expected_claim_id(target)
    claim_id = target['claim_instance_id']
    unrelated = claim_row(text='> - Unrelated producer claim.')
    unrelated['row_id'] = 'unrelated-claim'
    unrelated['run_id'] = 'producer-run'
    unrelated['classification'] = 'exempt'
    unrelated['exemption_reason'] = 'obvious_definitional'
    unrelated['claim_instance_id'] = ledger.expected_claim_id(unrelated)
    manifest = {
        'schema_version': 1,
        'row_type': 'manifest',
        'row_id': 'manifest',
        'run_id': 'producer-run',
        'planned_pages': 1,
        'planned_sources': 1,
        'planned_claims': 2,
        'planned_bullet_roles': 2,
        'planned_page_readers': 0,
        'planned_scanners': 0,
        'planned_status_writes': 0,
    }
    roles = [
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': role,
            'run_id': 'producer-run',
            'claim_instance_id': claim_id,
            'role': role,
            'role_version': '1',
            'agent_id': agent,
            'blind_to': [ledger.BULLET_COUNTERPART[role]],
            'verdict': 'hold',
            'quote': 'Supporting quote.',
            'quote_raw_path': '0-raw/evidence.txt',
            'structural_anchor': 'Evidence',
            'reasoning': 'The exact located evidence supports the claim.',
            'confidence': 'high',
            'correction': None,
            'quote_validated': True,
        }
        for role, agent in (
            ('locator_bullet', 'locator-agent'),
            ('entailment_bullet', 'entailment-agent'),
        )
    ]
    rows = [
        manifest,
        target,
        unrelated,
        *roles,
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'target-terminal',
            'run_id': 'producer-run',
            'claim_instance_id': claim_id,
            'disposition': 'backfilled_hold',
            'role_rows': ['locator_bullet', 'entailment_bullet'],
        },
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'unrelated-terminal',
            'run_id': 'producer-run',
            'claim_instance_id': unrelated['claim_instance_id'],
            'disposition': 'exempt',
        },
        {
            'schema_version': 1,
            'row_type': 'source',
            'row_id': 'source-evidence',
            'run_id': 'producer-run',
            'raw_path': '0-raw/evidence.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
            'disposition': 'available',
            'evidence': 'Current raw was opened and digest-bound.',
        },
    ]
    reconciliation = {
        'schema_version': 1,
        'row_type': 'reconciliation',
        'row_id': 'reconciliation',
        'run_id': 'producer-run',
        'result': 'complete',
        'pending': 0,
    }
    terminal_counts = {
        'pages': 1,
        'sources': 1,
        'claims': 2,
        'bullet_roles': 2,
        'page_readers': 0,
        'scanners': 0,
        'status_writes': 0,
    }
    for prefix in ledger.RECONCILIATION_UNITS:
        reconciliation[f'planned_{prefix}'] = manifest[f'planned_{prefix}']
        reconciliation[f'terminal_{prefix}'] = terminal_counts[prefix]
        reconciliation[f'pending_{prefix}'] = 0
    rows.append(reconciliation)
    report = tmp_path / '2-outputs/ingest/producer.md'
    report.parent.mkdir(parents=True)

    def write_producer(producer_rows, frontmatter=None):
        payload = '\n'.join(
            json.dumps(row, sort_keys=True) for row in producer_rows
        )
        report.write_text(
            (
                frontmatter
                or '---\ntype: ingest-report\nresult: complete\n'
                'ledger_schema: 1\npending: 0\n---\n'
            )
            + f'{ledger.START}\n```jsonl\n{payload}\n```\n{ledger.END}\n',
            encoding='utf-8',
        )

    write_producer(rows)
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.email', 'audit-test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'producer'], check=True
    )
    terminal = {
        'producer_report': '2-outputs/ingest/producer.md',
        'producer_blob': ledger.run_git(
            tmp_path, ['rev-parse', 'HEAD:2-outputs/ingest/producer.md']
        ),
        'reused_role_rows': ['locator_bullet', 'entailment_bullet'],
        'role_versions': {
            'locator_bullet': '1',
            'entailment_bullet': '1',
        },
    }
    ledger.validate_reused_pair(
        tmp_path, claim_id, terminal, recheck_quotes=True
    )

    no_source = [row for row in rows if row.get('row_type') != 'source']
    write_producer(no_source)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'drop source'],
        check=True,
    )
    terminal['producer_blob'] = ledger.run_git(
        tmp_path, ['rev-parse', 'HEAD:2-outputs/ingest/producer.md']
    )
    try:
        ledger.validate_reused_pair(
            tmp_path, claim_id, terminal, recheck_quotes=False
        )
    except ledger.LedgerError as error:
        assert 'source' in str(error)
    else:
        raise AssertionError('producer reuse passed without its source row')

    manifest['mode'] = 'partial'
    manifest['relationship_epoch'] = 'READY(2)'
    for role in roles:
        role['relationship_epoch'] = 'READY(2)'
    audit_frontmatter = (
        '---\ntype: audit\nmode: partial\nresult: complete\n'
        'ledger_schema: 1\npending: 0\n---\n'
    )
    write_producer(rows, frontmatter=audit_frontmatter)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'wrong folder type'],
        check=True,
    )
    terminal['producer_blob'] = ledger.run_git(
        tmp_path, ['rev-parse', 'HEAD:2-outputs/ingest/producer.md']
    )
    try:
        ledger.validate_reused_pair(
            tmp_path, claim_id, terminal, recheck_quotes=False
        )
    except ledger.LedgerError as error:
        assert 'producer' in str(error)
    else:
        raise AssertionError('audit producer passed from the ingest folder')

    report = tmp_path / '2-outputs/audit/producer.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    manifest['mode'] = 'full'
    write_producer(rows, frontmatter=audit_frontmatter)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'bad audit mode'],
        check=True,
    )
    terminal['producer_report'] = '2-outputs/audit/producer.md'
    terminal['producer_blob'] = ledger.run_git(
        tmp_path, ['rev-parse', 'HEAD:2-outputs/audit/producer.md']
    )
    try:
        ledger.validate_reused_pair(
            tmp_path, claim_id, terminal, recheck_quotes=False
        )
    except ledger.LedgerError as error:
        assert 'mode' in str(error) or 'epoch' in str(error)
    else:
        raise AssertionError('audit producer mode mismatch was accepted')

    manifest['mode'] = 'partial'
    manifest['relationship_epoch'] = 'READY(?)'
    write_producer(rows, frontmatter=audit_frontmatter)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'bad audit epoch'],
        check=True,
    )
    terminal['producer_blob'] = ledger.run_git(
        tmp_path, ['rev-parse', 'HEAD:2-outputs/audit/producer.md']
    )
    try:
        ledger.validate_reused_pair(
            tmp_path, claim_id, terminal, recheck_quotes=False
        )
    except ledger.LedgerError as error:
        assert 'epoch' in str(error) or 'READY' in str(error)
    else:
        raise AssertionError('audit producer without READY epoch was accepted')


def test_terminal_reconciliation_result_and_counts_must_balance():
    frontmatter = {'result': 'complete', 'pending': '0'}
    manifest = {
        'schema_version': 1,
        'row_id': 'manifest',
        'run_id': 'run',
        **{
            f'planned_{prefix}': 0
            for prefix in ledger.RECONCILIATION_UNITS
        },
    }
    reconciliation = {
        'schema_version': 1,
        'row_id': 'reconciliation',
        'run_id': 'run',
        'result': 'incomplete',
        'pending': 0,
    }
    for prefix in ledger.RECONCILIATION_UNITS:
        reconciliation[f'planned_{prefix}'] = 0
        reconciliation[f'terminal_{prefix}'] = 0
        reconciliation[f'pending_{prefix}'] = 0
    try:
        ledger.validate_terminal_reconciliation(
            frontmatter=frontmatter,
            reconciliation=reconciliation,
            manifest=manifest,
            label='producer',
        )
    except ledger.LedgerError as error:
        assert 'reconciliation is not terminal' in str(error)
    else:
        raise AssertionError('mismatched producer reconciliation was accepted')

    reconciliation['result'] = 'complete'
    reconciliation['planned_claims'] = 2
    reconciliation['terminal_claims'] = 1
    try:
        ledger.validate_terminal_reconciliation(
            frontmatter=frontmatter,
            reconciliation=reconciliation,
            manifest=manifest,
            label='producer',
        )
    except ledger.LedgerError as error:
        assert 'reconciliation mismatches claims' in str(error)
    else:
        raise AssertionError('unbalanced producer counts were accepted')


def test_conflicting_committed_terminal_report_invalidates_reuse(tmp_path):
    raw = tmp_path / '0-raw/evidence.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text(
        '## Evidence\nThe claim is contradicted.\n', encoding='utf-8'
    )
    claim = claim_row(
        locators=[
            {
                'raw_path': '0-raw/evidence.txt',
                'structural_anchor': 'Evidence',
            }
        ]
    )
    claim['raw_dependencies'] = [
        {
            'raw_path': '0-raw/evidence.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
        }
    ]
    claim['claim_instance_id'] = ledger.expected_claim_id(claim)
    claim_id = claim['claim_instance_id']
    manifest = {
        'schema_version': 1,
        'row_type': 'manifest',
        'row_id': 'manifest',
        'run_id': 'conflict-run',
        **{
            f'planned_{prefix}': (
                1 if prefix in {'pages', 'claims'} else 0
            )
            for prefix in ledger.RECONCILIATION_UNITS
        },
        'planned_bullet_roles': 2,
    }
    manifest['planned_sources'] = 1
    claim['run_id'] = 'conflict-run'
    rows = [
        manifest,
        claim,
        *[
            {
                'schema_version': 1,
                'row_type': 'bullet_verdict',
                'row_id': role,
                'run_id': 'conflict-run',
                'claim_instance_id': claim_id,
                'role': role,
                'role_version': '1',
                'agent_id': agent,
                'blind_to': [ledger.BULLET_COUNTERPART[role]],
                'verdict': verdict,
                'quote': 'The claim is contradicted.',
                'quote_raw_path': '0-raw/evidence.txt',
                'structural_anchor': 'Evidence',
                'reasoning': 'The claim is not supported.',
                'confidence': 'high',
                'correction': None,
            }
            for role, agent, verdict in (
                ('locator_bullet', 'locator', 'refute'),
                ('entailment_bullet', 'entailment', 'refute'),
            )
        ],
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'terminal',
            'run_id': 'conflict-run',
            'claim_instance_id': claim_id,
            'disposition': 'refute',
            'role_rows': ['locator_bullet', 'entailment_bullet'],
        },
        {
            'schema_version': 1,
            'row_type': 'source',
            'row_id': 'source-evidence',
            'run_id': 'conflict-run',
            'raw_path': '0-raw/evidence.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
            'disposition': 'available',
            'evidence': 'Current raw was opened for the conflict verdict.',
        },
    ]
    reconciliation = {
        'schema_version': 1,
        'row_type': 'reconciliation',
        'row_id': 'reconciliation',
        'run_id': 'conflict-run',
        'result': 'complete',
        'pending': 0,
    }
    terminal_counts = {
        'pages': 1,
        'sources': 1,
        'claims': 1,
        'bullet_roles': 2,
        'page_readers': 0,
        'scanners': 0,
        'status_writes': 0,
    }
    for prefix in ledger.RECONCILIATION_UNITS:
        reconciliation[f'planned_{prefix}'] = manifest[f'planned_{prefix}']
        reconciliation[f'terminal_{prefix}'] = terminal_counts[prefix]
        reconciliation[f'pending_{prefix}'] = 0
    rows.append(reconciliation)
    report = tmp_path / '2-outputs/ingest/conflict.md'
    report.parent.mkdir(parents=True)
    payload = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{payload}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.email', 'audit-test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'conflict'], check=True
    )
    assert ledger.conflicting_terminal_reports(
        repo_root=tmp_path,
        claim_id=claim_id,
        producer_report='2-outputs/audit/producer.md',
    ) == ['2-outputs/ingest/conflict.md']

    report.write_text(
        report.read_text(encoding='utf-8') + '\n', encoding='utf-8'
    )
    assert ledger.conflicting_terminal_reports(
        repo_root=tmp_path,
        claim_id=claim_id,
        producer_report='2-outputs/audit/producer.md',
    ) == ['2-outputs/ingest/conflict.md']

    unlocated_rows = json.loads(json.dumps(rows))
    for row in unlocated_rows:
        if row.get('row_type') == 'bullet_verdict':
            row.pop('quote')
            row.pop('quote_raw_path')
            row.pop('structural_anchor')
    unlocated_payload = '\n'.join(
        json.dumps(row, sort_keys=True) for row in unlocated_rows
    )
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{unlocated_payload}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'unlocated'], check=True
    )
    assert ledger.conflicting_terminal_reports(
        repo_root=tmp_path,
        claim_id=claim_id,
        producer_report='2-outputs/audit/producer.md',
    ) == []

    malformed_variants = []
    placeholder = json.loads(json.dumps(rows))
    next(row for row in placeholder if row['row_type'] == 'manifest')[
        'run_id'
    ] = ' ... '
    malformed_variants.append(('placeholder run', placeholder))
    bad_schema = json.loads(json.dumps(rows))
    next(
        row for row in bad_schema if row['row_type'] == 'bullet_verdict'
    )['schema_version'] = True
    malformed_variants.append(('bad schema', bad_schema))
    stale_run = json.loads(json.dumps(rows))
    next(
        row for row in stale_run if row['row_type'] == 'bullet_verdict'
    )['run_id'] = 'other-run'
    malformed_variants.append(('stale run', stale_run))
    for label, variant in malformed_variants:
        variant_payload = '\n'.join(
            json.dumps(row, sort_keys=True) for row in variant
        )
        report.write_text(
            '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
            'pending: 0\n---\n'
            f'{ledger.START}\n```jsonl\n{variant_payload}\n```\n'
            f'{ledger.END}\n',
            encoding='utf-8',
        )
        subprocess.run(
            ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
        )
        subprocess.run(
            ['git', '-C', str(tmp_path), 'commit', '-qm', label], check=True
        )
        assert ledger.conflicting_terminal_reports(
            repo_root=tmp_path,
            claim_id=claim_id,
            producer_report='2-outputs/audit/producer.md',
        ) == []

    source_less = [
        row for row in rows if row.get('row_type') != 'source'
    ]
    source_less_payload = '\n'.join(
        json.dumps(row, sort_keys=True) for row in source_less
    )
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{source_less_payload}\n```\n'
        f'{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'missing source'],
        check=True,
    )
    assert ledger.conflicting_terminal_reports(
        repo_root=tmp_path,
        claim_id=claim_id,
        producer_report='2-outputs/audit/producer.md',
    ) == []

    unbound_rows = [
        row for row in rows if row.get('row_type') != 'bullet_verdict'
    ]
    unbound_payload = '\n'.join(
        json.dumps(row, sort_keys=True) for row in unbound_rows
    )
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{unbound_payload}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'unbound'],
        check=True,
    )
    assert ledger.conflicting_terminal_reports(
        repo_root=tmp_path,
        claim_id=claim_id,
        producer_report='2-outputs/audit/producer.md',
    ) == []

    malformed_rows = [
        row for row in rows if row.get('row_type') != 'claim_terminal'
    ]
    malformed_payload = '\n'.join(
        json.dumps(row, sort_keys=True) for row in malformed_rows
    )
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{malformed_payload}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'malformed'],
        check=True,
    )
    assert ledger.conflicting_terminal_reports(
        repo_root=tmp_path,
        claim_id=claim_id,
        producer_report='2-outputs/audit/producer.md',
    ) == []


def test_hold_quote_must_match_exact_locator_coordinates():
    claim = claim_row(
        locators=[
            {
                'raw_path': '0-raw/evidence.txt',
                'physical_page': 1,
                'printed_page': 7,
                'structural_anchor': 'Locator section',
            }
        ]
    )
    claim['raw_dependencies'] = [
        {'raw_path': '0-raw/evidence.txt', 'sha256': 'a' * 64}
    ]
    role_rows = [
        {
            'row_id': 'locator',
            'verdict': 'hold',
            'quote': 'Evidence.',
            'quote_raw_path': '0-raw/evidence.txt',
            'physical_page': 2,
            'printed_page': 8,
            'structural_anchor': 'Other section',
        }
    ]
    try:
        ledger.validate_hold_raw_binding(
            claim_id='claim', claim=claim, role_rows=role_rows
        )
    except ledger.LedgerError as error:
        assert 'lacks exact structural locator' in str(error)
    else:
        raise AssertionError('HOLD from a different locator was accepted')


def test_claim_locator_cannot_contradict_authored_raw_anchor():
    text = (
        '> - Supported by '
        '[[0-raw/evidence.txt#section-a|section A]].'
    )
    claim = claim_row(
        text=text,
        locators=[
            {
                'raw_path': '0-raw/evidence.txt',
                'structural_anchor': 'section-b',
            }
        ],
    )
    try:
        ledger.validate_authored_locator_binding(
            claim_id='claim',
            claim_text=claim['claim_text'],
            locators=claim['locators'],
        )
    except ledger.LedgerError as error:
        assert 'does not match authored raw wikilink' in str(error)
    else:
        raise AssertionError('ledger accepted a contradictory raw anchor')


def test_claim_locator_matches_authored_raw_page_fragment():
    claim = claim_row(
        text='> - Supported by [[0-raw/evidence.pdf#page=5|p. 5]].',
        locators=[
            {
                'raw_path': '0-raw/evidence.pdf',
                'physical_page': 5,
                'printed_page': 5,
            }
        ],
    )
    ledger.validate_authored_locator_binding(
        claim_id='claim',
        claim_text=claim['claim_text'],
        locators=claim['locators'],
    )


def test_claim_printed_locator_must_match_display_and_pagination_map(tmp_path):
    claim = claim_row(
        text='> - Supported by [[0-raw/evidence.pdf#page=5|p. 5]].',
        locators=[
            {
                'raw_path': '0-raw/evidence.pdf',
                'physical_page': 5,
                'printed_page': 4,
            }
        ],
    )
    try:
        ledger.validate_authored_locator_binding(
            claim_id='claim',
            claim_text=claim['claim_text'],
            locators=claim['locators'],
        )
    except ledger.LedgerError as error:
        assert 'printed locator differs from authored display' in str(error)
    else:
        raise AssertionError('printed locator contradicted authored display')

    pagination = (
        tmp_path / '.claude/skills/multi-skill/pagination-map.md'
    )
    pagination.parent.mkdir(parents=True)
    pagination.write_text(
        '## 0-raw/evidence.pdf\n- 5 = 4\n', encoding='utf-8'
    )
    claim['locators'][0]['printed_page'] = 5
    try:
        ledger.validate_authored_locator_binding(
            claim_id='claim',
            claim_text=claim['claim_text'],
            locators=claim['locators'],
            repo_root=tmp_path,
        )
    except ledger.LedgerError as error:
        assert 'contradicts authoritative pagination map' in str(error)
    else:
        raise AssertionError('printed locator contradicted pagination map')


def test_registered_pdf_pagination_fails_closed_without_authored_link(
    tmp_path,
):
    pagination = (
        tmp_path / '.claude/skills/multi-skill/pagination-map.md'
    )
    pagination.parent.mkdir(parents=True)
    pagination.write_text(
        '## 0-raw/evidence.pdf\n- 1 = 7\n- 3 = 9\n',
        encoding='utf-8',
    )
    for locator, expected in (
        (
            {
                'raw_path': '0-raw/evidence.pdf',
                'physical_page': 2,
                'printed_page': 8,
            },
            'physical pages absent from pagination map',
        ),
        (
            {
                'raw_path': '0-raw/evidence.pdf',
                'physical_page': 3,
                'printed_page': 8,
            },
            'contradicts authoritative pagination map',
        ),
    ):
        try:
            ledger.validate_authored_locator_binding(
                claim_id='claim',
                claim_text='> - Claim without an authored raw wikilink.',
                locators=[locator],
                repo_root=tmp_path,
            )
        except ledger.LedgerError as error:
            assert expected in str(error)
        else:
            raise AssertionError(
                'registered PDF escaped authoritative pagination binding'
            )


def test_unregistered_pdf_cannot_assert_printed_pagination(tmp_path):
    try:
        ledger.validate_pagination_coordinates(
            repo_root=tmp_path,
            row={
                'raw_path': '0-raw/evidence.pdf',
                'physical_page': 4,
                'printed_page': 1,
            },
            label='claim locator',
        )
    except ledger.LedgerError as error:
        assert 'unregistered PDF' in str(error)
    else:
        raise AssertionError('unregistered PDF invented printed pagination')


def test_authored_single_page_fragment_cannot_widen_to_range():
    claim = claim_row(
        text='> - Supported by [[0-raw/evidence.pdf#page=5|p. 5]].',
        locators=[
            {
                'raw_path': '0-raw/evidence.pdf',
                'physical_page_start': 5,
                'physical_page_end': 10,
            }
        ],
    )
    try:
        ledger.validate_authored_locator_binding(
            claim_id='claim',
            claim_text=claim['claim_text'],
            locators=claim['locators'],
        )
    except ledger.LedgerError as error:
        assert 'does not match authored raw wikilink' in str(error)
    else:
        raise AssertionError('authored single page widened into range')


def test_pdf_page_and_range_coordinates_are_mutually_exclusive():
    row = {
        'physical_page': 2,
        'physical_page_start': 10,
        'physical_page_end': 12,
    }
    try:
        ledger.physical_page_span(row, label='verdict', required=True)
    except ledger.LedgerError as error:
        assert 'mixes physical page and range' in str(error)
    else:
        raise AssertionError('PDF verdict mixed single page and range')


def test_pdf_range_coordinates_are_complete_and_ordered():
    for row in (
        {'physical_page_start': 10},
        {'physical_page_end': 12},
        {'physical_page_start': 12, 'physical_page_end': 10},
        {'physical_page': True},
    ):
        try:
            ledger.physical_page_span(row, label='verdict', required=True)
        except ledger.LedgerError:
            pass
        else:
            raise AssertionError(f'invalid PDF coordinates passed: {row!r}')


def test_claim_locator_order_matches_authored_raw_links():
    claim = claim_row(
        text=(
            '> - Compare [[0-raw/evidence.pdf#page=5|p. 5]] with '
            '[[0-raw/evidence.pdf#page=6|p. 6]].'
        ),
        locators=[
            {'raw_path': '0-raw/evidence.pdf', 'physical_page': 6},
            {'raw_path': '0-raw/evidence.pdf', 'physical_page': 5},
        ],
    )
    try:
        ledger.validate_authored_locator_binding(
            claim_id='claim',
            claim_text=claim['claim_text'],
            locators=claim['locators'],
        )
    except ledger.LedgerError as error:
        assert 'locator order differs' in str(error)
    else:
        raise AssertionError('ledger accepted reversed authored locators')


def test_non_pdf_quote_is_bounded_to_structural_anchor(tmp_path):
    raw = tmp_path / '0-raw/evidence.md'
    raw.parent.mkdir(parents=True)
    raw.write_text(
        '## Section A\nEvidence A.\n\n## Section B\nEvidence B.\n',
        encoding='utf-8',
    )
    row = {
        'row_id': 'locator',
        'verdict': 'hold',
        'quote': 'Evidence B.',
        'quote_raw_path': '0-raw/evidence.md',
        'structural_anchor': 'section-a',
    }
    try:
        ledger.validate_quote(tmp_path, row)
    except ledger.LedgerError as error:
        assert 'does not occur at attributed raw page' in str(error)
    else:
        raise AssertionError('quote from another text section was accepted')


def test_non_pdf_section_extraction_ignores_indented_code_heading(tmp_path):
    raw = tmp_path / '0-raw/evidence.md'
    raw.parent.mkdir(parents=True)
    raw.write_text(
        '    ## Section A\n    Fake quote.\n',
        encoding='utf-8',
    )
    row = {
        'row_id': 'locator',
        'verdict': 'hold',
        'quote': 'Fake quote.',
        'quote_raw_path': '0-raw/evidence.md',
        'structural_anchor': 'section-a',
    }
    try:
        ledger.validate_quote(tmp_path, row)
    except ledger.LedgerError as error:
        assert 'lacks declared structural anchor' in str(error)
    else:
        raise AssertionError('indented code was treated as a section')


def test_non_pdf_section_extraction_ignores_fenced_code_heading(tmp_path):
    raw = tmp_path / '0-raw/evidence.md'
    raw.parent.mkdir(parents=True)
    raw.write_text(
        '```markdown\n## Section A\nFake quote.\n```\n',
        encoding='utf-8',
    )
    row = {
        'row_id': 'locator',
        'verdict': 'hold',
        'quote': 'Fake quote.',
        'quote_raw_path': '0-raw/evidence.md',
        'structural_anchor': 'section-a',
    }
    try:
        ledger.validate_quote(tmp_path, row)
    except ledger.LedgerError as error:
        assert 'lacks declared structural anchor' in str(error)
    else:
        raise AssertionError('fenced code heading became evidence provenance')


def test_evidence_path_cannot_point_into_wiki(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_text('## Evidence\nSelf support.\n', encoding='utf-8')
    try:
        ledger.resolve_raw_path(tmp_path, '1-wiki/concepts/example.md')
    except ledger.LedgerError as error:
        assert 'outside 0-raw' in str(error)
    else:
        raise AssertionError('wiki page was accepted as raw evidence')


def test_raw_evidence_path_rejects_lexical_aliases(tmp_path):
    raw = tmp_path / '0-raw/evidence.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('evidence\n', encoding='utf-8')
    for alias in ('0-raw/./evidence.txt', '0-raw//evidence.txt'):
        try:
            ledger.resolve_raw_path(tmp_path, alias)
        except ledger.LedgerError as error:
            assert 'not canonical' in str(error)
        else:
            raise AssertionError(f'raw lexical alias was accepted: {alias}')


def test_non_pdf_refute_must_match_claim_structural_locator():
    claim = claim_row(
        locators=[
            {
                'raw_path': '0-raw/evidence.md',
                'structural_anchor': 'section-a',
            }
        ]
    )
    claim['raw_dependencies'] = [
        {'raw_path': '0-raw/evidence.md', 'sha256': 'a' * 64}
    ]
    role_rows = [
        {
            'row_id': 'refute',
            'verdict': 'refute',
            'quote': 'Evidence B.',
            'quote_raw_path': '0-raw/evidence.md',
            'physical_page': 1,
        }
    ]
    try:
        ledger.validate_hold_raw_binding(
            claim_id='claim', claim=claim, role_rows=role_rows
        )
    except ledger.LedgerError as error:
        assert 'lacks exact structural locator' in str(error)
    else:
        raise AssertionError('non-PDF REFUTE escaped section binding')


def test_minimal_complete_report_validates(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True)
    page.write_text(
        '# Example\n\n> [!idea]\n> - A claim.\n> ^idea\n',
        encoding='utf-8',
    )
    raw = tmp_path / '0-raw/example.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text(
        '## Evidence\nA supporting quote.\n',
        encoding='utf-8',
    )
    claim = claim_row(
        locators=[
            {
                'raw_path': '0-raw/example.txt',
                'structural_anchor': 'Evidence',
            }
        ]
    )
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
                'role_version': '1',
                'agent_id': agent,
                'blind_to': [
                    (
                        'entailment_bullet'
                        if role == 'locator_bullet'
                        else 'locator_bullet'
                    )
                ],
                'verdict': 'hold',
                'quote': 'A supporting quote.',
                'quote_raw_path': '0-raw/example.txt',
                'physical_page': None,
                'structural_anchor': 'Evidence',
                'reasoning': 'The quote supports the exact claim.',
                'confidence': 'high',
                'correction': None,
                'quote_validated': True,
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
            'role_rows': ['locator_bullet', 'entailment_bullet'],
        },
        {
            'schema_version': 1,
            'row_type': 'source',
            'row_id': 'source-example',
            'run_id': 'run',
            'raw_path': '0-raw/example.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
            'disposition': 'available',
            'evidence': (
                'Current raw was opened and matched its frozen digest.'
            ),
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
        'rows': 7,
        'claims': 1,
        'page_generations': 0,
        'pending': 0,
    }
    source = rows.pop(5)
    body = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{body}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'source terminal inventory' in str(error)
    else:
        raise AssertionError('raw dependency passed without a source row')
    rows.insert(5, source)
    rows[4]['role_rows'] = ['locator_bullet', 'invented-row']
    body = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{body}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'does not bind both role rows' in str(error)
    else:
        raise AssertionError('claim terminal accepted invented role row ID')
    rows[4]['role_rows'] = ['locator_bullet', 'entailment_bullet']
    unrelated = tmp_path / '0-raw/unrelated.txt'
    unrelated.write_text('A supporting quote.\n', encoding='utf-8')
    rows[2]['quote_raw_path'] = '0-raw/unrelated.txt'
    report = tmp_path / 'report-unrelated-quote.md'
    body = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        '---\ntype: ingest-report\nresult: complete\nledger_schema: 1\n'
        'pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n{body}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'HOLD quote is outside claim raw dependencies' in str(error)
    else:
        raise AssertionError('ledger accepted a HOLD from an unrelated raw')


def _write_audit_report(
    tmp_path,
    rows,
    mode='partial',
    markers_pending=0,
    result='complete',
    pending=0,
):
    report = tmp_path / 'audit.md'
    body = '\n'.join(json.dumps(row, sort_keys=True) for row in rows)
    report.write_text(
        f'---\ntype: audit\nmode: {mode}\nresult: {result}\n'
        f'ledger_schema: 1\npending: {pending}\n'
        f'markers_pending: {markers_pending}\n---\n'
        f'{ledger.START}\n```jsonl\n{body}\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    return report


def test_current_report_type_must_be_supported(tmp_path):
    rows = _audit_rows(tmp_path)
    report = _write_audit_report(tmp_path, rows)
    report.write_text(
        report.read_text(encoding='utf-8').replace(
            'type: audit', 'type: unrelated-report', 1
        ),
        encoding='utf-8',
    )
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'unsupported report type' in str(error)
    else:
        raise AssertionError('unsupported current report type was accepted')


def test_audit_page_reader_requires_exact_raw_manifest(tmp_path):
    rows = _audit_rows(tmp_path)
    page_reader = next(
        row for row in rows if row.get('row_type') == 'page_reader'
    )
    page_reader.pop('raw_manifest')
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'raw_manifest' in str(error)
    else:
        raise AssertionError('page reader without raw_manifest was accepted')


def test_zero_claim_raw_backed_page_still_requires_source_inventory(tmp_path):
    rows = _audit_rows(tmp_path)
    raw = tmp_path / '0-raw/example.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('Evidence.\n', encoding='utf-8')
    page = tmp_path / '1-wiki/concepts/example.md'
    body = '# Example\n\n[[0-raw/example.txt]]\n'
    verified_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    page.write_text(
        '---\ntype: concept\ntitle: Example\n'
        'sources: [Example2026]\nstatus: verified\n'
        f'verified_hash: {verified_hash}\n---\n{body}',
        encoding='utf-8',
    )
    rows = [
        row
        for row in rows
        if row.get('row_type') not in {'claim', 'claim_terminal'}
    ]
    generation = ledger.semantic_page_digest(page=page)
    manifest = next(row for row in rows if row['row_type'] == 'manifest')
    manifest['planned_claims'] = 0
    manifest['planned_bullet_roles'] = 0
    reconciliation = next(
        row for row in rows if row['row_type'] == 'reconciliation'
    )
    for prefix in ('planned', 'terminal'):
        reconciliation[f'{prefix}_claims'] = 0
        reconciliation[f'{prefix}_bullet_roles'] = 0
    for row in rows:
        if row.get('row_type') == 'page_reader':
            row['page_generation'] = generation
        elif row.get('row_type') == 'status_write':
            row['page_generation'] = generation
            row['pre_semantic_hash'] = generation
            row['post_semantic_hash'] = generation
            row['verified_hash'] = verified_hash
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'planned source count' in str(error)
    else:
        raise AssertionError('zero-claim raw-backed page omitted its source')


def _audit_rows(tmp_path):
    page = tmp_path / '1-wiki/concepts/example.md'
    page.parent.mkdir(parents=True, exist_ok=True)
    body = '# Example\n\n> [!idea]\n> - A claim.\n> ^idea\n'
    verified_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    page.write_text(
        '---\ntype: concept\ntitle: Example\n'
        'sources: [Example2026]\nstatus: verified\n'
        f'verified_hash: {verified_hash}\n---\n{body}',
        encoding='utf-8',
    )
    claim = claim_row()
    claim['classification'] = 'exempt'
    claim['exemption_reason'] = 'obvious_definitional'
    generation = ledger.semantic_page_digest(page=page)
    claim['context_digest'] = generation
    claim['claim_instance_id'] = ledger.expected_claim_id(claim)
    claim_id = claim['claim_instance_id']
    epoch = 'READY(2)'
    rows = [
        {
            'schema_version': 1,
            'row_type': 'manifest',
            'row_id': 'manifest',
            'run_id': 'run',
            'mode': 'partial',
            'relationship_epoch': epoch,
            'planned_pages': 1,
            'planned_sources': 0,
            'planned_claims': 1,
            'planned_bullet_roles': 0,
            'planned_page_readers': 2,
            'planned_scanners': 0,
            'planned_status_writes': 1,
        },
        claim,
        {
            'schema_version': 1,
            'row_type': 'claim_terminal',
            'row_id': 'terminal',
            'run_id': 'run',
            'claim_instance_id': claim_id,
            'disposition': 'exempt',
        },
        *[
            {
                'schema_version': 1,
                'row_type': 'page_reader',
                'row_id': role,
                'run_id': 'run',
                'relationship_epoch': epoch,
                'page_path': '1-wiki/concepts/example.md',
                'page_generation': generation,
                'role': role,
                'agent_id': agent,
                'blind_to': [
                    (
                        'entailment_argument_page'
                        if role == 'locator_page'
                        else 'locator_page'
                    )
                ],
                'verdict': 'hold',
                'raw_manifest': [],
                'defects': [],
                'evidence': 'Complete page and raw manifest reviewed.',
            }
            for role, agent in (
                ('locator_page', 'locator-agent'),
                ('entailment_argument_page', 'entailment-agent'),
            )
        ],
        {
            'schema_version': 1,
            'row_type': 'status_write',
            'row_id': 'status',
            'run_id': 'run',
            'relationship_epoch': epoch,
            'page_path': '1-wiki/concepts/example.md',
            'page_generation': generation,
            'before_status': 'draft',
            'after_status': 'verified',
            'pre_semantic_hash': generation,
            'post_semantic_hash': generation,
            'marker_action': 'none',
            'pre_marker_count': 0,
            'post_marker_count': 0,
            'verified_hash': verified_hash,
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
            'planned_sources': 0,
            'terminal_sources': 0,
            'pending_sources': 0,
            'planned_claims': 1,
            'terminal_claims': 1,
            'pending_claims': 0,
            'planned_bullet_roles': 0,
            'terminal_bullet_roles': 0,
            'pending_bullet_roles': 0,
            'planned_page_readers': 2,
            'terminal_page_readers': 2,
            'pending_page_readers': 0,
            'planned_scanners': 0,
            'terminal_scanners': 0,
            'pending_scanners': 0,
            'planned_status_writes': 1,
            'terminal_status_writes': 1,
            'pending_status_writes': 0,
        },
    ]
    return rows


def _rebind_audit_page(rows, page, body):
    verified_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    page.write_text(
        '---\ntype: concept\ntitle: Example\n'
        'sources: [Example2026]\nstatus: verified\n'
        f'verified_hash: {verified_hash}\n---\n{body}',
        encoding='utf-8',
    )
    generation = ledger.semantic_page_digest(page=page)
    for row in rows:
        if row['row_type'] == 'page_reader':
            row['page_generation'] = generation
        elif row['row_type'] == 'status_write':
            row['page_generation'] = generation
            row['pre_semantic_hash'] = generation
            row['post_semantic_hash'] = generation
            row['verified_hash'] = verified_hash


def _bind_audit_claim_to_raw(rows, tmp_path):
    raw = tmp_path / '0-raw/example.txt'
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text('supporting quote\n', encoding='utf-8')
    claim = next(row for row in rows if row['row_type'] == 'claim')
    old_id = claim['claim_instance_id']
    claim['raw_dependencies'] = [
        {
            'raw_path': '0-raw/example.txt',
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
        }
    ]
    claim['claim_instance_id'] = ledger.expected_claim_id(claim)
    for row in rows:
        if row.get('claim_instance_id') == old_id:
            row['claim_instance_id'] = claim['claim_instance_id']
        if row.get('row_type') == 'bullet_verdict' and row.get(
            'verdict'
        ) in {'hold', 'refute'}:
            row['quote'] = 'supporting quote'
            row['quote_raw_path'] = '0-raw/example.txt'
            row['structural_anchor'] = 'Evidence'
        if (
            row.get('row_type') == 'bullet_verdict'
            and row.get('verdict') == 'cannot_confirm'
        ):
            row['searched_raw_paths'] = ['0-raw/example.txt']
            row['search_summary'] = (
                'Searched the complete current raw without finding support.'
            )
    manifest = next(row for row in rows if row['row_type'] == 'manifest')
    manifest['planned_sources'] = 1
    reconciliation = next(
        row for row in rows if row['row_type'] == 'reconciliation'
    )
    reconciliation['planned_sources'] = 1
    reconciliation['terminal_sources'] = 1
    if not any(row.get('row_type') == 'source' for row in rows):
        rows.insert(
            rows.index(reconciliation),
            {
                'schema_version': 1,
                'row_type': 'source',
                'row_id': 'source-example',
                'run_id': 'run',
                'raw_path': '0-raw/example.txt',
                'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
                'disposition': 'available',
                'evidence': (
                    'Current raw was opened and matched its frozen digest.'
                ),
            },
        )


def test_audit_rows_bind_run_epoch_page_and_generation(tmp_path):
    rows = _audit_rows(tmp_path)
    report = _write_audit_report(tmp_path, rows)
    summary = ledger.validate(report, tmp_path, recheck_quotes=False)
    assert summary['page_generations'] == 1


def test_required_claim_cannot_use_exempt_terminal(tmp_path):
    rows = _audit_rows(tmp_path)
    claim = next(row for row in rows if row['row_type'] == 'claim')
    claim['classification'] = 'required'
    claim.pop('exemption_reason')
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'invalid required-claim disposition' in str(error)
    else:
        raise AssertionError('required claim terminated as exempt')


def test_claim_text_cannot_be_empty_or_whitespace(tmp_path):
    for empty in ('', '   '):
        rows = _audit_rows(tmp_path)
        claim = next(row for row in rows if row['row_type'] == 'claim')
        old_id = claim['claim_instance_id']
        claim['claim_text'] = empty
        claim['claim_bytes'] = len(empty.encode('utf-8'))
        claim['claim_instance_id'] = ledger.expected_claim_id(claim)
        for row in rows:
            if row.get('claim_instance_id') == old_id:
                row['claim_instance_id'] = claim['claim_instance_id']
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'lacks full claim_text' in str(error)
        else:
            raise AssertionError('empty claim text was accepted')


def test_audit_reconciliation_rejects_boolean_counts(tmp_path):
    rows = _audit_rows(tmp_path)
    manifest = next(row for row in rows if row['row_type'] == 'manifest')
    reconciliation = next(
        row for row in rows if row['row_type'] == 'reconciliation'
    )
    manifest['planned_sources'] = False
    reconciliation['planned_sources'] = False
    reconciliation['terminal_sources'] = False
    reconciliation['pending_sources'] = False
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'integer sources counts' in str(error)
    else:
        raise AssertionError('audit accepted Boolean reconciliation counts')


def test_audit_rejects_phantom_scanner_row(tmp_path):
    rows = _audit_rows(tmp_path)
    manifest = next(row for row in rows if row['row_type'] == 'manifest')
    reconciliation = next(
        row for row in rows if row['row_type'] == 'reconciliation'
    )
    manifest['planned_scanners'] = 1
    reconciliation['planned_scanners'] = 1
    reconciliation['terminal_scanners'] = 1
    rows.insert(
        -1,
        {
            'schema_version': 1,
            'row_type': 'scanner',
            'row_id': 'phantom',
            'run_id': 'run',
        },
    )
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'scanner lacks identity' in str(error)
    else:
        raise AssertionError('audit accepted phantom scanner evidence')


def test_audit_complete_rejects_failed_nonfinal_scanner(tmp_path):
    rows = _audit_rows(tmp_path)
    manifest = next(row for row in rows if row['row_type'] == 'manifest')
    reconciliation = next(
        row for row in rows if row['row_type'] == 'reconciliation'
    )
    manifest['planned_scanners'] = 1
    reconciliation['planned_scanners'] = 1
    reconciliation['terminal_scanners'] = 1
    rows.insert(
        -1,
        {
            'schema_version': 1,
            'row_type': 'scanner',
            'row_id': 'failed-gate',
            'run_id': 'run',
            'relationship_epoch': 'READY(2)',
            'scanner': 'relationship_sweep',
            'target': '1-wiki',
            'status': 1,
            'result': 'blocked',
            'stdout_json': True,
            'stderr_runtime_error': False,
            'terminal': True,
        },
    )
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'terminal audit contains failed scanner' in str(error)
    else:
        raise AssertionError('complete audit accepted failed scanner')


def test_audit_page_reader_agent_ids_are_trimmed_and_distinct(tmp_path):
    for identities in ((' ', 'reader-b'), ('reader-a', 'reader-a ')):
        rows = _audit_rows(tmp_path)
        page_readers = [
            row for row in rows if row['row_type'] == 'page_reader'
        ]
        for row, identity in zip(page_readers, identities, strict=True):
            row['agent_id'] = identity
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'agent ID' in str(error) or 'not distinct' in str(error)
        else:
            raise AssertionError(
                f'audit accepted reader identities {identities!r}'
            )


def test_audit_status_write_requires_transition_and_marker_provenance(
    tmp_path,
):
    for missing in (
        'before_status',
        'marker_action',
        'pre_marker_count',
        'post_marker_count',
    ):
        rows = _audit_rows(tmp_path)
        status = next(row for row in rows if row['row_type'] == 'status_write')
        status.pop(missing)
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'audit status write' in str(error)
        else:
            raise AssertionError(
                f'audit accepted status write without {missing}'
            )


def test_audit_status_write_marker_action_matches_retained_transition(
    tmp_path,
):
    rows = _audit_rows(tmp_path)
    status = next(row for row in rows if row['row_type'] == 'status_write')
    status['marker_action'] = 'cleared'
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'marker action contradicts counts' in str(error)
    else:
        raise AssertionError('audit accepted contradictory marker action')


def test_audit_frontmatter_marker_count_matches_retained_rows(tmp_path):
    rows = _audit_rows(tmp_path)
    page = tmp_path / '1-wiki/concepts/example.md'
    page_text = page.read_text(encoding='utf-8').replace(
        '> - A claim.',
        '> - *[unverified]* A claim.',
    )
    page.write_text(page_text, encoding='utf-8')
    verified_hash = ledger.verified_body_hash(page=page)
    page_text = re.sub(
        r'^verified_hash:.*$',
        f'verified_hash: {verified_hash}',
        page_text,
        flags=re.MULTILINE,
    )
    page.write_text(page_text, encoding='utf-8')
    status = next(row for row in rows if row['row_type'] == 'status_write')
    status['marker_action'] = 'added'
    status['pre_marker_count'] = 0
    status['post_marker_count'] = 1
    status['verified_hash'] = verified_hash
    report = _write_audit_report(tmp_path, rows, markers_pending=0)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'markers_pending differs' in str(error)
    else:
        raise AssertionError('audit hid a retained pending marker')


def test_audit_page_readers_require_evidence_defects_and_blindness(tmp_path):
    for missing, expected in (
        ('evidence', 'lacks full evidence'),
        ('defects', 'defects are malformed'),
        ('blind_to', 'lacks blindness provenance'),
    ):
        rows = _audit_rows(tmp_path)
        page_reader = next(
            row for row in rows if row['row_type'] == 'page_reader'
        )
        page_reader.pop(missing)
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert expected in str(error)
        else:
            raise AssertionError(
                f'audit accepted page reader without {missing}'
            )


def test_audit_page_reader_hold_requires_empty_defects(tmp_path):
    rows = _audit_rows(tmp_path)
    page_reader = next(
        row for row in rows if row['row_type'] == 'page_reader'
    )
    page_reader['defects'] = [
        {'scope': 'bullet_local', 'detail': 'Unsupported conclusion'}
    ]
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'HOLD contains defects' in str(error)
    else:
        raise AssertionError('audit accepted page HOLD with defects')


def test_audit_page_reader_requires_structured_nonempty_defects(tmp_path):
    for malformed in (
        None,
        '',
        {},
        {'scope': ''},
        {'scope': 'nonsense', 'detail': 'x'},
        {'detail': ''},
    ):
        rows = _audit_rows(tmp_path)
        page_reader = next(
            row for row in rows if row['row_type'] == 'page_reader'
        )
        page_reader['verdict'] = 'refute'
        page_reader['defects'] = [malformed]
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'contains a malformed defect' in str(error)
        else:
            raise AssertionError(
                f'audit accepted malformed page defect: {malformed!r}'
            )


def test_audit_cross_bullet_defect_requires_exact_dependency_set(tmp_path):
    rows = _audit_rows(tmp_path)
    page_reader = next(
        row for row in rows if row['row_type'] == 'page_reader'
    )
    page_reader['verdict'] = 'refute'
    page_reader['defects'] = [
        {'scope': 'cross_bullet', 'detail': 'Conflict'}
    ]
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'lacks exact claim dependency set' in str(error)
    else:
        raise AssertionError('cross-bullet defect omitted dependencies')


def test_audit_bullet_local_refute_invalidates_held_claim_pair(tmp_path):
    rows = _audit_rows(tmp_path)
    manifest = rows[0]
    claim = rows[1]
    claim['classification'] = 'required'
    claim.pop('exemption_reason')
    terminal = next(row for row in rows if row['row_id'] == 'terminal')
    terminal['disposition'] = 'backfilled_hold'
    terminal['role_rows'] = ['locator_bullet', 'entailment_bullet']
    manifest['planned_bullet_roles'] = 2
    reconciliation = next(
        row for row in rows if row['row_id'] == 'reconciliation'
    )
    reconciliation['planned_bullet_roles'] = 2
    reconciliation['terminal_bullet_roles'] = 2
    bullet_rows = [
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': role,
            'run_id': 'run',
            'relationship_epoch': 'READY(2)',
            'claim_instance_id': claim['claim_instance_id'],
            'role': role,
            'role_version': '1',
            'agent_id': agent,
            'blind_to': [ledger.BULLET_COUNTERPART[role]],
            'verdict': 'hold',
            'reasoning': 'The exact located evidence supports the claim.',
            'confidence': 'high',
            'correction': None,
            'quote_validated': True,
        }
        for role, agent in (
            ('locator_bullet', 'locator-agent'),
            ('entailment_bullet', 'entailment-agent'),
        )
    ]
    rows[2:2] = bullet_rows
    _bind_audit_claim_to_raw(rows=rows, tmp_path=tmp_path)
    page_reader = next(
        row for row in rows if row['row_type'] == 'page_reader'
    )
    page_reader['verdict'] = 'refute'
    page_reader['defects'] = [
        {
            'scope': 'bullet_local',
            'detail': 'The claim-level conclusion is unsupported.',
            'claim_instance_ids': [claim['claim_instance_id']],
        }
    ]
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'bullet-local page defect lacks a current non-HOLD' in str(
            error
        )
    else:
        raise AssertionError('page-level refute retained a claim HOLD pair')


def test_audit_bullet_local_refute_rejects_exempt_or_invalidated_target(
    tmp_path,
):
    for disposition in ('exempt', 'invalidated'):
        case = tmp_path / disposition
        rows = _audit_rows(case)
        claim = next(row for row in rows if row['row_type'] == 'claim')
        terminal = next(
            row for row in rows if row['row_type'] == 'claim_terminal'
        )
        page_reader = next(
            row for row in rows if row['row_type'] == 'page_reader'
        )
        page_reader['verdict'] = 'refute'
        page_reader['defects'] = [
            {
                'scope': 'bullet_local',
                'detail': 'Claim-level support is defective.',
                'claim_instance_ids': [claim['claim_instance_id']],
            }
        ]
        page = case / '1-wiki/concepts/example.md'
        page_text = page.read_text(encoding='utf-8')
        page_text = page_text.replace(
            'status: verified\n',
            'status: needs-update\n'
            'needs_update_reason: page reader refuted claim support\n',
        )
        page_text = re.sub(
            r'^verified_hash:.*\n', '', page_text, flags=re.MULTILINE
        )
        page.write_text(page_text, encoding='utf-8')
        status = next(
            row for row in rows if row['row_type'] == 'status_write'
        )
        status['after_status'] = 'needs-update'
        status['needs_update_reason'] = (
            'page reader refuted claim support'
        )
        status.pop('verified_hash')
        result = 'complete'
        pending = 0
        if disposition == 'invalidated':
            claim['classification'] = 'required'
            claim.pop('exemption_reason')
            terminal['disposition'] = 'invalidated'
            manifest = next(
                row for row in rows if row['row_type'] == 'manifest'
            )
            reconciliation = next(
                row for row in rows if row['row_type'] == 'reconciliation'
            )
            manifest['planned_bullet_roles'] = 2
            reconciliation['result'] = 'incomplete'
            reconciliation['pending'] = 2
            reconciliation['planned_bullet_roles'] = 2
            reconciliation['terminal_bullet_roles'] = 0
            reconciliation['pending_bullet_roles'] = 2
            result = 'incomplete'
            pending = 2
        report = _write_audit_report(
            case,
            rows,
            result=result,
            pending=pending,
        )
        try:
            ledger.validate(report, case, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'bullet-local page defect' in str(error)
        else:
            raise AssertionError(
                f'bullet-local defect targeted {disposition} claim'
            )


def test_audit_full_mode_rejects_reused_hold(monkeypatch, tmp_path):
    rows = _audit_rows(tmp_path)
    manifest = rows[0]
    claim = rows[1]
    claim['classification'] = 'required'
    claim.pop('exemption_reason')
    terminal = next(row for row in rows if row['row_id'] == 'terminal')
    terminal['disposition'] = 'reused_hold'
    reconciliation = next(
        row for row in rows if row['row_id'] == 'reconciliation'
    )
    manifest['planned_bullet_roles'] = 2
    reconciliation['planned_bullet_roles'] = 2
    reconciliation['terminal_bullet_roles'] = 2
    monkeypatch.setattr(
        ledger, 'validate_reused_pair', lambda *args, **kwargs: None
    )

    partial = _write_audit_report(tmp_path, rows, mode='partial')
    ledger.validate(partial, tmp_path, recheck_quotes=False)

    manifest['mode'] = 'full'
    full = _write_audit_report(tmp_path, rows, mode='full')
    try:
        ledger.validate(full, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'full mode contains reused HOLD evidence' in str(error)
    else:
        raise AssertionError('audit full mode accepted reused HOLD evidence')


def test_audit_full_mode_reconciles_entire_retained_page_inventory(tmp_path):
    rows = _audit_rows(tmp_path)
    rows[0]['mode'] = 'full'
    report = _write_audit_report(tmp_path, rows, mode='full')
    ledger.validate(report, tmp_path, recheck_quotes=False)

    omitted = tmp_path / '1-wiki/concepts/omitted.md'
    omitted_hash = hashlib.sha256(b'# Omitted\n').hexdigest()
    omitted.write_text(
        '---\ntype: concept\ntitle: Omitted\nstatus: verified\n'
        f'verified_hash: {omitted_hash}\n'
        '---\n# Omitted\n',
        encoding='utf-8',
    )
    report = _write_audit_report(tmp_path, rows, mode='full')
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'full page inventory differs from retained wiki' in str(error)
    else:
        raise AssertionError('audit full mode omitted a retained wiki page')


def test_audit_partial_mode_includes_every_mandatory_retained_page(tmp_path):
    for status, extra in (
        ('draft', ''),
        ('needs-update', 'needs_update_reason: unresolved source\n'),
        ('verified', 'verified_hash: invalid\n'),
    ):
        case = tmp_path / status
        rows = _audit_rows(case)
        omitted = case / '1-wiki/concepts/omitted.md'
        omitted.write_text(
            '---\ntype: concept\ntitle: Omitted\n'
            f'status: {status}\n{extra}---\n# Omitted\n',
            encoding='utf-8',
        )
        report = _write_audit_report(case, rows, mode='partial')
        try:
            ledger.validate(report, case, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'partial page inventory omits mandatory pages' in str(error)
        else:
            raise AssertionError(f'audit partial mode omitted a {status} page')


def test_audit_partial_mode_includes_verified_page_with_unverified_marker(
    tmp_path,
):
    rows = _audit_rows(tmp_path)
    omitted = tmp_path / '1-wiki/concepts/omitted.md'
    omitted_body = (
        '# Omitted\n\n> [!idea]\n> - *[unverified]* Pending.\n> ^idea\n'
    )
    omitted.write_text(
        '---\ntype: concept\ntitle: Omitted\nstatus: verified\n'
        f'verified_hash: {hashlib.sha256(omitted_body.encode()).hexdigest()}\n'
        f'---\n{omitted_body}',
        encoding='utf-8',
    )
    report = _write_audit_report(tmp_path, rows, mode='partial')
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'partial page inventory omits mandatory pages' in str(error)
    else:
        raise AssertionError('audit partial mode omitted an unverified marker')


def test_audit_partial_mode_includes_untracked_self_stamped_page(tmp_path):
    rows = _audit_rows(tmp_path)
    omitted = tmp_path / '1-wiki/concepts/untracked.md'
    body = '# Untracked\n'
    omitted.write_text(
        '---\ntype: concept\ntitle: Untracked\nstatus: verified\n'
        f'verified_hash: {hashlib.sha256(body.encode()).hexdigest()}\n'
        f'---\n{body}',
        encoding='utf-8',
    )
    report = _write_audit_report(tmp_path, rows, mode='partial')
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'partial page inventory omits mandatory pages' in str(error)
    else:
        raise AssertionError('audit omitted an untracked self-stamped page')


def test_audit_partial_mode_includes_pages_affected_by_dirty_raw(tmp_path):
    rows = _audit_rows(tmp_path)
    raw = tmp_path / '0-raw/papers/source.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('original evidence\n', encoding='utf-8')
    source = tmp_path / '1-wiki/sources/source.md'
    source.parent.mkdir(parents=True)
    source_body = '# Source\n'
    source.write_text(
        '---\ntype: paper\ntitle: Source\nupdated: 2026-08-05\n'
        'file: "[[0-raw/papers/source.txt]]"\nstatus: verified\n'
        f'verified_hash: {hashlib.sha256(source_body.encode()).hexdigest()}\n'
        f'---\n{source_body}',
        encoding='utf-8',
    )
    dependent_body = '# Dependent\n\nSee [[source]].\n'
    dependent = tmp_path / '1-wiki/concepts/dependent.md'
    dependent.write_text(
        '---\ntype: concept\ntitle: Dependent\nupdated: 2026-08-05\n'
        'status: verified\n'
        'verified_hash: '
        f'{hashlib.sha256(dependent_body.encode()).hexdigest()}\n'
        f'---\n{dependent_body}',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            'config',
            'user.email',
            'audit-test',
        ],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw', '1-wiki'], check=True
    )
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            'commit',
            '-qm',
            'fixture',
        ],
        check=True,
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '2026-08-05T09:00:00Z',
            'GIT_COMMITTER_DATE': '2026-08-05T09:00:00Z',
        },
    )
    raw.write_text('changed evidence\n', encoding='utf-8')
    assert ledger.pages_affected_by_raw_drift(repo_root=tmp_path) == {
        '1-wiki/concepts/dependent.md',
        '1-wiki/sources/source.md',
    }

    report = _write_audit_report(tmp_path, rows, mode='partial')
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'partial page inventory omits mandatory pages' in str(error)
    else:
        raise AssertionError(
            'audit partial mode omitted a dirty-raw dependent'
        )


def test_audit_partial_mode_includes_newer_committed_raw_dependents(tmp_path):
    rows = _audit_rows(tmp_path)
    raw = tmp_path / '0-raw/papers/source.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('original evidence\n', encoding='utf-8')
    source = tmp_path / '1-wiki/sources/source.md'
    source.parent.mkdir(parents=True)
    source_body = '# Source\n'
    source.write_text(
        '---\ntype: paper\ntitle: Source\nupdated: 2020-01-01\n'
        'file: "[[0-raw/papers/source.txt]]"\nstatus: verified\n'
        f'verified_hash: {hashlib.sha256(source_body.encode()).hexdigest()}\n'
        f'---\n{source_body}',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            'config',
            'user.email',
            'audit-test',
        ],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw', '1-wiki'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'fixture'],
        check=True,
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '2020-01-01T12:00:00Z',
            'GIT_COMMITTER_DATE': '2020-01-01T12:00:00Z',
        },
    )
    raw.write_text('committed replacement\n', encoding='utf-8')
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw/papers/source.txt'],
        check=True,
    )
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            'commit',
            '-qm',
            'replace raw',
        ],
        check=True,
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '2020-01-01T12:00:00Z',
            'GIT_COMMITTER_DATE': '2026-08-05T17:00:00Z',
        },
    )

    report = _write_audit_report(tmp_path, rows, mode='partial')
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'partial page inventory omits mandatory pages' in str(error)
    else:
        raise AssertionError(
            'audit partial mode omitted a newer committed raw dependent'
        )


def test_raw_drift_compares_transitive_dependency_to_each_page_date(tmp_path):
    raw = tmp_path / '0-raw/papers/source.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('evidence\n', encoding='utf-8')
    source = tmp_path / '1-wiki/sources/source.md'
    source.parent.mkdir(parents=True)
    source.write_text(
        '---\ntype: paper\nupdated: 1900-01-01\nstatus: verified\n---\n'
        '# Source\n\n[[0-raw/papers/source.txt]]\n',
        encoding='utf-8',
    )
    concept = tmp_path / '1-wiki/concepts/concept.md'
    concept.parent.mkdir(parents=True)
    concept.write_text(
        '---\ntype: concept\nupdated: 2099-01-01\nstatus: verified\n---\n'
        '# Concept\n\n[[source]]\n',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.email', 'audit-test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '1-wiki/concepts/concept.md'],
        check=True,
    )
    subprocess.run(
        [
            'git',
            '-C',
            str(tmp_path),
            'commit',
            '-qm',
            'older dependent',
        ],
        check=True,
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '2025-01-01T12:00:00Z',
            'GIT_COMMITTER_DATE': '2025-01-01T12:00:00Z',
        },
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw/papers/source.txt'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'newer raw'],
        check=True,
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '2025-01-02T12:00:00Z',
            'GIT_COMMITTER_DATE': '2025-01-02T12:00:00Z',
        },
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '1-wiki/sources/source.md'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'newest source page'],
        check=True,
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '2025-01-03T12:00:00Z',
            'GIT_COMMITTER_DATE': '2025-01-03T12:00:00Z',
        },
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=tmp_path) == {
        '1-wiki/concepts/concept.md',
        '1-wiki/sources/source.md',
    }


def test_raw_drift_requires_terminal_raw_verification_not_commit_order(
    tmp_path,
):
    page_path = '1-wiki/sources/source.md'
    raw_path = '0-raw/evidence.txt'

    def initialize(case):
        case.mkdir()
        subprocess.run(
            ['git', 'init', '-q', '-b', 'main', str(case)], check=True
        )
        subprocess.run(
            ['git', '-C', str(case), 'config', 'user.email', 'audit-test'],
            check=True,
        )
        subprocess.run(
            ['git', '-C', str(case), 'config', 'user.name', 'Audit Test'],
            check=True,
        )

    def write_page(case):
        page = case / page_path
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(
            '---\ntype: paper\nupdated: 2099-01-01\nstatus: verified\n'
            '---\n# Source\n\n[[0-raw/evidence.txt]]\n',
            encoding='utf-8',
        )

    def write_raw(case):
        raw = case / raw_path
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text('evidence\n', encoding='utf-8')

    def commit(case, paths, message, timestamp):
        subprocess.run(
            ['git', '-C', str(case), 'add', *paths], check=True
        )
        subprocess.run(
            ['git', '-C', str(case), 'commit', '-qm', message],
            check=True,
            env={
                **os.environ,
                'GIT_AUTHOR_DATE': timestamp,
                'GIT_COMMITTER_DATE': timestamp,
            },
        )

    same = tmp_path / 'same'
    initialize(same)
    write_page(same)
    write_raw(same)
    commit(same, [page_path, raw_path], 'same commit', '2025-01-01T12:00:00Z')
    assert ledger.pages_affected_by_raw_drift(repo_root=same) == {page_path}

    page_ancestor = tmp_path / 'page-ancestor'
    initialize(page_ancestor)
    write_page(page_ancestor)
    commit(
        page_ancestor,
        [page_path],
        'page first',
        '2025-01-01T12:00:00Z',
    )
    write_raw(page_ancestor)
    commit(
        page_ancestor,
        [raw_path],
        'raw later',
        '2025-01-02T12:00:00Z',
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=page_ancestor) == {
        page_path
    }

    raw_ancestor = tmp_path / 'raw-ancestor'
    initialize(raw_ancestor)
    write_raw(raw_ancestor)
    commit(
        raw_ancestor,
        [raw_path],
        'raw first',
        '2025-01-01T12:00:00Z',
    )
    write_page(raw_ancestor)
    commit(
        raw_ancestor,
        [page_path],
        'page later',
        '2025-01-02T12:00:00Z',
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=raw_ancestor) == {
        page_path
    }

    divergent = tmp_path / 'divergent'
    initialize(divergent)
    subprocess.run(
        [
            'git',
            '-C',
            str(divergent),
            'commit',
            '--allow-empty',
            '-qm',
            'root',
        ],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(divergent), 'switch', '-qc', 'page'], check=True
    )
    write_page(divergent)
    commit(
        divergent,
        [page_path],
        'page branch',
        '2025-01-02T12:00:00Z',
    )
    subprocess.run(
        ['git', '-C', str(divergent), 'switch', '-q', 'main'], check=True
    )
    write_raw(divergent)
    commit(
        divergent,
        [raw_path],
        'raw branch',
        '2025-01-02T12:00:00Z',
    )
    subprocess.run(
        [
            'git',
            '-C',
            str(divergent),
            'merge',
            '--no-ff',
            '-qm',
            'merge',
            'page',
        ],
        check=True,
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=divergent) == {
        page_path
    }


def test_raw_drift_uses_last_terminal_page_raw_proof(tmp_path):
    rows = _audit_rows(tmp_path)
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.email', 'audit-test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    raw = tmp_path / '0-raw/example.txt'
    raw.parent.mkdir(parents=True)
    raw.write_text('Evidence.\n', encoding='utf-8')
    raw_sha = hashlib.sha256(raw.read_bytes()).hexdigest()
    page = tmp_path / '1-wiki/concepts/example.md'
    body = '# Example\n\n[[0-raw/example.txt]]\n'
    verified_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    page.write_text(
        '---\ntype: concept\ntitle: Example\n'
        'sources: [Example2026]\nstatus: verified\n'
        f'verified_hash: {verified_hash}\n---\n{body}',
        encoding='utf-8',
    )
    rows = [
        row
        for row in rows
        if row.get('row_type') not in {'claim', 'claim_terminal'}
    ]
    manifest = next(row for row in rows if row['row_type'] == 'manifest')
    manifest['planned_sources'] = 1
    manifest['planned_claims'] = 0
    manifest['planned_bullet_roles'] = 0
    manifest['planned_scanners'] = 1
    rec = next(row for row in rows if row['row_type'] == 'reconciliation')
    rec['planned_sources'] = 1
    rec['terminal_sources'] = 1
    rec['planned_claims'] = 0
    rec['terminal_claims'] = 0
    rec['planned_bullet_roles'] = 0
    rec['terminal_bullet_roles'] = 0
    rec['planned_scanners'] = 1
    rec['terminal_scanners'] = 1
    completion_context = 'd' * 64
    completion_baseline_path = '2-outputs/audit/baselines/proof.json'
    completion_baseline = {
        'schema_version': 1,
        'kind': 'audit-warning-baseline',
        'run_id': 'run',
        'baseline_id': 'proof-baseline',
        'evidence_context_sha256': completion_context,
    }
    completion_baseline_bytes = json.dumps(
        completion_baseline, sort_keys=True
    ).encode()
    completion_baseline_file = tmp_path / completion_baseline_path
    completion_baseline_file.parent.mkdir(parents=True, exist_ok=True)
    completion_baseline_file.write_bytes(completion_baseline_bytes)
    rec.update(
        {
            'warning_baseline_path': completion_baseline_path,
            'warning_baseline_sha256': hashlib.sha256(
                completion_baseline_bytes
            ).hexdigest(),
            'warning_baseline_id': 'proof-baseline',
            'evidence_context_sha256': completion_context,
            'warning_fingerprints': [],
            'mention_occurrences': [],
            'suppression_batches': [],
            'suppression_reader_verdicts': [],
            'neutral_page_transactions': [],
        }
    )
    generation = ledger.semantic_page_digest(page=page)
    raw_manifest = [{'raw_path': '0-raw/example.txt', 'sha256': raw_sha}]
    for row in rows:
        if row.get('row_type') == 'page_reader':
            row['page_generation'] = generation
            row['raw_manifest'] = raw_manifest
        elif row.get('row_type') == 'status_write':
            row['page_generation'] = generation
            row['pre_semantic_hash'] = generation
            row['post_semantic_hash'] = generation
            row['verified_hash'] = verified_hash
    source_row = {
        'schema_version': 1,
        'row_type': 'source',
        'row_id': 'source:example',
        'run_id': 'run',
        'raw_path': '0-raw/example.txt',
        'sha256': raw_sha,
        'disposition': 'available',
        'evidence': 'Current raw bytes were opened and digest-bound.',
    }
    rows.insert(-1, source_row)
    rows.insert(
        -1,
        {
            'schema_version': 1,
            'row_type': 'scanner',
            'row_id': 'final-scanner',
            'run_id': 'run',
            'scanner': 'final_lint_post_bookkeeping',
            'target': '1-wiki',
            'status': 0,
            'lint_result': 'clean',
            'audit_blocking_count': 0,
            'stdout_json': True,
            'stderr_runtime_error': False,
            'warning_count': 0,
            'terminal': True,
        },
    )
    report = _write_audit_report(tmp_path, rows)
    proof = tmp_path / '2-outputs/ingest/proof.md'
    proof.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        report.read_text(encoding='utf-8').replace(
            'type: audit', 'type: ingest-report', 1
        ),
        encoding='utf-8',
    )
    report.replace(proof)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw', '1-wiki', '2-outputs'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'verified raw proof'],
        check=True,
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=tmp_path) == set()

    raw.write_text('Replacement evidence.\n', encoding='utf-8')
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw/example.txt'], check=True
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'replace raw'],
        check=True,
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=tmp_path) == {
        '1-wiki/concepts/example.md'
    }

    page.write_text(
        page.read_text(encoding='utf-8').replace(
            '# Example', '# [[1-wiki/concepts/example.md|Example]]'
        ),
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '1-wiki/concepts/example.md'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'neutral page edit'],
        check=True,
    )
    assert ledger.pages_affected_by_raw_drift(repo_root=tmp_path) == {
        '1-wiki/concepts/example.md'
    }


def _neutral_bridge_fixture(tmp_path):
    host_path = '1-wiki/concepts/host.md'
    target_path = '1-wiki/concepts/target.md'
    host_raw_path = '0-raw/host.txt'
    target_raw_path = '0-raw/target.txt'
    for raw_path, text in (
        (host_raw_path, 'host evidence\n'),
        (target_raw_path, 'target evidence\n'),
    ):
        raw = tmp_path / raw_path
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(text, encoding='utf-8')

    def write_verified_page(page_path, title, body):
        page = tmp_path / page_path
        page.parent.mkdir(parents=True, exist_ok=True)
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        page.write_text(
            f'---\ntype: concept\ntitle: {title}\nstatus: verified\n'
            f'verified_hash: {body_hash}\n---\n{body}',
            encoding='utf-8',
        )
        return page, body_hash

    host_body = '# Host\n\n[[0-raw/host.txt]]\n\nSee Target.\n'
    target_body = '# Target\n\n[[0-raw/target.txt]]\n'
    host, host_body_hash = write_verified_page(host_path, 'Host', host_body)
    target, target_body_hash = write_verified_page(
        target_path, 'Target', target_body
    )
    host_preimage = host.read_bytes()
    raw_shas = {
        raw_path: hashlib.sha256((tmp_path / raw_path).read_bytes()).hexdigest()
        for raw_path in (host_raw_path, target_raw_path)
    }
    generations = {
        host_path: ledger.semantic_page_digest(page=host),
        target_path: ledger.semantic_page_digest(page=target),
    }
    body_hashes = {host_path: host_body_hash, target_path: target_body_hash}
    raw_manifests = {
        host_path: [{'raw_path': host_raw_path, 'sha256': raw_shas[host_raw_path]}],
        target_path: [
            {'raw_path': target_raw_path, 'sha256': raw_shas[target_raw_path]}
        ],
    }
    epoch = 'READY(1)'
    proof_context_hash = 'b' * 64
    proof_baseline_path = '2-outputs/audit/baselines/proof-run.json'
    proof_baseline = {
        'schema_version': 1,
        'kind': 'audit-warning-baseline',
        'run_id': 'proof-run',
        'baseline_id': 'proof-baseline',
        'evidence_context_sha256': proof_context_hash,
    }
    proof_baseline_bytes = json.dumps(
        proof_baseline, sort_keys=True
    ).encode()
    proof_baseline_file = tmp_path / proof_baseline_path
    proof_baseline_file.parent.mkdir(parents=True, exist_ok=True)
    proof_baseline_file.write_bytes(proof_baseline_bytes)
    proof_rows = [
        {
            'schema_version': 1,
            'row_type': 'manifest',
            'row_id': 'proof-manifest',
            'run_id': 'proof-run',
            'mode': 'partial',
            'relationship_epoch': epoch,
            'planned_pages': 2,
            'planned_sources': 2,
            'planned_claims': 0,
            'planned_bullet_roles': 0,
            'planned_page_readers': 4,
            'planned_scanners': 1,
            'planned_status_writes': 2,
        },
    ]
    for index, raw_path in enumerate((host_raw_path, target_raw_path)):
        proof_rows.append(
            {
                'schema_version': 1,
                'row_type': 'source',
                'row_id': f'proof-source-{index}',
                'run_id': 'proof-run',
                'raw_path': raw_path,
                'sha256': raw_shas[raw_path],
                'disposition': 'available',
                'evidence': 'Opened and digest-bound.',
            }
        )
    for page_index, page_path in enumerate((host_path, target_path)):
        for role_index, (role, blind_to) in enumerate(
            (
                ('locator_page', 'entailment_argument_page'),
                ('entailment_argument_page', 'locator_page'),
            )
        ):
            proof_rows.append(
                {
                    'schema_version': 1,
                    'row_type': 'page_reader',
                    'row_id': f'proof-reader-{page_index}-{role_index}',
                    'run_id': 'proof-run',
                    'relationship_epoch': epoch,
                    'page_path': page_path,
                    'page_generation': generations[page_path],
                    'role': role,
                    'agent_id': f'agent-{page_index}-{role_index}',
                    'blind_to': [blind_to],
                    'verdict': 'hold',
                    'raw_manifest': raw_manifests[page_path],
                    'defects': [],
                    'evidence': 'Complete page and raw closure reviewed.',
                }
            )
        proof_rows.append(
            {
                'schema_version': 1,
                'row_type': 'status_write',
                'row_id': f'proof-status-{page_index}',
                'run_id': 'proof-run',
                'relationship_epoch': epoch,
                'page_path': page_path,
                'page_generation': generations[page_path],
                'before_status': 'draft',
                'after_status': 'verified',
                'pre_semantic_hash': generations[page_path],
                'post_semantic_hash': generations[page_path],
                'marker_action': 'none',
                'pre_marker_count': 0,
                'post_marker_count': 0,
                'verified_hash': body_hashes[page_path],
            }
        )
    proof_rows.append(
        {
            'schema_version': 1,
            'row_type': 'scanner',
            'row_id': 'proof-scanner',
            'run_id': 'proof-run',
            'scanner': 'final_lint_post_bookkeeping',
            'target': '1-wiki',
            'status': 0,
            'lint_result': 'clean',
            'audit_blocking_count': 0,
            'stdout_json': True,
            'stderr_runtime_error': False,
            'warning_count': 0,
            'terminal': True,
        }
    )
    reconciliation = {
        'schema_version': 1,
        'row_type': 'reconciliation',
        'row_id': 'proof-reconciliation',
        'run_id': 'proof-run',
        'result': 'complete',
        'pending': 0,
        'warning_baseline_path': proof_baseline_path,
        'warning_baseline_sha256': hashlib.sha256(
            proof_baseline_bytes
        ).hexdigest(),
        'warning_baseline_id': 'proof-baseline',
        'evidence_context_sha256': proof_context_hash,
        'warning_fingerprints': [],
        'mention_occurrences': [],
        'suppression_batches': [],
        'suppression_reader_verdicts': [],
        'neutral_page_transactions': [],
    }
    for unit, count in (
        ('pages', 2),
        ('sources', 2),
        ('claims', 0),
        ('bullet_roles', 0),
        ('page_readers', 4),
        ('scanners', 1),
        ('status_writes', 2),
    ):
        reconciliation[f'planned_{unit}'] = count
        reconciliation[f'terminal_{unit}'] = count
        reconciliation[f'pending_{unit}'] = 0
    proof_rows.append(reconciliation)
    proof = tmp_path / '2-outputs/ingest/proof.md'
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text(
        '---\ntype: ingest-report\nmode: partial\nresult: complete\n'
        'ledger_schema: 1\npending: 0\nmarkers_pending: 0\n---\n'
        f'{ledger.START}\n```jsonl\n'
        + '\n'.join(json.dumps(row, sort_keys=True) for row in proof_rows)
        + f'\n```\n{ledger.END}\n',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.email', 'audit-test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'config', 'user.name', 'Audit Test'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '0-raw', '1-wiki', '2-outputs'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'raw proof'], check=True
    )

    occurrence_id = 'occurrence-1'
    start = host_preimage.rindex(b'Target')
    occurrence = {
        'occurrence_id': occurrence_id,
        'page_path': host_path,
        'target_path': target_path,
        'target_stem': 'target',
        'start_byte': start,
        'end_byte': start + len(b'Target'),
        'matched_text': 'Target',
    }
    context_hash = 'c' * 64
    baseline = {
        'schema_version': 1,
        'kind': 'audit-warning-baseline',
        'run_id': 'current-run',
        'baseline_id': 'baseline-current-run',
        'evidence_context_sha256': context_hash,
        'affected_page_preimages': {
            host_path: {
                'status': 'verified',
                'sha256': hashlib.sha256(host_preimage).hexdigest(),
                'verified_hash': host_body_hash,
                'bytes_base64': base64.b64encode(host_preimage).decode(),
            }
        },
        'enumerator': {'occurrences': [occurrence]},
    }
    baseline_path = '2-outputs/audit/baselines/current-run.json'
    baseline_file = tmp_path / baseline_path
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_data = json.dumps(baseline, sort_keys=True).encode()
    baseline_file.write_bytes(baseline_data)

    post_body = host_body.replace(
        'See Target.', f'See [[{target_path}|Target]].'
    )
    _, post_body_hash = write_verified_page(host_path, 'Host', post_body)
    postimage = host.read_bytes()
    transaction = {
        'schema_version': 1,
        'row_id': 'neutral-host',
        'run_id': 'current-run',
        'page_path': host_path,
        'preimage_sha256': hashlib.sha256(host_preimage).hexdigest(),
        'postimage_sha256': hashlib.sha256(postimage).hexdigest(),
        'postimage_bytes_base64': base64.b64encode(postimage).decode(),
        'before_status': 'verified',
        'after_status': 'verified',
        'verified_hash': post_body_hash,
        'baseline_occurrence_ids': [occurrence_id],
    }
    current_reconciliation = {
        'schema_version': 1,
        'row_type': 'reconciliation',
        'row_id': 'current-reconciliation',
        'run_id': 'current-run',
        'result': 'complete',
        'pending': 0,
        'warning_baseline_path': baseline_path,
        'warning_baseline_sha256': hashlib.sha256(baseline_data).hexdigest(),
        'warning_baseline_id': 'baseline-current-run',
        'evidence_context_sha256': context_hash,
        'mention_occurrences': [
            {**occurrence, 'disposition': 'genuine_wrap'}
        ],
        'neutral_page_transactions': [transaction],
    }
    current_manifest = {
        'schema_version': 1,
        'row_type': 'manifest',
        'row_id': 'current-manifest',
        'run_id': 'current-run',
        'mode': 'partial',
        'relationship_epoch': 'READY(1)',
    }
    for unit in (
        'pages', 'sources', 'claims', 'bullet_roles', 'page_readers',
        'scanners', 'status_writes',
    ):
        current_manifest[f'planned_{unit}'] = 0
        current_reconciliation[f'planned_{unit}'] = 0
        current_reconciliation[f'terminal_{unit}'] = 0
        current_reconciliation[f'pending_{unit}'] = 0
    report = _write_audit_report(
        tmp_path, [current_manifest, current_reconciliation]
    )
    return report, current_reconciliation, transaction, host_path, target_raw_path


def test_current_neutral_edge_carries_direct_target_raw_proof(tmp_path):
    report, reconciliation, _, host_path, _ = _neutral_bridge_fixture(tmp_path)
    edges = ledger._neutral_edges_from_report(
        repo_root=tmp_path,
        run_id='current-run',
        reconciliation=reconciliation,
    )
    assert edges
    assert ledger.pages_affected_by_raw_drift(
        repo_root=tmp_path, neutral_edges=edges
    ) == set()
    assert ledger.validate(report, tmp_path, recheck_quotes=False)['result'] == (
        'complete'
    )
    assert host_path not in ledger.mandatory_partial_wiki_pages(
        repo_root=tmp_path, neutral_edges=edges
    )


def test_current_neutral_edge_skips_nonverified_transaction(tmp_path):
    _, reconciliation, transaction, _, _ = _neutral_bridge_fixture(tmp_path)
    expected = ledger._neutral_edges_from_report(
        repo_root=tmp_path,
        run_id='current-run',
        reconciliation=reconciliation,
    )
    draft = dict(transaction)
    draft.update(
        {
            'row_id': 'neutral-draft',
            'page_path': '1-wiki/concepts/draft.md',
            'before_status': 'draft',
            'after_status': 'draft',
            'verified_hash': None,
        }
    )
    reconciliation['neutral_page_transactions'].append(draft)
    assert ledger._neutral_edges_from_report(
        repo_root=tmp_path,
        run_id='current-run',
        reconciliation=reconciliation,
    ) == expected


def test_current_neutral_edge_rejects_bad_postimage(tmp_path):
    report, reconciliation, transaction, _, _ = _neutral_bridge_fixture(tmp_path)
    original = transaction['postimage_bytes_base64']
    transaction['postimage_bytes_base64'] = base64.b64encode(b'forged').decode()
    assert ledger._neutral_edges_from_report(
        repo_root=tmp_path,
        run_id='current-run',
        reconciliation=reconciliation,
    ) == {}
    report.write_text(
        report.read_text(encoding='utf-8').replace(
            original, transaction['postimage_bytes_base64']
        ),
        encoding='utf-8',
    )
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'partial page inventory omits mandatory pages' in str(error)
    else:
        raise AssertionError('forged neutral postimage hid a mandatory page')


def test_current_neutral_edge_rejects_changed_raw(tmp_path):
    report, _, _, _, target_raw_path = _neutral_bridge_fixture(tmp_path)
    (tmp_path / target_raw_path).write_text('changed target evidence\n')
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'partial page inventory omits mandatory pages' in str(error)
    else:
        raise AssertionError('neutral edge hid a changed transitive raw')


def test_committed_raw_proof_rejects_nested_and_wrong_type_reports(tmp_path):
    for case_name, mutate in (
        ('nested', 'nested'),
        ('wrong-type', 'wrong-type'),
    ):
        repo = tmp_path / case_name
        repo.mkdir()
        _, reconciliation, _, host_path, _ = _neutral_bridge_fixture(repo)
        edges = ledger._neutral_edges_from_report(
            repo_root=repo,
            run_id='current-run',
            reconciliation=reconciliation,
        )
        pre_generation = next(iter(edges.values()))[0]
        proof = repo / '2-outputs/ingest/proof.md'
        if mutate == 'nested':
            nested = repo / '2-outputs/ingest/nested/proof.md'
            nested.parent.mkdir()
            proof.replace(nested)
        else:
            proof.write_text(
                proof.read_text(encoding='utf-8').replace(
                    'type: ingest-report', 'type: audit', 1
                ),
                encoding='utf-8',
            )
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(
            ['git', '-C', str(repo), 'commit', '-qm', mutate], check=True
        )
        assert (host_path, pre_generation) not in (
            ledger.committed_page_raw_proofs(repo_root=repo)
        )


def test_committed_raw_proof_rejects_forged_status_generation(tmp_path):
    _, reconciliation, _, host_path, _ = _neutral_bridge_fixture(tmp_path)
    edges = ledger._neutral_edges_from_report(
        repo_root=tmp_path,
        run_id='current-run',
        reconciliation=reconciliation,
    )
    pre_generation = next(iter(edges.values()))[0]
    proof = tmp_path / '2-outputs/ingest/proof.md'
    original = f'"pre_semantic_hash": "{pre_generation}"'
    assert original in proof.read_text(encoding='utf-8')
    proof.write_text(
        proof.read_text(encoding='utf-8').replace(
            original, f'"pre_semantic_hash": "{"f" * 64}"', 1
        ),
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '2-outputs/ingest/proof.md'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'forge status'],
        check=True,
    )
    assert (host_path, pre_generation) not in ledger.committed_page_raw_proofs(
        repo_root=tmp_path
    )


def test_committed_raw_proof_runs_actual_audit_completion_contract(tmp_path):
    _, reconciliation, _, host_path, _ = _neutral_bridge_fixture(tmp_path)
    edges = ledger._neutral_edges_from_report(
        repo_root=tmp_path,
        run_id='current-run',
        reconciliation=reconciliation,
    )
    pre_generation = next(iter(edges.values()))[0]
    ingest_proof = tmp_path / '2-outputs/ingest/proof.md'
    proof = tmp_path / '2-outputs/audit/proof.md'
    proof.parent.mkdir(parents=True, exist_ok=True)
    ingest_proof.replace(proof)
    lines = proof.read_text(encoding='utf-8').splitlines()
    proof.write_text(
        '\n'.join(
            line.replace('type: ingest-report', 'type: audit')
            for line in lines
        )
        + '\n',
        encoding='utf-8',
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'add', '-A'],
        check=True,
    )
    subprocess.run(
        ['git', '-C', str(tmp_path), 'commit', '-qm', 'invalid audit proof'],
        check=True,
    )
    assert (host_path, pre_generation) not in ledger.committed_page_raw_proofs(
        repo_root=tmp_path
    )

def test_audit_claim_manifest_matches_retained_bullet_inventory(tmp_path):
    for body in (
        '# Example\n',
        '# Example\n\n> [!idea]\n> - A claim.\n> - Extra claim.\n> ^idea\n',
        '# Example\n\n> [!idea]\n> - A claim.\n> - A claim.\n> ^idea\n',
    ):
        rows = _audit_rows(tmp_path)
        page = tmp_path / '1-wiki/concepts/example.md'
        _rebind_audit_page(rows=rows, page=page, body=body)
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert (
                'claim manifest does not match retained page' in str(error)
                or 'duplicate ordinal inventory differs' in str(error)
            )
        else:
            raise AssertionError(
                'audit accepted absent, extra, or duplicate retained bullets'
            )


def test_logical_bullet_extractor_handles_boundaries_and_nested_lists(
    tmp_path,
):
    page = tmp_path / 'page.md'
    page.write_text(
        '> [!idea]\n> - First claim.\n>\n> ![[image.png]]\n> ^idea\n\n'
        '> [!evidence]\n> - Parent claim:\n>     - nested evidence\n'
        '> ^evidence\n',
        encoding='utf-8',
    )
    assert ledger.extract_logical_bullets(page=page) == [
        '> - First claim.',
        '> - Parent claim:\n>     - nested evidence',
    ]
    assert ledger.extract_claim_records(page=page) == [
        {
            'claim_text': '> - First claim.',
            'callout_type': 'idea',
            'callout_id': 'idea',
        },
        {
            'claim_text': '> - Parent claim:\n>     - nested evidence',
            'callout_type': 'evidence',
            'callout_id': 'evidence',
        },
    ]


def test_claim_inventory_ignores_bullets_inside_fenced_code(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '> [!idea]\n> - Real claim.\n> ^real\n\n'
        '> ```markdown\n> - Example claim.\n> ```\n',
        encoding='utf-8',
    )
    assert ledger.extract_logical_bullets(page=page) == ['> - Real claim.']
    assert ledger.extract_claim_records(page=page) == [
        {
            'claim_text': '> - Real claim.',
            'callout_type': 'idea',
            'callout_id': 'real',
        },
    ]


def test_audit_claim_context_matches_retained_semantic_frontmatter(tmp_path):
    rows = _audit_rows(tmp_path)
    page = tmp_path / '1-wiki/concepts/example.md'
    page.write_text(
        page.read_text(encoding='utf-8').replace(
            'sources: [Example2026]', 'sources: [Other2026]'
        ),
        encoding='utf-8',
    )
    generation = ledger.semantic_page_digest(page=page)
    for row in rows:
        if row['row_type'] == 'page_reader':
            row['page_generation'] = generation
        elif row['row_type'] == 'status_write':
            row['page_generation'] = generation
            row['pre_semantic_hash'] = generation
            row['post_semantic_hash'] = generation
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'semantic_frontmatter differs from retained page' in str(error)
    else:
        raise AssertionError('audit accepted fabricated semantic frontmatter')


def test_audit_claim_context_matches_retained_callout(tmp_path):
    rows = _audit_rows(tmp_path)
    claim = next(row for row in rows if row['row_type'] == 'claim')
    old_id = claim['claim_instance_id']
    claim['callout_id'] = 'evidence'
    claim['claim_instance_id'] = ledger.expected_claim_id(claim)
    for row in rows:
        if row.get('claim_instance_id') == old_id:
            row['claim_instance_id'] = claim['claim_instance_id']
    page = tmp_path / '1-wiki/concepts/example.md'
    body = '# Example\n\n> [!evidence]\n> - A claim.\n> ^evidence\n'
    _rebind_audit_page(rows=rows, page=page, body=body)
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'callout_type differs from retained page' in str(error)
    else:
        raise AssertionError('audit accepted fabricated callout context')


def test_audit_claim_context_digest_is_current_page_generation(tmp_path):
    rows = _audit_rows(tmp_path)
    claim = rows[1]
    old_id = claim['claim_instance_id']
    claim['context_digest'] = 'b' * 64
    claim['claim_instance_id'] = ledger.expected_claim_id(claim)
    new_id = claim['claim_instance_id']
    for row in rows:
        if row.get('claim_instance_id') == old_id:
            row['claim_instance_id'] = new_id
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'context_digest differs from retained page' in str(error)
    else:
        raise AssertionError('audit accepted a fabricated context digest')


def test_audit_rejects_stale_row_run(tmp_path):
    rows = _audit_rows(tmp_path)
    rows[3]['run_id'] = 'old-run'
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'run_id differs from manifest' in str(error)
    else:
        raise AssertionError('audit accepted a page reader from another run')


def test_audit_rejects_whitespace_padded_placeholder_run(tmp_path):
    rows = _audit_rows(tmp_path)
    for row in rows:
        row['run_id'] = ' ... '
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'run_id is missing or a placeholder' in str(error)
    else:
        raise AssertionError('audit accepted a padded placeholder run_id')


def test_audit_rejects_stale_relationship_epoch(tmp_path):
    rows = _audit_rows(tmp_path)
    rows[3]['relationship_epoch'] = 'READY(1)'
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'stale epoch' in str(error)
    else:
        raise AssertionError('audit accepted a page reader from a stale epoch')


def test_audit_rejects_status_write_for_another_page(tmp_path):
    rows = _audit_rows(tmp_path)
    rows[5]['page_path'] = '1-wiki/concepts/missing.md'
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except (ledger.LedgerError, FileNotFoundError):
        pass
    else:
        raise AssertionError('audit accepted a status write for another page')


def test_audit_rejects_page_changed_after_reader_generation(tmp_path):
    rows = _audit_rows(tmp_path)
    page = tmp_path / '1-wiki/concepts/example.md'
    page.write_text(
        page.read_text(encoding='utf-8').replace(
            '# Example', '# Changed Example'
        ),
        encoding='utf-8',
    )
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'context_digest differs from retained page' in str(error)
    else:
        raise AssertionError(
            'audit accepted readers for a stale page generation'
        )


def test_audit_rejects_missing_or_mismatched_retained_status(tmp_path):
    rows = _audit_rows(tmp_path)
    page = tmp_path / '1-wiki/concepts/example.md'
    page.write_text('# Example\n', encoding='utf-8')
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError:
        pass
    else:
        raise AssertionError('audit accepted a retained page with no status')

    rows = _audit_rows(tmp_path)
    page.write_text(
        page.read_text(encoding='utf-8').replace(
            'status: verified', 'status: draft'
        ),
        encoding='utf-8',
    )
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'status write differs from retained page' in str(error)
    else:
        raise AssertionError('audit accepted a mismatched retained status')


def test_audit_rejects_forged_retained_verified_hash(tmp_path):
    rows = _audit_rows(tmp_path)
    page = tmp_path / '1-wiki/concepts/example.md'
    forged = 'd' * 64
    page.write_text(
        re.sub(
            r'verified_hash: [0-9a-f]{64}',
            f'verified_hash: {forged}',
            page.read_text(encoding='utf-8'),
        ),
        encoding='utf-8',
    )
    status = next(row for row in rows if row['row_id'] == 'status')
    status['verified_hash'] = forged
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'verified_hash differs from retained page' in str(error)
    else:
        raise AssertionError('audit accepted a forged retained verified_hash')


def test_semantic_page_digest_ignores_terminal_bookkeeping(tmp_path):
    page = tmp_path / 'page.md'
    page.write_text(
        '---\ntype: concept\nstatus: draft\nupdated: 2026-08-05\n---\n'
        '> - *[unverified]* Claim.\n',
        encoding='utf-8',
    )
    before = ledger.semantic_page_digest(page=page)
    page.write_text(
        '---\ntype: concept\nstatus: verified\nupdated: 2026-08-06\n'
        f'verified_hash: {"a" * 64}\n---\n> - Claim.\n',
        encoding='utf-8',
    )
    assert ledger.semantic_page_digest(page=page) == before


def test_audit_rejects_promotion_after_non_hold_page_verdict(tmp_path):
    for verdict in ('refute', 'cannot_confirm'):
        rows = _audit_rows(tmp_path)
        rows[3]['verdict'] = verdict
        rows[3]['defects'] = [
            {
                'scope': 'page_only',
                'detail': 'Unsupported conclusion',
            }
        ]
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'lacks needs-update hand-off' in str(error)
        else:
            raise AssertionError(
                f'audit accepted verified status after page {verdict}'
            )


def test_audit_non_hold_page_reader_cannot_end_draft(tmp_path):
    rows = _audit_rows(tmp_path)
    page_reader = next(
        row for row in rows if row['row_type'] == 'page_reader'
    )
    page_reader['verdict'] = 'refute'
    page_reader['defects'] = [
        {'scope': 'page_only', 'detail': 'Unsupported page conclusion'}
    ]
    page = tmp_path / '1-wiki/concepts/example.md'
    page_text = page.read_text(encoding='utf-8')
    page_text = page_text.replace('status: verified', 'status: draft')
    page_text = re.sub(
        r'^verified_hash:.*\n',
        '',
        page_text,
        flags=re.MULTILINE,
    )
    page.write_text(page_text, encoding='utf-8')
    status = next(row for row in rows if row['row_type'] == 'status_write')
    status['before_status'] = 'verified'
    status['after_status'] = 'draft'
    status.pop('verified_hash')
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'lacks needs-update hand-off' in str(error)
    else:
        raise AssertionError('non-HOLD page defect ended as bare draft')


def test_audit_fully_held_page_cannot_end_draft(tmp_path):
    rows = _audit_rows(tmp_path)
    page = tmp_path / '1-wiki/concepts/example.md'
    page_text = page.read_text(encoding='utf-8')
    page_text = page_text.replace('status: verified', 'status: draft')
    page_text = re.sub(
        r'^verified_hash:.*\n',
        '',
        page_text,
        flags=re.MULTILINE,
    )
    page.write_text(page_text, encoding='utf-8')
    status = next(row for row in rows if row['row_type'] == 'status_write')
    status['after_status'] = 'draft'
    status.pop('verified_hash')
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'fully held page lacks verified terminal status' in str(error)
    else:
        raise AssertionError('fully held page remained unexplained draft')


def test_audit_rejects_bullet_verdict_from_stale_epoch(tmp_path):
    rows = _audit_rows(tmp_path)
    manifest = rows[0]
    claim = rows[1]
    claim['classification'] = 'required'
    claim.pop('exemption_reason')
    terminal = next(row for row in rows if row['row_id'] == 'terminal')
    terminal['disposition'] = 'backfilled_hold'
    terminal['role_rows'] = ['locator_bullet', 'entailment_bullet']
    manifest['planned_bullet_roles'] = 2
    reconciliation = next(
        row for row in rows if row['row_id'] == 'reconciliation'
    )
    reconciliation['planned_bullet_roles'] = 2
    reconciliation['terminal_bullet_roles'] = 2
    bullet_rows = [
        {
            'schema_version': 1,
            'row_type': 'bullet_verdict',
            'row_id': role,
            'run_id': 'run',
            'relationship_epoch': epoch,
            'claim_instance_id': claim['claim_instance_id'],
            'role': role,
            'role_version': '1',
            'agent_id': agent,
            'blind_to': [
                (
                    'entailment_bullet'
                    if role == 'locator_bullet'
                    else 'locator_bullet'
                )
            ],
            'verdict': 'hold',
            'reasoning': 'The quote supports the exact claim.',
            'confidence': 'high',
            'correction': None,
            'quote_validated': True,
        }
        for role, agent, epoch in (
            ('locator_bullet', 'locator-agent', 'READY(1)'),
            ('entailment_bullet', 'entailment-agent', 'READY(2)'),
        )
    ]
    rows[2:2] = bullet_rows
    _bind_audit_claim_to_raw(rows=rows, tmp_path=tmp_path)
    report = _write_audit_report(tmp_path, rows)
    try:
        ledger.validate(report, tmp_path, recheck_quotes=False)
    except ledger.LedgerError as error:
        assert 'bullet verdict has stale epoch' in str(error)
    else:
        raise AssertionError(
            'audit accepted a bullet verdict from a stale epoch'
        )


def test_audit_rejects_promotion_after_non_hold_required_claim(tmp_path):
    for disposition, outcomes in (
        ('refute', ('refute', 'hold')),
        ('cannot_confirm', ('cannot_confirm', 'hold')),
    ):
        rows = _audit_rows(tmp_path)
        manifest = rows[0]
        claim = rows[1]
        claim['classification'] = 'required'
        claim.pop('exemption_reason')
        terminal = next(row for row in rows if row['row_id'] == 'terminal')
        terminal['disposition'] = disposition
        terminal['role_rows'] = [
            'locator_bullet',
            'entailment_bullet',
        ]
        manifest['planned_bullet_roles'] = 2
        reconciliation = next(
            row for row in rows if row['row_id'] == 'reconciliation'
        )
        reconciliation['planned_bullet_roles'] = 2
        reconciliation['terminal_bullet_roles'] = 2
        bullet_rows = [
            {
                'schema_version': 1,
                'row_type': 'bullet_verdict',
                'row_id': role,
                'run_id': 'run',
                'relationship_epoch': 'READY(2)',
                'claim_instance_id': claim['claim_instance_id'],
                'role': role,
                'role_version': '1',
                'agent_id': agent,
                'blind_to': [
                    (
                        'entailment_bullet'
                        if role == 'locator_bullet'
                        else 'locator_bullet'
                    )
                ],
                'verdict': verdict,
                'reasoning': 'The role reached its independent verdict.',
                'confidence': 'high',
                'correction': None,
                'quote_validated': verdict == 'hold',
            }
            for role, agent, verdict in (
                ('locator_bullet', 'locator-agent', outcomes[0]),
                ('entailment_bullet', 'entailment-agent', outcomes[1]),
            )
        ]
        rows[2:2] = bullet_rows
        _bind_audit_claim_to_raw(rows=rows, tmp_path=tmp_path)
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'non-HOLD claim lacks needs-update hand-off' in str(error)
        else:
            raise AssertionError(
                f'audit accepted verified status after claim {disposition}'
            )
        page = tmp_path / '1-wiki/concepts/example.md'
        page_text = page.read_text(encoding='utf-8')
        page_text = page_text.replace('status: verified', 'status: draft')
        page_text = re.sub(
            r'^verified_hash:.*\n',
            '',
            page_text,
            flags=re.MULTILINE,
        )
        page.write_text(page_text, encoding='utf-8')
        status = next(
            row for row in rows if row['row_type'] == 'status_write'
        )
        status['after_status'] = 'draft'
        status.pop('verified_hash')
        report = _write_audit_report(tmp_path, rows)
        try:
            ledger.validate(report, tmp_path, recheck_quotes=False)
        except ledger.LedgerError as error:
            assert 'non-HOLD claim lacks needs-update hand-off' in str(error)
        else:
            raise AssertionError(
                f'audit hid claim {disposition} behind draft status'
            )
        if disposition == 'refute':
            refute_row = next(
                row
                for row in rows
                if row.get('row_type') == 'bullet_verdict'
                and row.get('verdict') == 'refute'
            )
            refute_row.pop('quote')
            refute_row.pop('quote_raw_path')
            refute_row.pop('structural_anchor')
            report = _write_audit_report(tmp_path, rows)
            try:
                ledger.validate(report, tmp_path, recheck_quotes=False)
            except ledger.LedgerError as error:
                assert 'REFUTE row lacks located evidence' in str(error)
            else:
                raise AssertionError('audit accepted unlocated REFUTE')
        if disposition == 'cannot_confirm':
            cannot_row = next(
                row
                for row in rows
                if row.get('row_type') == 'bullet_verdict'
                and row.get('verdict') == 'cannot_confirm'
            )
            cannot_row.pop('search_summary')
            report = _write_audit_report(tmp_path, rows)
            try:
                ledger.validate(report, tmp_path, recheck_quotes=False)
            except ledger.LedgerError as error:
                assert 'lacks exhausted-search evidence' in str(error)
            else:
                raise AssertionError(
                    'audit accepted unevidenced CANNOT_CONFIRM'
                )
