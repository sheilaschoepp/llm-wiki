#!/usr/bin/env python3
"""Run the consistency check battery from consistency/SKILL.md in Python.

Usage:
    check_consistency.py <project-root>
    check_consistency.py <project-root> --checks A,B,C
    check_consistency.py <project-root> --packet schema-language
    check_consistency.py --list-checks

Replaces the bash + grep one-liners that previously sat inline in SKILL.md.
Output: JSON list of findings, printed to stdout. Each finding has:
    - check_id: the descriptive snake_case identifier of the check (e.g.
      referenced_paths_exist), matching CHECK_MANIFEST and --list-checks
    - file: relative path
    - line: int or null
    - message: one-sentence description
    - fix_hint: concrete fix

The script is read-only — it surfaces findings; SKILL.md's procedure decides
whether to apply fixes mechanically or surface for user approval.

Tracked patterns and constants are pulled out so future schema changes
update one place. Keeps SKILL.md prose focused on procedure, not regex.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Patterns the schema has retired. Lines matching these in any tracked file
# are stale.
REMOVED_FEATURE_PATTERNS = ['working_copy', 'working copy']

# Stale old-schema wording. These phrases usually indicate the previous
# citation-heavy template or retired callout names survived a schema rewrite.
STALE_SCHEMA_PHRASES = [
    'literature note',
    'literature notes',
    'literature-note',
    'literature-notes',
    'permanent note',
    'permanent notes',
    'permanent-note',
    'permanent-notes',
    'source note',
    'source notes',
    'source-note',
    'source-notes',
    'synthesis note',
    'synthesis notes',
    'synthesis-note',
    'synthesis-notes',
    "wikilink to that source's page",
    "wikilink to the cited source's page",
    "wikilink to the source's page",
    'what-sources-say',
    'what-it-is',
    'citation-attached',
    'Sections 1–5 carry citations',
    'Sections 1-5 carry citations',
    'full `([[Source]]',
]

# Working-skill-count prose patterns (working_skill_count_prose). Catches both "the eleven" /
# "eleven skills" / "eleven operation skills" forms across the wiki.
SKILL_COUNT_PROSE = re.compile(
    r'\b(ten|eleven|twelve)\s+(operation\s+)?skills?\b|'
    r'\bthe\s+(ten|eleven|twelve)\b',
    re.IGNORECASE,
)

# Meta-skills excluded from the working-skill count (CLAUDE.md Operations
# section: consistency, skill-linter, skill-llm-council, checkup, and cleanup
# are project-scoped meta-skills).
META_SKILL_NAMES = {'consistency', 'skill-linter', 'skill-llm-council', 'checkup', 'cleanup'}

# Standalone skills deliberately kept out of the project catalogues: skills that
# serve some out-of-band purpose rather than the wiki workflow, and so are exempt
# from the Operations list, the directory tree, and the output-kind naming registry.
# Their on-disk skill folders and `2-outputs/` folders must not be flagged as
# missing from those catalogues (same exemption shape as OUTPUT_ARCHIVE_DIRS).
# Currently empty — no standalone skill exists. Add a folder name here to exempt
# a future one.
STANDALONE_SKILL_NAMES: set[str] = set()

EXPECTED_SECTIONS = {
    'source': ['tldr', 'contribution', 'key-claims', 'evidence', 'method',
               'assumptions', 'limitations', 'appraisal', 'concepts-entities',
               'contradictions', 'open-questions', 'connections'],
    'entity': ['idea', 'why', 'not-this', 'examples', 'contradictions',
               'disconfirming', 'open-questions', 'connections', 'sources'],
    'concept': ['idea', 'why', 'not-this', 'examples', 'contradictions',
                'disconfirming', 'open-questions', 'connections', 'sources'],
    'synthesis': ['question', 'answer', 'scope', 'evidence', 'tensions',
                  'what-would-change-this', 'open-questions', 'connections',
                  'sources'],
}

# referenced_paths_exist: backticked path-like strings whose targets should exist on disk.
# Only match candidates that start with a known top-level prefix or are one of
# a small set of repo-root files. Placeholder/template paths are skipped.
PATH_PREFIXES = ('0-raw/', '1-wiki/', '2-outputs/', 'a-archive/',
                 '.claude/', '.obsidian/')
TOPLEVEL_FILES = {'CLAUDE.md', 'README.md', 'MEMORY.md'}
PLACEHOLDER_TOKENS = ('{', '}', '*', '<', '>', 'YYYY', 'MM-DD', 'HHMM',
                      '$', '...')
PATH_IN_BACKTICKS = re.compile(r'`([^`\n]+?)`')
# Markdown link target: [text](path). The path group excludes spaces and
# closing parens so we don't capture across links or stop early on '(' inside
# a path. URL targets are filtered later by PATH_PREFIXES.
MARKDOWN_LINK_RE = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
BASH_FENCE_LANGS = {'bash', 'sh', 'shell', 'zsh', 'console'}

CALLOUT_RE = re.compile(r'^> \[!([a-z-]+)\]', re.MULTILINE)
WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
REQUIRED_CALLOUTS = sorted({slug for slugs in EXPECTED_SECTIONS.values()
                            for slug in slugs})

# AI-writing tells (ai_writing_tells). Mechanical/regex-friendly tells only — semantic
# tells (puffing tone, broader-context reflex, etc.) belong in audit. Source
# list: a-archive/style/ai-writing-tells.md. Each entry: (label, severity,
# pattern, fix_hint).
AI_TELL_PATTERNS: list[tuple[str, str, re.Pattern[str], str]] = [
    ('high-density AI vocabulary', 'warning',
     re.compile(
         r'\b(delve[sd]?|delving|meticulous(?:ly)?|pivotal|tapestry|'
         r'showcas(?:e[sd]?|ing)|garner(?:ed|ing|s)?|'
         r'intricate(?:ly)?|intricacies|interplay|'
         r'testament|vibrant|bolster(?:ed|ing|s)?|enduring)\b',
         re.IGNORECASE),
     'Replace with a plainer word; see ai-writing-tells.md vocabulary list.'),
    ('significance-puffing phrase', 'warning',
     re.compile(
         r'\b(stands as|serves as a|is a testament to|'
         r'plays a (?:vital|significant|crucial|pivotal|key) role|'
         r'evolving landscape|rich (?:cultural )?heritage|'
         r'diverse (?:array|tapestry)|nestled in|in the heart of|'
         r'setting the stage for|key turning point)\b',
         re.IGNORECASE),
     'Cut the puffery; state the specific fact.'),
    ('hedging / knowledge-cutoff tell', 'warning',
     re.compile(
         r'\b(as of (?:my (?:last )?(?:knowledge|training) '
         r'(?:update|cutoff)|the time of writing)|'
         r'as an AI language model|as a large language model|'
         r'in the (?:provided|available) (?:sources|search results))\b',
         re.IGNORECASE),
     'Drop the hedge; use the certain / believe-but-verify / guessing '
     'scheme from CLAUDE.md.'),
    ('citation-markup leakage', 'error',
     re.compile(
         r':contentReference\[oaicite:|oai_citation|turn0search\d+|'
         r'cite turn0search|attached_file:\d+|grok_card'),
     'Strip the leaked AI citation markup.'),
    ('placeholder leakage', 'error',
     re.compile(
         r'\[Your Name\]|\[Insert (?:Date|Time|Name|Topic|Source)\]|'
         r"\[Entertainer's Name\]|INSERT_SOURCE_URL|"
         r'PASTE_[A-Z_]+_HERE|\[link to revised article\]'),
     'Fill in the placeholder or remove the line.'),
    ('UTM parameter leakage', 'warning',
     re.compile(
         r'utm_source=(?:chatgpt\.com|openai|copilot\.com)|'
         r'referrer=grok\.com'),
     'Strip the UTM parameter from the URL.'),
    ('Subject: header in body', 'warning',
     re.compile(r'^Subject:\s', re.MULTILINE),
     'Remove the leftover email-style subject line.'),
    ('footnote-arrow leakage', 'warning',
     re.compile(r'↩'),
     'Remove the leaked footnote arrow character.'),
    ('negative-parallelism cliche', 'suggestion',
     re.compile(r'\bnot only [^,\n]{1,80}, but also\b', re.IGNORECASE),
     'Restructure as plain prose.'),
    ("'Despite challenges' conclusion template", 'suggestion',
     re.compile(r'^Despite (?:its |these |the )?challenges,',
                re.MULTILINE | re.IGNORECASE),
     'Name the specific challenge or drop the sentence.'),
]

CHECK_MANIFEST = [
    {
        'check_id': 'retired_feature_mentions',
        'packet': 'schema-language',
        'name': 'retired feature mentions',
        'scope': 'CLAUDE.md, README.md, 1-wiki/, .claude/skills/',
    },
    {
        'check_id': 'working_skill_count_prose',
        'packet': 'schema-language',
        'name': 'working-skill count prose',
        'scope': 'CLAUDE.md, README.md, .claude/skills/*/SKILL.md',
    },
    {
        'check_id': 'old_schema_wording',
        'packet': 'schema-language',
        'name': 'old schema wording',
        'scope': 'CLAUDE.md, README.md, .claude/skills/',
    },
    {
        'check_id': 'placeholder_consistency',
        'packet': 'wiki-pages',
        'name': 'placeholder consistency',
        'scope': '1-wiki/sources, entities, concepts, syntheses',
    },
    {
        'check_id': 'body_section_order',
        'packet': 'wiki-pages',
        'name': 'body section order',
        'scope': '1-wiki/sources, entities, concepts, syntheses',
    },
    {
        'check_id': 'source_venue_year_split',
        'packet': 'wiki-pages',
        'name': 'source venue-year split',
        'scope': '1-wiki/sources',
    },
    {
        'check_id': 'index_vs_files_drift',
        'packet': 'wiki-pages',
        'name': 'index-vs-files drift',
        'scope': '1-wiki/index.md and wiki page folders',
    },
    {
        'check_id': 'attachments_folder_coverage',
        'packet': 'wiki-pages',
        'name': 'attachments folder presence and stem coverage',
        'scope': '1-wiki/attachments and 1-wiki/sources',
    },
    {
        'check_id': 'callout_css_coverage',
        'packet': 'styles-files',
        'name': 'callout CSS coverage',
        'scope': '.obsidian/snippets/custom_callouts.css',
    },
    {
        'check_id': 'gitkeep_coverage',
        'packet': 'styles-files',
        'name': 'non-hidden folder .gitkeep coverage',
        'scope': 'all non-hidden folders outside hidden project config',
    },
    {
        'check_id': 'referenced_paths_exist',
        'packet': 'styles-files',
        'name': 'referenced file paths exist',
        'scope': '.claude/skills/ and README.md',
    },
    {
        'check_id': 'orphan_skill_scripts',
        'packet': 'styles-files',
        'name': 'orphan skill scripts',
        'scope': '.claude/skills/*/scripts/',
    },
    {
        'check_id': 'personal_info_leakage',
        'packet': 'styles-files',
        'name': 'personal information leakage',
        'scope': 'repo-wide except 0-raw/, a-archive/ (which contains about-me/), 2-outputs/, .git/, .obsidian/, and the STANDALONE_SKILL_NAMES folders',
    },
    {
        'check_id': 'identity_term_leakage',
        'packet': 'styles-files',
        'name': 'identity term leakage',
        'scope': 'repo-wide except 0-raw/, a-archive/ (which contains about-me/), 2-outputs/, .git/, .obsidian/, and the STANDALONE_SKILL_NAMES folders',
    },
    {
        'check_id': 'domain_literature_leakage',
        'packet': 'styles-files',
        'name': 'domain literature leakage',
        'scope': "CLAUDE.md + .claude/skills/** text files including scripts; the structural exemptions are *-memory.md journals, the agent-writable curated data files in AGENT_DATA_FILES (hyphenation-lists / unlinked-mention-ignore / pagination-map — data, not logic, whose content is by construction the vault's own), and the STANDALONE_SKILL_NAMES folders. Flags bibkey-pattern paper citations not in the placeholder allowlist (PLACEHOLDER_BIBKEYS); these leak a vault's research-corpus literature into generic infra. Legitimate citations in any other domain-specific skill are recorded as sanctioned exceptions in consistency-memory.md, not special-cased in the check. Domain terms and claims are left to the judgment-drift packet. Root-level proposals.",
    },
    {
        'check_id': 'ai_writing_tells',
        'packet': 'ai-writing-tells',
        'name': 'AI-writing tells in project docs',
        'scope': 'CLAUDE.md, README.md, MEMORY.md, a-archive/style/, .claude/skills/*/SKILL.md and references',
    },
    {
        'check_id': 'file_naming_consistency',
        'packet': 'naming',
        'name': 'file naming consistency',
        'scope': '1-wiki/ (kebab-case), 2-outputs/{kind}/ (dated form), .claude/skills/ (kebab-case)',
    },
    {
        'check_id': 'filename_references_resolve',
        'packet': 'styles-files',
        'name': 'filename references resolve',
        'scope': 'CLAUDE.md, README.md, MEMORY.md, .claude/skills/**/*.md, a-archive/**/*.md, 1-wiki/**/*.md — backticked bare filenames must exist somewhere in the repo',
    },
    {
        'check_id': 'memory_file_graduation_prompt',
        'packet': 'styles-files',
        'name': 'memory file graduation prompt',
        'scope': 'MEMORY.md (cap 15, graduates to CLAUDE.md), .claude/skills/multi-skill/multi-skill-memory.md, and each .claude/skills/<skill>/<skill>-memory.md (cap 10) — marks files above their soft entry cap as graduation candidates; the per-entry graduation audit reads the content',
    },
    {
        'check_id': 'dir_tree_drift',
        'packet': 'styles-files',
        'name': 'CLAUDE.md directory tree drift',
        'scope': "CLAUDE.md — parses the ASCII directory tree under 'Directory Structure' and compares it to the actual repo: tree entries that don't exist on disk are flagged stale; on-disk paths that should appear in the tree (top-level docs, top-level dirs, immediate children of 0-raw/, 2-outputs/, a-archive/, plus 1-wiki/'s hot/index/log files and child dirs, plus .claude/skills/) but are missing are flagged. STANDALONE_SKILL_NAMES output folders are exempt — kept out of the tree by design; OUTPUT_EXEMPT_DIRS user-owned free-form folders are exempt the same way.",
    },
    {
        'check_id': 'unbackticked_paths_resolve',
        'packet': 'styles-files',
        'name': 'unbackticked schema-prefix path references resolve',
        'scope': "CLAUDE.md — finds path-shaped tokens starting with a known schema prefix (0-raw/, 1-wiki/, 2-outputs/, a-archive/, .claude/) in prose outside backticks and code fences, and verifies each resolves to an existing path. Pairs with filename_references_resolve (which scans backticked filenames); together they catch path drift regardless of backtick convention.",
    },
    {
        'check_id': 'operations_list_matches_skills',
        'packet': 'schema-language',
        'name': 'CLAUDE.md Operations list matches skill folders',
        'scope': "CLAUDE.md '## Operations' section vs '.claude/skills/*/'. Parses bulleted skill names in the Operations section and cross-checks both directions: skills listed in CLAUDE.md but missing on disk are flagged stale, and skill folders on disk that are missing from the Operations list are flagged. STANDALONE_SKILL_NAMES skills are dropped from both sides — they are deliberately out of the catalogue.",
    },
    {
        'check_id': 'retired_skill_references',
        'packet': 'schema-language',
        'name': 'retired/merged skill names not routed to',
        'scope': "CLAUDE.md, README.md, and .claude/skills/ bodies and scripts. Flags references that route to a skill that no longer exists after a merge or rename. `ingest-deep` (now ingest's deep mode) is flagged anywhere it appears; `reingest` (now ingest's existing-source mode) is flagged only in its routing form — backticked `reingest` or the /reingest slash command — because unbackticked 'reingest' survives as legitimate mode vocabulary. Also resolves the 'operation/meta skills `...`' required-skills enumeration: every backticked skill name there must be a current skill folder. Exempts the owning ingest/ folder (mode-verb log template), the consistency/ folder (documents this check), and *-memory.md history.",
    },
    {
        'check_id': 'section_lists_match_schema',
        'packet': 'schema-language',
        'name': 'section lists match schema',
        'scope': "CLAUDE.md '### Required Callout Sections' vs EXPECTED_SECTIONS in the script. Parses the numbered slug lists for source, concept/entity, and synthesis pages and asserts they equal the script's hardcoded copy, so a section-template edit in CLAUDE.md cannot silently leave body_section_order enforcing the old schema. Findings are root-level proposals.",
    },
    {
        'check_id': 'output_kinds_match_disk',
        'packet': 'naming',
        'name': 'output kinds match disk',
        'scope': "OUTPUT_KIND_DIRS in the script vs the on-disk 2-outputs/ subfolders (minus the quarantined/superseded archive folders, the OUTPUT_EXEMPT_DIRS free-form folders, and the STANDALONE_SKILL_NAMES output folders). Flags an output folder that exists but is absent from OUTPUT_KIND_DIRS (its files would escape file_naming_consistency) and a listed kind whose folder is missing while its owning skill still exists. Standalone skills are exempt. Findings are root-level proposals (the constant lives in the script).",
    },
    {
        'check_id': 'catalogue_matches_manifest',
        'packet': 'schema-language',
        'name': 'catalogue matches manifest',
        'scope': "references/checks.md per-check catalogue vs the script's CHECK_MANIFEST / PACKET_CHECKS. Parses the '## Packet:' sections, their bullet check_ids, and the stated total and per-packet counts, and asserts they match the live manifest. Guards the doc copy the SKILL.md catalogue refactor moved into references/checks.md. Findings are root-level proposals (the file lives in the consistency skill).",
    },
    {
        'check_id': 'shared_reference_integrity',
        'packet': 'styles-files',
        'name': 'shared multi-skill references are shared and single-copy',
        'scope': "`.claude/skills/multi-skill/references/*.md` vs the skill tree. Each shared reference must be (a) cited by >= 2 distinct skills — that location is for genuinely cross-skill material; a reference used by one skill belongs in that skill's own references/ — and (b) a single copy, with no same-named references/<file> duplicated in any skill folder. Motivating case: verification.md, run by ingest (Step 8) and query (page-authoring path). CLAUDE.md -> Stay In Your Lane. Root-level proposals.",
    },
]

MEMORY_FILE_ENTRY_CAP = 10
# MEMORY.md is the consolidation tier (graduation destination), so it sits at a
# higher cap than the append-only journals and graduates only outward to CLAUDE.md.
MEMORY_MD_ENTRY_CAP = 15

PACKET_CHECKS: dict[str, list[str]] = {}
for item in CHECK_MANIFEST:
    PACKET_CHECKS.setdefault(item['packet'], []).append(item['check_id'])


def finding(check_id: str, file: str, message: str,
            fix_hint: str = '', line: int | None = None) -> dict[str, Any]:
    """Build a finding dict from check ID, file, message, and fix hint."""
    return {
        'check_id': check_id,
        'file': file,
        'line': line,
        'message': message,
        'fix_hint': fix_hint,
    }


def search_files(root: Path, patterns: list[str], paths: list[str],
                 exclude_paths: Sequence[str] = ()) -> list[tuple[Path, int, str]]:
    """Return (path, line_no, line_content) for every line in `paths` matching
    any of `patterns`, with substring-match exclusions applied."""
    hits: list[tuple[Path, int, str]] = []
    for rel in paths:
        full = root / rel
        if not full.exists():
            continue
        if full.is_file():
            files = [full]
        else:
            files = list(full.rglob('*.md'))
        for f in files:
            relstr = str(f.relative_to(root))
            if any(ex in relstr for ex in exclude_paths):
                continue
            try:
                lines = f.read_text(encoding='utf-8').splitlines()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for i, line in enumerate(lines, start=1):
                if any(p in line for p in patterns):
                    hits.append((f, i, line))
    return hits


# retired_feature_mentions: removed-feature mentions outside the explicit retirement note.
def check_retired_feature_mentions(root: Path) -> list[dict[str, Any]]:
    findings = []
    hits = search_files(
        root=root,
        patterns=REMOVED_FEATURE_PATTERNS,
        paths=['CLAUDE.md', 'README.md', '1-wiki/', '.claude/skills/'],
        exclude_paths=['log.md', 'consistency/SKILL.md'],
    )
    for path, line_no, content in hits:
        relstr = str(path.relative_to(root))
        findings.append(finding(
            check_id='retired_feature_mentions',
            file=relstr,
            message=f'Removed-feature mention: {content.strip()[:120]}',
            fix_hint='Remove the stale reference or migrate to the current schema.',
            line=line_no,
        ))
    return findings


# working_skill_count_prose: skill-count prose vs actual working-skill folder count.
def check_working_skill_count_prose(root: Path) -> list[dict[str, Any]]:
    findings = []
    skills_dir = root / '.claude/skills'
    if not skills_dir.exists():
        return findings
    actual = sum(1 for p in skills_dir.iterdir()
                 if p.is_dir() and p.name not in META_SKILL_NAMES
                 and p.name not in STANDALONE_SKILL_NAMES
                 and (p / 'SKILL.md').exists())
    expected_word = {10: 'ten', 11: 'eleven', 12: 'twelve'}.get(actual, str(actual))

    # Walk files directly — search_files is substring-only and this check
    # needs the SKILL_COUNT_PROSE regex.
    for rel in ['CLAUDE.md', 'README.md']:
        full = root / rel
        if full.exists():
            for i, line in enumerate(full.read_text(encoding='utf-8').splitlines(),
                                     start=1):
                m = SKILL_COUNT_PROSE.search(line)
                if m:
                    word = m.group(1) or m.group(3) or ''
                    if word.lower() != expected_word:
                        findings.append(finding(
                            check_id='working_skill_count_prose',
                            file=rel,
                            message=f"Skill-count prose `{m.group(0)}` doesn't match "
                            f'actual working-skill count ({actual}).',
                            fix_hint=f'Update the prose to `{expected_word}`.',
                            line=i,
                        ))
    for skill_md in (root / '.claude/skills').rglob('SKILL.md'):
        if 'consistency' in str(skill_md):
            continue
        for i, line in enumerate(skill_md.read_text(encoding='utf-8').splitlines(),
                                 start=1):
            m = SKILL_COUNT_PROSE.search(line)
            if m:
                word = m.group(1) or m.group(3) or ''
                if word.lower() != expected_word:
                    findings.append(finding(
                        check_id='working_skill_count_prose',
                        file=str(skill_md.relative_to(root)),
                        message=f"Skill-count prose `{m.group(0)}` doesn't match "
                        f'actual working-skill count ({actual}).',
                        fix_hint=f'Update the prose to `{expected_word}`.',
                        line=i,
                    ))
    return findings


# old_schema_wording: stale old-schema wording.
def check_old_schema_wording(root: Path) -> list[dict[str, Any]]:
    findings = []
    paths = ['CLAUDE.md', 'README.md', '.claude/skills/']
    exclude_paths = ['consistency/SKILL.md']
    for rel in paths:
        full = root / rel
        if not full.exists():
            continue
        files = [full] if full.is_file() else list(full.rglob('*.md'))
        for path in files:
            relstr = str(path.relative_to(root))
            if any(ex in relstr for ex in exclude_paths):
                continue
            try:
                lines = path.read_text(encoding='utf-8').splitlines()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for line_no, content in enumerate(lines, start=1):
                lowered = content.lower()
                # Strip inline-code spans: a stale phrase inside backticks is a
                # quoted token or example (e.g. the `the source notes` example in
                # lint's vague_source_referent entry), not old-schema prose.
                probe = re.sub(r'`[^`]*`', '', lowered)
                if any(p in probe for p in STALE_SCHEMA_PHRASES):
                    findings.append(finding(
                        check_id='old_schema_wording',
                        file=relstr,
                        message=f'Stale old-schema wording: {content.strip()[:120]}',
                        fix_hint='Update to the current schema.',
                        line=line_no,
                    ))
    return findings


# placeholder_consistency: per-page placeholder uniformity.
def check_placeholder_consistency(root: Path) -> list[dict[str, Any]]:
    findings = []
    folders = [
        (root / '1-wiki/sources', 'source'),
        (root / '1-wiki/entities', 'entity'),
        (root / '1-wiki/concepts', 'concept'),
        (root / '1-wiki/syntheses', 'synthesis'),
    ]
    for folder, _kind in folders:
        if not folder.exists():
            continue
        for page in folder.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            placeholders = set()
            for line in text.splitlines():
                m = re.match(r'^> - (None [^.*]+?)(\.|$)', line.strip())
                if m:
                    placeholders.add(m.group(1).strip())
            if len(placeholders) > 1:
                findings.append(finding(
                    check_id='placeholder_consistency',
                    file=str(page.relative_to(root)),
                    message=f'Mixed empty-section placeholders on one page: '
                    f'{sorted(placeholders)}.',
                    fix_hint='Pick one canonical placeholder phrase and use it consistently.',
                ))
    return findings


# body_section_order: body section-order conformance per page type.
def check_body_section_order(root: Path) -> list[dict[str, Any]]:
    findings = []

    def get_kind(path: Path) -> str:
        parts = path.parts
        if 'sources' in parts:
            return 'source'
        if 'entities' in parts:
            return 'entity'
        if 'concepts' in parts:
            return 'concept'
        if 'syntheses' in parts:
            return 'synthesis'
        return ''

    for folder in ('1-wiki/sources', '1-wiki/entities', '1-wiki/concepts',
                   '1-wiki/syntheses'):
        full = root / folder
        if not full.exists():
            continue
        for page in full.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            kind = get_kind(path=page)
            expected = EXPECTED_SECTIONS.get(kind, [])
            actual = [m.group(1) for m in CALLOUT_RE.finditer(text)]
            if expected and actual != expected:
                findings.append(finding(
                    check_id='body_section_order',
                    file=str(page.relative_to(root)),
                    message=f"Section order doesn't match `{kind}` schema: "
                    f'got {actual}, expected {expected}.',
                    fix_hint='Reorder body callouts to match CLAUDE.md schema.',
                ))
    return findings


# source_venue_year_split: `venue:` field embeds a year.
def check_source_venue_year_split(root: Path) -> list[dict[str, Any]]:
    findings = []
    sources = root / '1-wiki/sources'
    if not sources.exists():
        return findings
    venue_year_re = re.compile(r'^venue:.*\b\d{4}\b', re.MULTILINE)
    for page in sources.glob('*.md'):
        text = page.read_text(encoding='utf-8')
        m = venue_year_re.search(text)
        if m:
            line_no = text[:m.start()].count('\n') + 1
            findings.append(finding(
                check_id='source_venue_year_split',
                file=str(page.relative_to(root)),
                message=f'`venue:` field embeds a year: {m.group(0).strip()}',
                fix_hint='Move the year to the separate `year:` field; venue should be '
                'the venue name only (e.g., `NeurIPS`, not `NeurIPS 2017`).',
                line=line_no,
            ))
    return findings


# index_vs_files_drift: index.md vs filesystem.
def check_index_vs_files_drift(root: Path) -> list[dict[str, Any]]:
    findings = []
    index = root / '1-wiki/index.md'
    if not index.exists():
        return findings
    text = index.read_text(encoding='utf-8')
    sections = [
        ('Sources', root / '1-wiki/sources', '## Entities'),
        ('Entities', root / '1-wiki/entities', '## Concepts'),
        ('Concepts', root / '1-wiki/concepts', '## Syntheses'),
        ('Syntheses', root / '1-wiki/syntheses', None),
    ]
    for name, folder, end_marker in sections:
        # Guard folder.exists() OUTSIDE the comprehension: folder.iterdir() in
        # the for-clause runs before any if-clause, so an in-comprehension
        # existence check does not protect the iterdir() call and a missing
        # wiki subfolder would raise FileNotFoundError mid-battery.
        present = sorted(p.stem for p in folder.iterdir()
                         if p.suffix == '.md') if folder.exists() else []
        m_start = re.search(rf'^## {name}\s*$', text, re.MULTILINE)
        if not m_start:
            continue
        body_start = m_start.end()
        if end_marker:
            m_end = re.search(rf'^{re.escape(end_marker)}\s*$',
                              text[body_start:], re.MULTILINE)
            section_body = text[body_start:body_start + m_end.start()] if m_end else text[body_start:]
        else:
            section_body = text[body_start:]
        # Wikilinks are path-qualified (`[[1-wiki/sources/foo.md|foo]]`);
        # normalize each target to its bare stem before comparing to files.
        listed = sorted({Path(x.strip()).stem
                         for x in WIKILINK_RE.findall(section_body)})
        rel_folder = str(folder.relative_to(root))
        for stem in sorted(set(present) - set(listed)):
            findings.append(finding(
                check_id='index_vs_files_drift',
                file='1-wiki/index.md',
                message=f"{name}: file `{stem}.md` exists but isn't listed in index.md.",
                fix_hint=f'Add `- [[{rel_folder}/{stem}.md|{stem}]]` to the '
                f'{name} section.',
            ))
        for stem in sorted(set(listed) - set(present)):
            findings.append(finding(
                check_id='index_vs_files_drift',
                file='1-wiki/index.md',
                message=f'{name}: index.md lists `{stem}.md` but no matching file.',
                fix_hint='Remove the entry or restore the file.',
            ))
    return findings


# gitkeep_coverage: every non-hidden folder has a .gitkeep.
def check_gitkeep_coverage(root: Path) -> list[dict[str, Any]]:
    findings = []
    excluded = {'.git', '.claude', '.obsidian'}
    for folder in root.rglob('*'):
        if not folder.is_dir():
            continue
        # Skip if any part is hidden / excluded.
        if any(part.startswith('.') or part in excluded
               for part in folder.relative_to(root).parts):
            continue
        if not (folder / '.gitkeep').exists():
            findings.append(finding(
                check_id='gitkeep_coverage',
                file=str(folder.relative_to(root)),
                message="Non-hidden folder missing `.gitkeep` (won't survive fresh clone).",
                fix_hint=f'touch `{folder.relative_to(root)}/.gitkeep`',
            ))
    return findings


# attachments_folder_coverage: `1-wiki/attachments/` is present and every stem subfolder
# corresponds to an existing source page.
def check_attachments_folder_coverage(root: Path) -> list[dict[str, Any]]:
    findings = []
    attachments = root / '1-wiki/attachments'
    sources = root / '1-wiki/sources'
    if not attachments.exists():
        # Schema requires the folder. Surface it once so a manual mkdir
        # restores the structure.
        findings.append(finding(
            check_id='attachments_folder_coverage',
            file='1-wiki/attachments',
            message='Required schema folder `1-wiki/attachments/` is missing.',
            fix_hint='Create `1-wiki/attachments/` and add a `.gitkeep`.',
        ))
        return findings
    if not sources.exists():
        return findings
    source_stems = {p.stem for p in sources.glob('*.md')}
    for stem_dir in sorted(attachments.iterdir()):
        if not stem_dir.is_dir():
            continue
        if stem_dir.name not in source_stems:
            findings.append(finding(
                check_id='attachments_folder_coverage',
                file=f'1-wiki/attachments/{stem_dir.name}',
                message=f'Attachment folder `{stem_dir.name}/` has no matching source '
                f'page at `1-wiki/sources/{stem_dir.name}.md`.',
                fix_hint='Quarantine the folder via /forget, or create the source page.',
            ))
    return findings


# callout_css_coverage: every required callout slug has a CSS style.
def check_callout_css_coverage(root: Path) -> list[dict[str, Any]]:
    findings = []
    css = root / '.obsidian/snippets/custom_callouts.css'
    if not css.exists():
        return [finding(
            check_id='callout_css_coverage',
            file='.obsidian/snippets/custom_callouts.css',
            message='Callout stylesheet is missing.',
            fix_hint='Create styles for the required callout slugs.',
        )]
    text = css.read_text(encoding='utf-8')
    for slug in REQUIRED_CALLOUTS:
        if f'data-callout="{slug}"' not in text:
            findings.append(finding(
                check_id='callout_css_coverage',
                file=str(css.relative_to(root)),
                message=f'Missing CSS style for callout `{slug}`.',
                fix_hint=f'Add `.callout[data-callout=\"{slug}\"]` to the stylesheet.',
            ))
    return findings


# referenced_paths_exist: backticked path references must exist on disk.
def check_referenced_paths_exist(root: Path) -> list[dict[str, Any]]:
    findings = []
    seen: set[tuple[str, str]] = set()
    # Scope: operational files where a missing referenced path is a real
    # bug. CLAUDE.md and MEMORY.md contain illustrative example paths (e.g.
    # `0-raw/papers/Vaswani2017AttentionIA.pdf`) that aren't expected to exist;
    # scanning them produces false positives, so they are out of scope.
    paths_to_scan = ['README.md', '.claude/skills/']
    exclude_paths = ['consistency/SKILL.md',
                     'consistency/scripts/check_consistency.py']
    file_line_re = re.compile(r':\d+$')
    for rel in paths_to_scan:
        full = root / rel
        if not full.exists():
            continue
        if full.is_file():
            files = [full]
        else:
            files = list(full.rglob('*.md'))
        for f in files:
            relstr = str(f.relative_to(root))
            if any(ex in relstr for ex in exclude_paths):
                continue
            try:
                lines = f.read_text(encoding='utf-8').splitlines()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            in_fence = False
            in_bash_block = False
            for i, line in enumerate(lines, start=1):
                stripped = line.lstrip()
                if stripped.startswith('```'):
                    fence_info = stripped[3:].strip().lower()
                    if not in_fence:
                        in_fence = True
                        # Only known shell langs get bash-token scanning.
                        in_bash_block = fence_info in BASH_FENCE_LANGS
                    else:
                        in_fence = False
                        in_bash_block = False
                    continue
                # Backtick/markdown-link scanning is suppressed inside ANY
                # fence (```python, ```yaml, ```text, ...), not just bash —
                # a backticked path inside a non-bash fence is an example,
                # not a live reference. Mirrors filename_references_resolve.
                if in_fence and not in_bash_block:
                    continue
                candidates: list[str] = []
                if not in_fence:
                    for m in PATH_IN_BACKTICKS.finditer(line):
                        candidates.append(m.group(1))
                    for m in MARKDOWN_LINK_RE.finditer(line):
                        candidates.append(m.group(1))
                if in_bash_block:
                    # Whitespace/quote/equals-separated tokens; PATH_PREFIXES
                    # filter keeps this from flagging system binaries or
                    # `cd` targets that aren't repo paths.
                    for tok in re.split(r"[\s'\"=]+", line):
                        if tok:
                            candidates.append(tok)
                for raw in candidates:
                    candidate = raw.strip().rstrip('.,;)')
                    candidate = file_line_re.sub('', candidate)
                    if not candidate or ' ' in candidate:
                        continue
                    if any(tok in candidate for tok in PLACEHOLDER_TOKENS):
                        continue
                    is_path = (candidate.startswith(PATH_PREFIXES)
                               or candidate in TOPLEVEL_FILES)
                    if not is_path:
                        continue
                    target_rel = candidate.rstrip('/')
                    target = root / target_rel
                    if target.exists():
                        continue
                    key = (relstr, candidate)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(finding(
                        check_id='referenced_paths_exist',
                        file=relstr,
                        message=f'Referenced path `{candidate}` does not exist in repo.',
                        fix_hint='Update the reference or restore the file/folder.',
                        line=i,
                    ))
    return findings


# orphan_skill_scripts: scripts under .claude/skills/*/scripts/ should be referenced by
# at least one SKILL.md. Unreferenced scripts are usually leftovers from
# rewrites or rename operations.
def _extract_skill_path_refs(text: str) -> list[str]:
    refs: list[str] = []
    in_fence = False
    in_bash = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('```'):
            fence = stripped[3:].strip().lower()
            if not in_fence:
                in_fence = True
                in_bash = fence in BASH_FENCE_LANGS
            else:
                in_fence = False
                in_bash = False
            continue
        # Skip backtick/link scanning inside any non-bash fence; bash fences
        # still get token extraction below.
        if in_fence and not in_bash:
            continue
        if not in_fence:
            for m in PATH_IN_BACKTICKS.finditer(line):
                refs.append(m.group(1))
            for m in MARKDOWN_LINK_RE.finditer(line):
                refs.append(m.group(1))
        if in_bash:
            for tok in re.split(r"[\s'\"=]+", line):
                if tok:
                    refs.append(tok)
    return refs


def check_orphan_skill_scripts(root: Path) -> list[dict[str, Any]]:
    findings = []
    skills_dir = root / '.claude/skills'
    if not skills_dir.exists():
        return findings
    referenced: set[str] = set()
    for skill_md in skills_dir.rglob('SKILL.md'):
        try:
            text = skill_md.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        skill_rel_dir = skill_md.parent.relative_to(root)
        for raw in _extract_skill_path_refs(text=text):
            cand = raw.strip().rstrip('.,;)')
            cand = re.sub(r':\d+$', '', cand)
            if cand.startswith('.claude/skills/'):
                referenced.add(cand.rstrip('/'))
            elif cand.startswith(('scripts/', 'references/', 'assets/')):
                # Relative to the skill's own folder.
                referenced.add(str(skill_rel_dir / cand).rstrip('/'))
    skip_suffixes = {'.pyc'}
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        scripts = skill_dir / 'scripts'
        if not scripts.exists():
            continue
        for f in sorted(scripts.rglob('*')):
            if not f.is_file():
                continue
            # Skip transient cache/dot directories under scripts/ (__pycache__,
            # .pytest_cache, .mypy_cache, .ruff_cache, …) — these are generated,
            # gitignored, and not skill scripts. Check components relative to
            # scripts/ so the leading `.claude` path segment is not matched.
            dir_parts = f.relative_to(scripts).parts[:-1]
            if any(p == '__pycache__' or p.startswith('.') for p in dir_parts):
                continue
            if f.name.startswith('.'):  # dotfiles (e.g. .gitkeep) are not scripts
                continue
            if f.suffix in skip_suffixes:
                continue
            rel = str(f.relative_to(root))
            if rel in referenced:
                continue
            findings.append(finding(
                check_id='orphan_skill_scripts',
                file=rel,
                message='Skill script is not referenced by any SKILL.md (likely orphan).',
                fix_hint="Reference it from the owning skill's SKILL.md, or remove the file.",
            ))
    return findings


# personal_info_leakage: personal information leakage outside about/.
# Conservative regexes — emails and clearly-formatted phone numbers — to keep
# false-positive noise low. Skips immutable raw sources, generated outputs,
# the archive folder, and the user's own about-me page.
EMAIL_RE = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')
PHONE_RE = re.compile(
    r'\(\d{3}\)\s*\d{3}[-.\s]\d{4}|\b\d{3}[-.]\d{3}[-.]\d{4}\b'
)
# Automated addresses that are never personal information — e.g. the
# Co-Authored-By commit-trailer email. Any 'noreply' local-part is skipped.
EMAIL_ALLOWLIST_LOCALPARTS = {'noreply'}


def _under_standalone_skill(path: Path, root: Path) -> bool:
    """True if path lies inside a STANDALONE_SKILL_NAMES skill folder.

    A standalone skill is wiki-orthogonal — it serves some out-of-band purpose,
    not the wiki — so the leakage/privacy checks skip its folder. The set is
    currently empty, so this returns False for every path.
    """
    parts = path.relative_to(root).parts
    return (len(parts) >= 3 and parts[0] == '.claude'
            and parts[1] == 'skills' and parts[2] in STANDALONE_SKILL_NAMES)


def check_personal_info_leakage(root: Path) -> list[dict[str, Any]]:
    findings = []
    excluded_top = {'.git', '0-raw', 'a-archive', '2-outputs', '.obsidian',
                    'about', 'about-me'}
    text_exts = {'.md', '.py', '.sh', '.css', '.json', '.yaml', '.yml',
                 '.txt', '.toml', '.cfg', '.ini'}
    seen: set[tuple[str, str]] = set()
    for f in sorted(root.rglob('*')):
        if not f.is_file():
            continue
        rel_parts = f.relative_to(root).parts
        if rel_parts and rel_parts[0] in excluded_top:
            continue
        if _under_standalone_skill(path=f, root=root):
            continue
        if '__pycache__' in rel_parts:
            continue
        # Files with no extension (e.g. .gitkeep is technically named with a
        # leading dot but has empty suffix here) — skip unless they're known
        # text. Skip suffix not in text_exts.
        if f.suffix and f.suffix not in text_exts:
            continue
        if f.name == '.gitkeep':
            continue
        try:
            content = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IsADirectoryError, PermissionError, OSError):
            continue
        rel = str(f.relative_to(root))
        for i, line in enumerate(content.splitlines(), start=1):
            for m in EMAIL_RE.finditer(line):
                if m.group(0).split('@', 1)[0].lower() in EMAIL_ALLOWLIST_LOCALPARTS:
                    continue
                key = (rel, 'email:' + m.group(0))
                if key in seen:
                    continue
                seen.add(key)
                findings.append(finding(
                    check_id='personal_info_leakage',
                    file=rel,
                    message=f'Possible personal information (email): {m.group(0)}',
                    fix_hint='Move to the about-me page (a-archive/about-me/about-me.md) or redact.',
                    line=i,
                ))
            for m in PHONE_RE.finditer(line):
                key = (rel, 'phone:' + m.group(0))
                if key in seen:
                    continue
                seen.add(key)
                findings.append(finding(
                    check_id='personal_info_leakage',
                    file=rel,
                    message=f'Possible personal information (phone): {m.group(0)}',
                    fix_hint='Move to the about-me page (a-archive/about-me/about-me.md) or redact.',
                    line=i,
                ))
    return findings


# identity_term_leakage: identity terms (the user's name, supervisors, lab, institution,
# personal URL handles) should appear only in about-me/about-me.md. Terms
# are auto-extracted from the Identity section of about-me/about-me.md so
# the check stays in sync as that file evolves.
URL_RE = re.compile(r'https?://[^\s)\]]+')
GENERIC_URL_TOKENS = {
    'www', 'com', 'org', 'net', 'ca', 'io', 'uk', 'us',
    'site', 'html', 'pdf', 'https', 'http',
    'github', 'linkedin', 'google', 'scholar', 'notion', 'citations',
    'in', 'user', 'page', 'pages', 'wiki',
    'example', 'test', 'localhost',
}


def _extract_personal_url_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for m in URL_RE.finditer(text):
        url = m.group(0)
        url = re.split(r'[?#)\]]', url)[0].rstrip('/.,;)')
        for part in re.split(r'[/.:]+', url):
            part = part.strip()
            if len(part) < 4:
                continue
            if part.lower() in GENERIC_URL_TOKENS:
                continue
            tokens.add(part)
    return tokens


def _load_identity_terms(root: Path) -> tuple[set[str], set[str]]:
    # The canonical file is named about-me.md inside a-archive/about-me/.
    # Older layouts (a-archive/about/, about-me/, about/) are kept as
    # fallbacks so the check still locates the file if the layout shifts.
    candidates = [root / 'a-archive' / 'about-me' / 'about-me.md',
                  root / 'a-archive' / 'about' / 'about-me.md',
                  root / 'about-me' / 'about-me.md',
                  root / 'about' / 'about-me.md']
    about = next((p for p in candidates if p.exists()), None)
    if about is None:
        return set(), set()
    try:
        text = about.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return set(), set()
    section_match = re.search(
        r'^## Identity\s*\n(.*?)(?=^## |\Z)',
        text,
        re.MULTILINE | re.DOTALL,
    )
    section = section_match.group(1) if section_match else ''
    terms: set[str] = set()
    field_re = re.compile(
        r'\*\*(Name|Institution|Lab|Supervisors)\*\*:\s*(.+)$',
        re.MULTILINE,
    )
    for fm in field_re.finditer(section):
        field = fm.group(1)
        value = fm.group(2)
        # Capture parenthesized acronyms (e.g., a parenthesized lab name).
        for paren in re.findall(r'\(([^)]+)\)', value):
            paren = paren.strip()
            if any(ch.isupper() for ch in paren) and ' ' in paren:
                terms.add(paren)
        value = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', value)
        value = re.sub(r'\([^)]*\)', '', value)
        value = re.sub(r'[*_`]', '', value)
        value = value.split('—')[0].split('--')[0]
        if field == 'Supervisors':
            for name in re.split(r'\s+and\s+|,\s*', value):
                name = name.strip().rstrip('.').strip()
                if ' ' in name:
                    terms.add(name)
        else:
            value = value.strip().rstrip('.').strip()
            if ' ' in value:
                terms.add(value)
    handles = _extract_personal_url_tokens(text=text)
    return terms, handles


def check_identity_term_leakage(root: Path) -> list[dict[str, Any]]:
    terms, handles = _load_identity_terms(root=root)
    if not terms and not handles:
        # Fail loud rather than pass vacuously: an empty term set means the
        # identity source (a-archive/about-me/about-me.md and its ## Identity
        # section) is missing, unreadable, or unparseable, so this highest-
        # stakes personal-info scan would otherwise report clean while
        # scanning for nothing. Surface it as an advisory (a SKILL.md Step 7.3
        # non-blocking finding) so an inactive scan cannot masquerade as clean.
        return [finding(
            check_id='identity_term_leakage',
            file='a-archive/about-me/about-me.md',
            message='identity-term source could not be loaded (about-me.md '
                    'missing/unreadable, or its ## Identity section absent or '
                    'unparseable) — the identity-leakage scan is INACTIVE; '
                    'populate ## Identity to activate it',
            fix_hint='fill a-archive/about-me/about-me.md ## Identity '
                     '(Name / Institution / Lab / Supervisors) so terms load',
        )]
    findings = []
    excluded_top = {'.git', '0-raw', 'a-archive', '2-outputs', '.obsidian',
                    'about', 'about-me'}
    text_exts = {'.md', '.py', '.sh', '.css', '.json', '.yaml', '.yml',
                 '.txt', '.toml', '.cfg', '.ini'}
    seen: set[tuple[str, str]] = set()
    for f in sorted(root.rglob('*')):
        if not f.is_file():
            continue
        rel_parts = f.relative_to(root).parts
        if rel_parts and rel_parts[0] in excluded_top:
            continue
        if _under_standalone_skill(path=f, root=root):
            continue
        if '__pycache__' in rel_parts:
            continue
        if f.suffix and f.suffix not in text_exts:
            continue
        if f.name == '.gitkeep':
            continue
        try:
            content = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IsADirectoryError, PermissionError, OSError):
            continue
        rel = str(f.relative_to(root))
        for i, line in enumerate(content.splitlines(), start=1):
            for term in sorted(terms):
                if term in line:
                    key = (rel, 'term:' + term)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(finding(
                        check_id='identity_term_leakage',
                        file=rel,
                        message=f'Identity term `{term}` appears outside about-me/.',
                        fix_hint='Move the mention to the about-me page (a-archive/about-me/about-me.md) or remove it.',
                        line=i,
                    ))
            lowered = line.lower()
            for handle in sorted(handles):
                if handle.lower() in lowered:
                    key = (rel, 'handle:' + handle)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(finding(
                        check_id='identity_term_leakage',
                        file=rel,
                        message=f'Personal URL handle `{handle}` appears outside about-me/.',
                        fix_hint='Move the mention to the about-me page (a-archive/about-me/about-me.md) or remove it.',
                        line=i,
                    ))
    return findings


# domain_literature_leakage: the generic infrastructure (CLAUDE.md + the skills,
# including their scripts) should illustrate the schema only with neutral
# placeholder papers. Any other bibkey-pattern citation is presumed to be the
# vault's own research-corpus literature, which leaks domain specifics into
# reusable infra. The structural exemptions are the *-memory.md journals
# (append-only correction logs that legitimately cite real papers from past
# work) and the agent-writable curated DATA files named in AGENT_DATA_FILES --
# data, not skill logic (the checks load them at runtime), whose content is by
# construction the vault's own (a suppression list of the vault's page paths, a
# per-raw pagination map keyed on the vault's raw stems -- each carrying a corpus
# bibkey in its filename), exactly like the memory journals; requiring
# placeholder bibkeys there is incoherent and sanctioning each entry would never
# converge. A domain-specific skill that genuinely needs to cite the research
# literature is NOT special-cased here: keeping this check free of any one
# vault's skill names is what makes it portable. Such a skill's citations are
# recorded as sanctioned exceptions in consistency-memory.md, and the agent
# leaves them alone. Scripts and their tests are scanned like everything else, so
# a test that needs a non-placeholder bibkey composes it at runtime rather than
# writing a literal token into its source. Domain *terms* and *claims* are
# deliberately left to the judgment-drift packet: a regex over them would flag
# legitimate skill descriptions and generic tooling vocabulary, so a reader has
# to make that call.
PLACEHOLDER_BIBKEYS = {
    'Vaswani2017AttentionIA',  # Transformers / Attention Is All You Need
    'Kingma2015AdamAM',        # Adam optimizer
    'Devlin2019BERTPO',        # BERT
}
BIBKEY_RE = re.compile(r'\b[A-Z][A-Za-z]+\d{4}[A-Z][A-Za-z]+\b')
# The agent-writable curated DATA files under a skill folder (CLAUDE.md -> Stay
# In Your Lane). These are data, not skill logic: the checks load them at
# runtime, and their content is by construction this vault's own -- page paths,
# per-raw pagination maps -- so a corpus bibkey in them is content, not leakage.
# Same rationale as the `-memory.md` journals. Keep in step with CLAUDE.md when a
# data file is added or renamed.
AGENT_DATA_FILES = frozenset({
    'hyphenation-lists.md',        # hyphenated_open_compound_noun (lint)
    'unlinked-mention-ignore.md',  # unlinked_page_mention suppressions (lint)
    'pagination-map.md',           # locator_page_mismatch / locator exemption (lint)
})


def check_domain_literature_leakage(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text_exts = {'.md', '.py', '.sh', '.css', '.json', '.yaml', '.yml',
                 '.txt', '.toml', '.cfg', '.ini'}
    targets: list[Path] = []
    claude = root / 'CLAUDE.md'
    if claude.exists():
        targets.append(claude)
    skills = root / '.claude' / 'skills'
    if skills.exists():
        for path in sorted(skills.rglob('*')):
            if not path.is_file() or path.suffix not in text_exts:
                continue
            # Exempt append-only memory journals (they cite real past papers).
            if path.name.endswith('-memory.md'):
                continue
            # Exempt the agent-writable curated DATA files (data, not logic):
            # their content is by construction this vault's own -- page paths,
            # per-raw pagination maps -- exactly like the memory journals above.
            if path.name in AGENT_DATA_FILES:
                continue
            # Exempt the standalone skills (wiki-orthogonal, not corpus leakage).
            if _under_standalone_skill(path=path, root=root):
                continue
            targets.append(path)
    seen: set[tuple[str, str]] = set()
    for path in targets:
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(root))
        for i, line in enumerate(content.splitlines(), start=1):
            for m in BIBKEY_RE.finditer(line):
                key_str = m.group(0)
                if key_str in PLACEHOLDER_BIBKEYS:
                    continue
                dedup = (rel, key_str)
                if dedup in seen:
                    continue
                seen.add(dedup)
                findings.append(finding(
                    check_id='domain_literature_leakage',
                    file=rel,
                    message=f'Research-corpus paper citation `{key_str}` appears in '
                    f'generic infrastructure (only placeholder papers belong here).',
                    fix_hint='Replace with a placeholder bibkey (Vaswani2017AttentionIA '
                    '/ Kingma2015AdamAM / Devlin2019BERTPO). If the citation is '
                    'legitimate domain-specific content, record it as a sanctioned '
                    'exception in consistency-memory.md. See that file for current '
                    'exceptions.',
                    line=i,
                ))
    return findings


# ai_writing_tells: AI-writing tells (mechanical patterns) in project docs.
def check_ai_writing_tells(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    target_files: list[Path] = []
    for rel in ('CLAUDE.md', 'README.md', 'MEMORY.md'):
        p = root / rel
        if p.exists():
            target_files.append(p)
    for sub in ('a-archive/style', '.claude/skills'):
        full = root / sub
        if not full.exists():
            continue
        for path in full.rglob('*.md'):
            target_files.append(path)
    # ai-writing-tells.md enumerates the banned vocabulary; the consistency,
    # lint, audit, and skill-linter skills document the tell/check patterns they
    # scan for. Both would always self-flag. Skip ai-writing-tells.md and the
    # whole of those four skill folders — not just each SKILL.md, since the
    # patterns are also documented in their references/ (e.g. audit's Step 4
    # check catalogue, which was moved out of SKILL.md into a reference). This
    # mirrors old_schema_wording self-skipping the entire consistency/ folder.
    self_referential = {root / 'a-archive/style/ai-writing-tells.md'}
    doc_skill_dirs = tuple(
        f'.claude/skills/{name}/'
        for name in ('consistency', 'lint', 'audit', 'skill-linter')
    )
    for path in target_files:
        rel_posix = str(path.relative_to(root)).replace('\\', '/')
        if path in self_referential or rel_posix.startswith(doc_skill_dirs):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(root))
        for label, severity, pattern, fix_hint in AI_TELL_PATTERNS:
            for m in pattern.finditer(text):
                line_no = text.count('\n', 0, m.start()) + 1
                findings.append(finding(
                    check_id='ai_writing_tells',
                    file=rel,
                    message=f'AI-writing tell ({label}, {severity}): '
                    f'`{m.group(0)[:80]}`',
                    fix_hint=fix_hint,
                    line=line_no,
                ))
    return findings


# file_naming_consistency: file naming consistency. The wiki uses kebab-case lowercase for
# all generated files; 2-outputs/ subfolders use {kind}-YYYY-MM-DD-HHMM(...)
# form; skill folders use kebab-case. Raw sources are user-curated and exempt.
KEBAB_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
DATED_OUTPUT_RE = re.compile(
    r'^(?P<kind>[a-z][a-z-]*)-\d{4}-\d{2}-\d{2}(?:-\d{4})?(?:-[a-z0-9-]+)?$'
)
# Output kinds whose files follow the dated naming convention. `synthesis` is
# intentionally absent: the synthesis skill writes durable pages to
# 1-wiki/syntheses/, not dated 2-outputs/ files, so there is no
# 2-outputs/synthesis/ folder to validate. output_kinds_match_disk asserts this
# set stays equal to the on-disk 2-outputs/ subfolders (minus the archive
# folders and the STANDALONE_SKILL_NAMES output folders), so a new output kind
# cannot silently fall out of naming coverage. Standalone skills are exempt:
# their output files are not bound by the dated-naming registry.
OUTPUT_KIND_DIRS = {
    'query', 'ingest', 'brief', 'compare', 'reflect',
    'lint', 'audit', 'consistency', 'skill-linter', 'skill-llm-council',
    'cleanup',
}
# Archive folders under 2-outputs/ that preserve original filenames and are not
# output kinds.
OUTPUT_ARCHIVE_DIRS = {'quarantined', 'superseded'}
# User-owned 2-outputs/ folders with no owning skill and free-form (non-dated)
# filenames — exempt from the output-kind catalogue and the CLAUDE.md directory
# tree, the same way STANDALONE_SKILL_NAMES output folders are. Empty by
# default; add a folder name here to exempt a hand-authored output folder.
OUTPUT_EXEMPT_DIRS = set()


def _check_kebab(path: Path, root: Path,
                 findings: list[dict[str, Any]], context: str) -> None:
    stem = path.stem
    if KEBAB_RE.fullmatch(stem):
        return
    findings.append(finding(
        check_id='file_naming_consistency',
        file=str(path.relative_to(root)),
        message=f'Filename `{path.name}` is not kebab-case lowercase ({context}).',
        fix_hint='Rename to ASCII letters/digits/hyphens, lowercase, no spaces or '
        'underscores or uppercase.',
    ))


def _collect_raw_stems(root: Path) -> set[str]:
    """Stems of every file under `0-raw/` (without extension). Source pages,
    their attachment folders, and outputs that reference a source by its
    stem all preserve the raw filename verbatim per CLAUDE.md, so these
    stems are exempt from kebab-case checking."""
    raw_root = root / '0-raw'
    stems: set[str] = set()
    if not raw_root.exists():
        return stems
    for f in raw_root.rglob('*'):
        if f.is_file() and not f.name.startswith('.'):
            stems.add(f.stem)
    return stems


DATED_OUTPUT_RELAXED_RE = re.compile(
    r'^(?P<kind>[a-z][a-z-]*)-\d{4}-\d{2}-\d{2}(?:-\d{4})?-(?P<suffix>.+)$'
)


def check_file_naming_consistency(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    raw_stems = _collect_raw_stems(root=root)

    # Wiki pages: source/concept/entity/synthesis must be kebab-case .md.
    # Source pages are exempted when their stem matches a raw file stem
    # (the schema requires source-page filenames to match the raw source
    # stem exactly, preserving case).
    for sub in ('sources', 'concepts', 'entities', 'syntheses'):
        folder = root / '1-wiki' / sub
        if not folder.exists():
            continue
        for path in folder.glob('*.md'):
            if sub == 'sources' and path.stem in raw_stems:
                continue
            _check_kebab(path=path, root=root, findings=findings,
                         context=f'1-wiki/{sub}')

    # Wiki attachments: each `1-wiki/attachments/{stem}/` subfolder must be
    # kebab-case OR match a raw source stem (the schema uses the
    # source-page stem for attachment folders, so paper bibkeys like
    # `Vaswani2017AttentionIA` are valid). Files inside the folder must still be
    # kebab-case.
    attachments_root = root / '1-wiki/attachments'
    if attachments_root.exists():
        for sub in attachments_root.iterdir():
            if not sub.is_dir():
                continue
            if (sub.name not in raw_stems
                    and not KEBAB_RE.fullmatch(sub.name)):
                findings.append(finding(
                    check_id='file_naming_consistency',
                    file=str(sub.relative_to(root)),
                    message=f'Attachment folder `{sub.name}` is not kebab-case '
                    'lowercase and does not match a raw source stem.',
                    fix_hint='Rename to match the source-page stem.',
                ))
            for f in sub.iterdir():
                if f.is_file() and not f.name.startswith('.'):
                    _check_kebab(path=f, root=root, findings=findings,
                                 context=f'1-wiki/attachments/{sub.name}')

    # Outputs: each `2-outputs/{kind}/` subfolder uses
    # `{kind}-YYYY-MM-DD-HHMM(-extra)?.md`. The suffix after the date is
    # normally lowercase kebab-case, but outputs that reference a source
    # by its raw stem (e.g., `ingest-2026-05-20-1430-Vaswani2017AttentionIA.md`)
    # preserve the raw case. Other subfolders (quarantined, superseded)
    # are exempt
    # — they hold archived files keeping their original names.
    outputs_root = root / '2-outputs'
    if outputs_root.exists():
        for sub in outputs_root.iterdir():
            if not sub.is_dir() or sub.name not in OUTPUT_KIND_DIRS:
                continue
            for path in sub.glob('*.md'):
                m = DATED_OUTPUT_RE.fullmatch(path.stem)
                if m and m.group('kind') == sub.name:
                    continue
                relaxed = DATED_OUTPUT_RELAXED_RE.fullmatch(path.stem)
                if (relaxed and relaxed.group('kind') == sub.name
                        and relaxed.group('suffix') in raw_stems):
                    continue
                findings.append(finding(
                    check_id='file_naming_consistency',
                    file=str(path.relative_to(root)),
                    message=f'Output filename `{path.name}` does not match '
                    f'`{sub.name}-YYYY-MM-DD-HHMM(-extra)?.md`.',
                    fix_hint=f'Rename to `{sub.name}-YYYY-MM-DD-HHMM-...md`.',
                ))

    # Skill folder names: kebab-case.
    skills_root = root / '.claude/skills'
    if skills_root.exists():
        for sub in skills_root.iterdir():
            if not sub.is_dir():
                continue
            if not KEBAB_RE.fullmatch(sub.name):
                findings.append(finding(
                    check_id='file_naming_consistency',
                    file=str(sub.relative_to(root)),
                    message=f'Skill folder `{sub.name}` is not kebab-case lowercase.',
                    fix_hint='Rename to ASCII letters/digits/hyphens.',
                ))

    return findings


# filename_references_resolve: backticked bare filenames in repo prose must resolve to a real
# file somewhere in the repo. Catches stale claims, references to deleted
# files, typos, and illustrative examples that name fake files. Filenames
# containing placeholder tokens (YYYY, {, <, *, etc.) are skipped — those
# are intentionally pattern-form. Code fences are skipped. Path-shaped
# references (with `/`) are left to referenced_paths_exist. To keep an illustrative
# example, write it with placeholder tokens (e.g., `<bibkey>.pdf`) rather
# than naming a fake file.
FILENAME_IN_BACKTICKS_RE = re.compile(
    r'`([a-z0-9][\w.-]*\.(?:md|py|sh|json|yaml|yml|css|txt|pdf))`',
    re.IGNORECASE,
)
FILENAME_PLACEHOLDER_TOKENS = ('yyyy', 'mm-dd', 'hhmm', '{', '}', '<', '>',
                                '*', '...', '$')


def _collect_repo_basenames(root: Path) -> set[str]:
    excluded_top = {'.git', '2-outputs', '.obsidian'}
    basenames: set[str] = set()
    for f in root.rglob('*'):
        if not f.is_file():
            continue
        rel_parts = f.relative_to(root).parts
        if rel_parts and rel_parts[0] in excluded_top:
            continue
        if '__pycache__' in rel_parts:
            continue
        basenames.add(f.name.lower())
    return basenames


def check_filename_references_resolve(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    target_files: list[Path] = []
    for rel in ('CLAUDE.md', 'README.md', 'MEMORY.md'):
        p = root / rel
        if p.exists():
            target_files.append(p)
    for sub in ('.claude/skills', 'a-archive', '1-wiki'):
        full = root / sub
        if not full.exists():
            continue
        for path in full.rglob('*.md'):
            target_files.append(path)
    # a-archive/reference/ holds external reference material (design catalogs,
    # smart-notes summaries) that legitimately quotes filenames from other
    # systems. Those filenames aren't expected to exist in this repo; scanning
    # them produces noise. Project documents (a-archive/style, a-archive/about-me)
    # stay in scope. Standalone skills (STANDALONE_SKILL_NAMES) are also excluded
    # — they may ship placeholder/example filenames that intentionally don't
    # resolve, the same way the leakage and catalogue checks skip their folders.
    target_files = [p for p in target_files
                    if 'a-archive/reference' not in str(p.relative_to(root))
                    and not _under_standalone_skill(path=p, root=root)]
    repo_basenames = _collect_repo_basenames(root=root)
    seen: set[tuple[str, str, int]] = set()
    for path in target_files:
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(root))
        in_fence = False
        for i, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith('```'):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in FILENAME_IN_BACKTICKS_RE.finditer(line):
                raw = m.group(1)
                lower = raw.lower()
                if any(t in lower for t in FILENAME_PLACEHOLDER_TOKENS):
                    continue
                if lower in repo_basenames:
                    continue
                key = (rel, lower, i)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(finding(
                    check_id='filename_references_resolve',
                    file=rel,
                    message=f'Backticked filename `{raw}` is not present anywhere '
                    'in the repo.',
                    fix_hint='Update the reference, remove the line, or rewrite '
                    'as a placeholder pattern (e.g., `<bibkey>.pdf`).',
                    line=i,
                ))
    return findings


def check_memory_file_graduation_prompt(root: Path) -> list[dict[str, Any]]:
    """Memory file graduation prompt.

    Counts H2-level entries in `MEMORY.md`, `.claude/skills/multi-skill/multi-skill-memory.md`,
    and each `.claude/skills/<skill>/<skill>-memory.md`. Files past their soft
    cap (10 for the append-only journals, 15 for the `MEMORY.md` consolidation
    tier) are marked as graduation candidates for the per-entry memory audit to
    read. `MEMORY.md`'s `## Index` table of contents is not counted. Memory
    files are read at every operation (`MEMORY.md` every session), so long ones
    become a token tax. This counter only flags by count; it does not read
    entry content.
    """
    findings: list[dict[str, Any]] = []

    # Each entry: (path, cap, graduation-target text). The append-only journals
    # drain into MEMORY.md or CLAUDE.md; MEMORY.md is itself the consolidation
    # tier, so it only graduates outward to CLAUDE.md and sits at a higher cap.
    journal_target = 'MEMORY.md (behavioural) or CLAUDE.md (schema)'
    memory_md_target = "CLAUDE.md (schema or Behavioural defaults)"

    memory_files: list[tuple[Path, int, str]] = []
    memory_md = root / 'MEMORY.md'
    if memory_md.exists():
        memory_files.append((memory_md, MEMORY_MD_ENTRY_CAP, memory_md_target))
    multi = root / '.claude/skills/multi-skill/multi-skill-memory.md'
    if multi.exists():
        memory_files.append((multi, MEMORY_FILE_ENTRY_CAP, journal_target))
    skills_dir = root / '.claude/skills'
    if skills_dir.exists():
        for sub in sorted(skills_dir.iterdir()):
            if not sub.is_dir():
                continue
            mem = sub / f'{sub.name}-memory.md'
            if mem.exists():
                memory_files.append((mem, MEMORY_FILE_ENTRY_CAP, journal_target))

    for path, cap, target in memory_files:
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        # Count H2 entries; MEMORY.md's "## Index" is a table of contents, not an
        # entry, so it is not counted toward the cap.
        entries = sum(
            1 for line in lines
            if line.startswith('## ') and line.strip() != '## Index'
        )
        if entries > cap:
            rel = str(path.relative_to(root))
            findings.append(finding(
                check_id='memory_file_graduation_prompt',
                file=rel,
                message=f'Memory file has {entries} entries (soft cap: {cap}) — '
                'candidates for graduation. Long memory files become a '
                'per-operation token tax for every skill (or session) that '
                'reads them.',
                fix_hint='Run the `cleanup` skill (its memory graduation audit) for a per-entry check '
                f'of what has already graduated into {target}, then graduate '
                'stable rules and remove the absorbed originals. This counter '
                'only flags the file; it does not read entry content.',
            ))
    return findings


TREE_LINE_RE = re.compile(r'^((?:│   |    )*)([├└]── )(.+)$')


def parse_directory_tree(tree_text: str) -> set[str]:
    """Parse an ASCII directory tree into a set of relative paths.

    Handles the standard tree-rendering convention (├──, └──, │ prefixes)
    used in the CLAUDE.md `Directory Structure` block. Each emitted path
    is repo-root-relative, with no trailing slash.
    """
    paths: set[str] = set()
    stack: list[str] = []
    for raw_line in tree_text.splitlines():
        m = TREE_LINE_RE.match(raw_line)
        if not m:
            continue
        prefix, _, entry = m.groups()
        depth = len(prefix) // 4
        # Strip inline `# comment` and any trailing slash.
        name = re.sub(r'\s*#.*$', '', entry).strip().rstrip('/')
        if not name:
            continue
        stack = stack[:depth]
        stack.append(name)
        paths.add('/'.join(stack))
    return paths


def expected_tree_paths(root: Path) -> set[str]:
    """Collect repo paths that should appear in CLAUDE.md's directory tree.

    Includes top-level docs (CLAUDE.md, MEMORY.md, README.md), top-level
    non-hidden directories, immediate children of 0-raw/, 2-outputs/,
    a-archive/, and 1-wiki/'s hot/index/log files plus its immediate
    child directories. .claude/skills/ is included as a single tree leaf
    because its deeper structure is documented inside each skill.
    """
    paths: set[str] = set()

    for entry in root.iterdir():
        name = entry.name
        if name in {'.git', '.obsidian'}:
            continue
        if entry.is_file():
            if name in {'CLAUDE.md', 'MEMORY.md', 'README.md'}:
                paths.add(name)
            continue
        if entry.is_dir():
            if name.startswith('.'):
                if name == '.claude' and (entry / 'skills').is_dir():
                    paths.add('.claude/skills')
                continue
            paths.add(name)

    for parent in ('0-raw', '2-outputs', 'a-archive'):
        parent_dir = root / parent
        if not parent_dir.is_dir():
            continue
        for child in parent_dir.iterdir():
            if not child.is_dir() or child.name.startswith('.'):
                continue
            # Standalone skills' 2-outputs/ folders are kept out of the tree;
            # so are any user-owned free-form folders in OUTPUT_EXEMPT_DIRS.
            if parent == '2-outputs' and (child.name in STANDALONE_SKILL_NAMES
                                          or child.name in OUTPUT_EXEMPT_DIRS):
                continue
            paths.add(f'{parent}/{child.name}')

    wiki = root / '1-wiki'
    if wiki.is_dir():
        for child in wiki.iterdir():
            cname = child.name
            if child.is_file() and cname in {'hot.md', 'index.md', 'log.md'}:
                paths.add(f'1-wiki/{cname}')
            elif child.is_dir() and not cname.startswith('.'):
                paths.add(f'1-wiki/{cname}')

    return paths


# dir_tree_drift: CLAUDE.md directory tree drift.
def check_dir_tree_drift(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    claude = root / 'CLAUDE.md'
    if not claude.exists():
        return findings

    text = claude.read_text(encoding='utf-8')

    # Find the first text-fenced block that looks like the repo tree.
    tree_text: str | None = None
    for match in re.finditer(r'```text\n(.*?)```', text, re.DOTALL):
        block = match.group(1)
        if 'llm-wiki/' in block:
            tree_text = block
            break

    if tree_text is None:
        findings.append(finding(
            check_id='dir_tree_drift',
            file='CLAUDE.md',
            message='Directory tree block (```text ... ``` rooted at '
            '`llm-wiki/`) not found.',
            fix_hint='Add a `text`-fenced ASCII tree under the '
            '`Directory Structure` heading.',
        ))
        return findings

    tree_paths = parse_directory_tree(tree_text=tree_text)
    expected_paths = expected_tree_paths(root=root)

    # Tree lists a path that does not exist on disk.
    for tree_path in sorted(tree_paths):
        if not (root / tree_path).exists():
            findings.append(finding(
                check_id='dir_tree_drift',
                file='CLAUDE.md',
                message=f'Directory tree lists `{tree_path}` but it does '
                'not exist on disk.',
                fix_hint=f'Remove `{tree_path}` from the tree, or create '
                'the directory if it was meant to exist.',
            ))

    # On-disk path that the schema tree should include but doesn't.
    for expected in sorted(expected_paths - tree_paths):
        findings.append(finding(
            check_id='dir_tree_drift',
            file='CLAUDE.md',
            message=f'`{expected}` exists on disk but is missing from '
            "the CLAUDE.md directory tree.",
            fix_hint=f'Add `{expected}` to the tree under its parent in '
            '`CLAUDE.md` → Directory Structure.',
        ))

    return findings


UNBACKTICKED_PATH_RE = re.compile(
    r'(?<![\w/.\-])'
    r'((?:0-raw|1-wiki|2-outputs|a-archive|\.claude)/[\w./-]+)'
)


# unbackticked_paths_resolve: unbackticked schema-prefix paths in CLAUDE.md resolve.
def check_unbackticked_paths_resolve(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    claude = root / 'CLAUDE.md'
    if not claude.exists():
        return findings

    text = claude.read_text(encoding='utf-8')
    seen: set[tuple[str, int]] = set()
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Strip backticked inline spans (those are filename_references_resolve's territory).
        stripped = re.sub(r'`[^`]*`', '', line)
        for m in UNBACKTICKED_PATH_RE.finditer(stripped):
            token = m.group(1).rstrip('/.,;:)')
            if not token:
                continue
            # Skip placeholder tokens.
            if any(ch in token for ch in '<{*'):
                continue
            key = (token, i)
            if key in seen:
                continue
            seen.add(key)
            if not (root / token).exists():
                findings.append(finding(
                    check_id='unbackticked_paths_resolve',
                    file='CLAUDE.md',
                    message=f'Unbackticked path `{token}` referenced in '
                    'prose does not resolve.',
                    fix_hint='Backtick the reference (filename_references_resolve '
                    'will then validate it), or fix the path.',
                    line=i,
                ))
    return findings


OPERATIONS_HEADING_RE = re.compile(r'^## Operations\b', re.MULTILINE)
NEXT_H2_RE = re.compile(r'^## ', re.MULTILINE)
SKILL_BULLET_RE = re.compile(r'^- `([a-z0-9][a-z0-9-]*)`\s+-')


# operations_list_matches_skills: CLAUDE.md Operations list matches skill folders on disk.
def check_operations_list_matches_skills(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    claude = root / 'CLAUDE.md'
    skills_dir = root / '.claude/skills'
    if not claude.exists() or not skills_dir.exists():
        return findings

    text = claude.read_text(encoding='utf-8')
    start_match = OPERATIONS_HEADING_RE.search(text)
    if not start_match:
        findings.append(finding(
            check_id='operations_list_matches_skills',
            file='CLAUDE.md',
            message='`## Operations` section not found in CLAUDE.md.',
            fix_hint='Add a top-level `## Operations` section listing the '
            'project skills.',
        ))
        return findings

    section_start = start_match.start()
    next_match = NEXT_H2_RE.search(text, pos=start_match.end())
    section_end = next_match.start() if next_match else len(text)
    section = text[section_start:section_end]

    listed: set[str] = set()
    for line in section.splitlines():
        bm = SKILL_BULLET_RE.match(line)
        if bm:
            listed.add(bm.group(1))

    on_disk = {p.name for p in skills_dir.iterdir()
               if p.is_dir() and not p.name.startswith('.')
               and (p / 'SKILL.md').exists()}

    # Standalone skills are deliberately out of the Operations catalogue, so
    # neither requiring nor flagging them either way: drop them from both sides.
    listed -= STANDALONE_SKILL_NAMES
    on_disk -= STANDALONE_SKILL_NAMES

    for stale in sorted(listed - on_disk):
        findings.append(finding(
            check_id='operations_list_matches_skills',
            file='CLAUDE.md',
            message=f'Operations section lists `{stale}` but '
            f'`.claude/skills/{stale}/` does not exist.',
            fix_hint=f'Remove `{stale}` from `## Operations`, or create '
            'the skill folder.',
        ))

    for missing in sorted(on_disk - listed):
        findings.append(finding(
            check_id='operations_list_matches_skills',
            file='CLAUDE.md',
            message=f'Skill `.claude/skills/{missing}/` exists on disk '
            'but is missing from `## Operations` in CLAUDE.md.',
            fix_hint=f'Add `- \\`{missing}\\` - <one-line description>` '
            'under the appropriate sub-list in `## Operations`.',
        ))
    return findings


# retired_skill_references: routing to a skill that was merged or renamed away.
# `ingest-deep` and `reingest` were folded into `ingest` (deep mode and
# existing-source mode). The Operations list and folders were updated, but
# routing references can survive in skill bodies. `ingest-deep` has no
# legitimate prose form, so any occurrence is drift; `reingest` survives as
# mode vocabulary unbackticked ("a reingest appends"), so only its routing form
# — backticked or slash-prefixed — is drift. Add a name here when a skill
# retires or merges; the keys are the dead names, the values control how
# strictly each is matched ('any' = literal anywhere, 'routing' = backtick or
# slash only).
RETIRED_SKILL_NAMES = {
    'ingest-deep': 'any',
    'reingest': 'routing',
}
# 'operation skills `a`, `b`' / 'meta skills `c`' enumeration line.
SKILLS_ENUMERATION_RE = re.compile(r'(?:operation|meta)\s+skills?\s+`')
BACKTICKED_SKILL_TOKEN_RE = re.compile(r'`([a-z][a-z0-9-]*)`')


def _retired_routing_exempt(rel: str, line: str) -> bool:
    """Lines where naming a retired skill is legitimate, not drift."""
    slashed = '/' + rel.replace('\\', '/')
    # The ingest skill owns the mode names (log-verb template); the consistency
    # skill documents this very check.
    if '/skills/ingest/' in slashed or '/skills/consistency/' in slashed:
        return True
    if rel.endswith('-memory.md'):
        return True
    return False


def check_retired_skill_references(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    skills_dir = root / '.claude/skills'
    current_skills = (
        {p.name for p in skills_dir.iterdir()
         if p.is_dir() and not p.name.startswith('.')}
        if skills_dir.exists() else set()
    )

    scan: list[Path] = []
    for top in ('CLAUDE.md', 'README.md'):
        p = root / top
        if p.exists():
            scan.append(p)
    if skills_dir.exists():
        scan.extend(sorted(skills_dir.rglob('*.md')))
        scan.extend(sorted(skills_dir.rglob('*.py')))
        scan.extend(sorted(skills_dir.rglob('*.sh')))

    for f in scan:
        rel = str(f.relative_to(root))
        # The consistency skill documents these retired names and enumeration
        # patterns by necessity; self-skip its folder so the check never flags
        # its own definition (mirrors ai_writing_tells self-skipping).
        if '/skills/consistency/' in '/' + rel.replace('\\', '/'):
            continue
        try:
            lines = f.read_text(encoding='utf-8').splitlines()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for i, line in enumerate(lines, start=1):
            # Retired-skill routing guard.
            for name, mode in RETIRED_SKILL_NAMES.items():
                if name not in line:
                    continue
                if _retired_routing_exempt(rel=rel, line=line):
                    continue
                if mode == 'routing' and (
                    f'`{name}`' not in line and f'/{name}' not in line
                ):
                    continue
                findings.append(finding(
                    check_id='retired_skill_references',
                    file=rel,
                    line=i,
                    message=f'References merged-away skill `{name}` '
                    '(now a mode of `ingest`).',
                    fix_hint=f'`{name}` is no longer a separate skill — '
                    "rephrase to `ingest` (deep mode for `ingest-deep`, "
                    'existing-source mode for `reingest`).',
                ))
            # Required-skills enumeration must resolve to current folders.
            if current_skills and SKILLS_ENUMERATION_RE.search(line):
                for tok in BACKTICKED_SKILL_TOKEN_RE.findall(line):
                    if tok in current_skills or tok in RETIRED_SKILL_NAMES:
                        continue  # retired names reported by the guard above
                    findings.append(finding(
                        check_id='retired_skill_references',
                        file=rel,
                        line=i,
                        message=f'Required-skills enumeration lists `{tok}`, '
                        'which is not a current skill folder.',
                        fix_hint=f'Add `.claude/skills/{tok}/` or remove '
                        f'`{tok}` from the enumeration.',
                    ))
    return findings


# section_lists_match_schema: EXPECTED_SECTIONS is a hardcoded copy of the
# callout lists CLAUDE.md documents under "### Required Callout Sections".
# body_section_order validates wiki pages against that copy, not CLAUDE.md, so
# without this check a CLAUDE.md section-list edit (the exact change consistency
# runs for) silently leaves the script enforcing the old schema.
CLAUDE_SECTION_LABELS = {
    'source pages': 'source',
    'concept/entity pages': 'concept',
    'synthesis pages': 'synthesis',
}
# Capture the raw backticked token after the list number, not a pre-filtered
# slug shape: a malformed slug (uppercase/digit/underscore) must still appear
# in the parsed list so the mismatch message names the real offender instead of
# silently dropping the line.
SECTION_LIST_ITEM_RE = re.compile(r'^\s*\d+\.\s+`([^`]+)`')
# A label/heading line: ends in ':' or is a Markdown heading or bold run. These
# reset the current page-type so a list under an unrecognized heading is not
# misattributed to the last recognized one.
SECTION_PAGE_LABEL_RE = re.compile(r'^[a-z][a-z/ ]* pages?$')


def _norm_section_label(line: str) -> str:
    s = line.strip().strip('#').strip().strip('*').strip()
    return s.rstrip(':').strip().lower()


def _parse_claude_section_lists(
    text: str,
) -> tuple[dict[str, list[str]], list[str]]:
    """Parse the slug lists under CLAUDE.md '### Required Callout Sections'.

    Returns (lists-by-page-type, unrecognized-page-type-labels). `current` is
    reset on any label/heading line that is not a recognized page type, so a
    stray numbered list under a new or unrecognized heading is not appended to
    whichever recognized list came last.
    """
    m = re.search(r'^### Required Callout Sections\s*$', text, re.MULTILINE)
    if not m:
        return {}, []
    body_start = m.end()
    nxt = re.search(r'^## ', text[body_start:], re.MULTILINE)
    body = text[body_start:body_start + nxt.start()] if nxt else text[body_start:]
    result: dict[str, list[str]] = {}
    unrecognized: list[str] = []
    current: str | None = None
    for line in body.splitlines():
        stripped = line.strip()
        im = SECTION_LIST_ITEM_RE.match(line)
        if im:
            if current is not None:
                result[current].append(im.group(1))
            continue
        if not stripped:
            continue  # blank lines sit between a label and its list
        is_heading_shaped = (
            stripped.endswith(':')
            or stripped.startswith('#')
            or stripped.startswith('**')
        )
        if not is_heading_shaped:
            continue  # ordinary prose does not change the current page type
        label = _norm_section_label(line=line)
        if label in CLAUDE_SECTION_LABELS:
            current = CLAUDE_SECTION_LABELS[label]
            result.setdefault(current, [])
        else:
            current = None  # unrecognized heading — do not misattribute
            if SECTION_PAGE_LABEL_RE.match(label):
                unrecognized.append(label)
    return result, unrecognized


def check_section_lists_match_schema(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    claude = root / 'CLAUDE.md'
    if not claude.exists():
        return findings
    parsed, unrecognized = _parse_claude_section_lists(
        text=claude.read_text(encoding='utf-8'))
    if not parsed:
        findings.append(finding(
            check_id='section_lists_match_schema',
            file='CLAUDE.md',
            message="'### Required Callout Sections' lists not found or unparseable.",
            fix_hint='Keep the numbered "`slug` - Name" lists under that heading so '
            'the script can verify EXPECTED_SECTIONS against the schema.',
        ))
        return findings
    # A documented page type the script does not validate is a latent gap: a new
    # page type is exactly the section-template edit this check exists to catch.
    for label in unrecognized:
        findings.append(finding(
            check_id='section_lists_match_schema',
            file='CLAUDE.md',
            message=f"'### Required Callout Sections' documents a `{label}` list "
            'the script does not validate.',
            fix_hint='Add the page type to CLAUDE_SECTION_LABELS, EXPECTED_SECTIONS, '
            'and the comparison loop in check_consistency.py, or remove the list.',
        ))
    # CLAUDE.md documents one shared "concept/entity" list; EXPECTED_SECTIONS
    # stores 'concept' and 'entity' identically, so compare against 'concept'.
    for kind in ('source', 'concept', 'synthesis'):
        documented = parsed.get(kind)
        expected = EXPECTED_SECTIONS[kind]
        if documented is None:
            findings.append(finding(
                check_id='section_lists_match_schema',
                file='CLAUDE.md',
                message=f'No callout list for `{kind}` pages found under '
                "'### Required Callout Sections'.",
                fix_hint=f'Document the {kind}-page sections, or align '
                'EXPECTED_SECTIONS in check_consistency.py.',
            ))
            continue
        if documented != expected:
            findings.append(finding(
                check_id='section_lists_match_schema',
                file='CLAUDE.md',
                message=f'`{kind}` callout list in CLAUDE.md ({documented}) does '
                f'not match EXPECTED_SECTIONS in the script ({expected}).',
                fix_hint='Reconcile CLAUDE.md and EXPECTED_SECTIONS so '
                'body_section_order enforces the current schema.',
            ))
    return findings


# output_kinds_match_disk: OUTPUT_KIND_DIRS (the dated-naming kinds) must equal
# the on-disk 2-outputs/ subfolders minus the archive folders, so a newly added
# output kind cannot silently escape file_naming_consistency.
def check_output_kinds_match_disk(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    outputs = root / '2-outputs'
    if not outputs.exists():
        return findings
    on_disk = {p.name for p in outputs.iterdir()
               if p.is_dir() and not p.name.startswith('.')
               and p.name not in OUTPUT_ARCHIVE_DIRS
               and p.name not in OUTPUT_EXEMPT_DIRS
               and p.name not in STANDALONE_SKILL_NAMES}
    script_rel = '.claude/skills/consistency/scripts/check_consistency.py'
    for missing in sorted(on_disk - OUTPUT_KIND_DIRS):
        findings.append(finding(
            check_id='output_kinds_match_disk',
            file=script_rel,
            message=f'`2-outputs/{missing}/` exists but `{missing}` is not in '
            'OUTPUT_KIND_DIRS, so its files escape the naming check.',
            fix_hint=f"Add '{missing}' to OUTPUT_KIND_DIRS (and the SKILL.md "
            'naming list), or move the folder under quarantined/superseded.',
        ))
    # Stale direction: only a real drift when the kind's skill still exists but
    # its output folder vanished. Output folders are created lazily by their
    # skill, so on a fresh vault a never-run kind has no folder yet — flagging
    # that would be noise, not drift. Every current kind is named after its
    # owning skill (query/ingest/…), so skill presence is the proxy.
    skills_dir = root / '.claude/skills'
    for stale in sorted(OUTPUT_KIND_DIRS - on_disk):
        if not (skills_dir / stale).is_dir():
            continue
        findings.append(finding(
            check_id='output_kinds_match_disk',
            file=script_rel,
            message=f'OUTPUT_KIND_DIRS lists `{stale}` and the `{stale}` skill '
            f'exists, but `2-outputs/{stale}/` does not exist on disk.',
            fix_hint=f"Create `2-outputs/{stale}/` (with a .gitkeep), or drop "
            f"'{stale}' from OUTPUT_KIND_DIRS.",
        ))
    return findings


# catalogue_matches_manifest: references/checks.md restates the per-check
# catalogue (packet groupings and per-packet counts). Moving the catalogue out
# of SKILL.md created a doc copy nothing else guards, so this check parses it and
# asserts equality with CHECK_MANIFEST / PACKET_CHECKS — the same drift class
# section_lists_match_schema guards for CLAUDE.md's section lists.
CATALOGUE_PACKET_HEADER_RE = re.compile(r'^## Packet:\s*([a-z][a-z-]*)\s*$')
CATALOGUE_CHECK_BULLET_RE = re.compile(r'^- `([a-z_]+)`')
CATALOGUE_TOTAL_RE = re.compile(r'(\d+)\s+checks\s+across')
CATALOGUE_PACKET_COUNT_RE = re.compile(r'([a-z][a-z-]+)\s+\((\d+)\)')


def check_catalogue_matches_manifest(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    rel = '.claude/skills/consistency/references/checks.md'
    cat = root / rel
    if not cat.exists():
        return [finding(
            check_id='catalogue_matches_manifest',
            file=rel,
            message='Per-check catalogue reference is missing.',
            fix_hint='Restore references/checks.md or update the SKILL.md pointer.',
        )]
    text = cat.read_text(encoding='utf-8')
    actual_packets = {p: set(ids) for p, ids in PACKET_CHECKS.items()}

    # Parse packet -> set(check_ids) from '## Packet: X' sections and '- `id`'
    # bullets beneath each.
    doc_packets: dict[str, set[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        hm = CATALOGUE_PACKET_HEADER_RE.match(line)
        if hm:
            current = hm.group(1)
            doc_packets.setdefault(current, set())
            continue
        bm = CATALOGUE_CHECK_BULLET_RE.match(line)
        if bm and current is not None:
            doc_packets[current].add(bm.group(1))

    for packet in sorted(set(doc_packets) | set(actual_packets)):
        doc = doc_packets.get(packet, set())
        act = actual_packets.get(packet, set())
        if doc != act:
            findings.append(finding(
                check_id='catalogue_matches_manifest',
                file=rel,
                message=f'Catalogue packet `{packet}` lists {sorted(doc)} but the '
                f'manifest has {sorted(act)}.',
                fix_hint='Update references/checks.md to match `--list-checks`.',
            ))

    # Stated counts: total ('N checks across') and per-packet ('name (n)').
    tm = CATALOGUE_TOTAL_RE.search(text)
    if tm and int(tm.group(1)) != len(CHECK_MANIFEST):
        findings.append(finding(
            check_id='catalogue_matches_manifest',
            file=rel,
            message=f'Catalogue states {tm.group(1)} checks but the manifest has '
            f'{len(CHECK_MANIFEST)}.',
            fix_hint='Update the total count in references/checks.md.',
        ))
    for m in CATALOGUE_PACKET_COUNT_RE.finditer(text):
        name, n = m.group(1), int(m.group(2))
        if name in actual_packets and n != len(actual_packets[name]):
            findings.append(finding(
                check_id='catalogue_matches_manifest',
                file=rel,
                message=f'Catalogue states packet `{name}` has {n} checks but the '
                f'manifest has {len(actual_packets[name])}.',
                fix_hint='Update the per-packet count in references/checks.md.',
            ))
    return findings


def check_shared_reference_integrity(root: Path) -> list[dict[str, Any]]:
    """Enforce the `multi-skill/references/` contract (CLAUDE.md -> Stay In Your
    Lane): a file there must be genuinely shared and exist as a single copy.

    For each `.claude/skills/multi-skill/references/*.md`:
      (a) it is cited by >= 2 distinct skills — that location is for cross-skill
          material; a reference used by one skill belongs in that skill's own
          `references/`;
      (b) no skill folder holds a same-named `references/<file>` (a duplicate copy
          that would drift from the shared canonical one).

    Motivating case: `verification.md`, run by `ingest` (Step 8) and `query` (its
    page-authoring path). Findings are root-level proposals — the files are
    soft-read-only, so the user (not the script) acts.
    """
    findings: list[dict[str, Any]] = []
    skills_dir = root / '.claude/skills'
    shared_dir = skills_dir / 'multi-skill' / 'references'
    if not shared_dir.exists():
        return findings
    shared_files = sorted(shared_dir.glob('*.md'))
    if not shared_files:
        return findings

    skill_dirs = [p for p in sorted(skills_dir.iterdir())
                  if p.is_dir() and p.name != 'multi-skill'
                  and not p.name.startswith('.')]

    # Per-skill concatenated text (md + py) for citation scanning, and a map of
    # basename -> skill folders that hold their own references/<basename>.
    skill_text: dict[str, str] = {}
    own_ref_copies: dict[str, list[str]] = {}
    for sd in skill_dirs:
        chunks: list[str] = []
        for f in sd.rglob('*'):
            if f.is_file() and f.suffix in {'.md', '.py'}:
                try:
                    chunks.append(f.read_text(encoding='utf-8'))
                except (UnicodeDecodeError, OSError):
                    pass
        skill_text[sd.name] = '\n'.join(chunks)
        refs = sd / 'references'
        if refs.exists():
            for rp in refs.glob('*.md'):
                own_ref_copies.setdefault(rp.name, []).append(sd.name)

    rel = '.claude/skills/multi-skill/references'
    for shared in shared_files:
        name = shared.name
        for owner in own_ref_copies.get(name, []):
            findings.append(finding(
                check_id='shared_reference_integrity',
                file=f'{rel}/{name}',
                message=(f'Shared reference `{name}` is also copied at '
                         f'`.claude/skills/{owner}/references/{name}`; the shared '
                         f'spec must exist as a single canonical copy.'),
                fix_hint=(f'Delete `{owner}/references/{name}` and point that '
                          f'skill at `{rel}/{name}`.'),
            ))
        citing = sorted(n for n, txt in skill_text.items() if name in txt)
        if len(citing) < 2:
            who = ', '.join(citing) if citing else 'no skills'
            findings.append(finding(
                check_id='shared_reference_integrity',
                file=f'{rel}/{name}',
                message=(f'Shared reference `{name}` is cited by {len(citing)} '
                         f'skill(s) ({who}); `multi-skill/references/` is for '
                         f'references shared by two or more skills.'),
                fix_hint=(f'Cite `{name}` from a second skill, or move it into '
                          f'the one skill that uses it (its own `references/`).'),
            ))
    return findings


CHECK_FUNCTIONS = {
    'retired_feature_mentions': check_retired_feature_mentions,
    'working_skill_count_prose': check_working_skill_count_prose,
    'old_schema_wording': check_old_schema_wording,
    'placeholder_consistency': check_placeholder_consistency,
    'body_section_order': check_body_section_order,
    'source_venue_year_split': check_source_venue_year_split,
    'index_vs_files_drift': check_index_vs_files_drift,
    'attachments_folder_coverage': check_attachments_folder_coverage,
    'callout_css_coverage': check_callout_css_coverage,
    'gitkeep_coverage': check_gitkeep_coverage,
    'referenced_paths_exist': check_referenced_paths_exist,
    'orphan_skill_scripts': check_orphan_skill_scripts,
    'personal_info_leakage': check_personal_info_leakage,
    'identity_term_leakage': check_identity_term_leakage,
    'domain_literature_leakage': check_domain_literature_leakage,
    'ai_writing_tells': check_ai_writing_tells,
    'file_naming_consistency': check_file_naming_consistency,
    'filename_references_resolve': check_filename_references_resolve,
    'memory_file_graduation_prompt': check_memory_file_graduation_prompt,
    'dir_tree_drift': check_dir_tree_drift,
    'unbackticked_paths_resolve': check_unbackticked_paths_resolve,
    'operations_list_matches_skills': check_operations_list_matches_skills,
    'retired_skill_references': check_retired_skill_references,
    'section_lists_match_schema': check_section_lists_match_schema,
    'output_kinds_match_disk': check_output_kinds_match_disk,
    'catalogue_matches_manifest': check_catalogue_matches_manifest,
    'shared_reference_integrity': check_shared_reference_integrity,
}


def parse_check_ids(raw: str) -> list[str]:
    # Dedupe while preserving order so a copy-paste-repeated id does not run a
    # check twice and double its findings.
    return list(dict.fromkeys(
        part.strip() for part in raw.split(',') if part.strip()))


def _assert_manifest_consistency() -> list[str]:
    """Check the script's own wiring: CHECK_FUNCTIONS, CHECK_MANIFEST, and
    PACKET_CHECKS must describe the same set of checks, and the entity/concept
    shared-list assumption that lets section_lists_match_schema skip 'entity'
    must hold. Returns a list of problems (empty when wiring is sound)."""
    problems: list[str] = []
    fn_ids = set(CHECK_FUNCTIONS)
    manifest_ids = [x['check_id'] for x in CHECK_MANIFEST]
    manifest_set = set(manifest_ids)
    if len(manifest_ids) != len(manifest_set):
        dupes = sorted({c for c in manifest_ids if manifest_ids.count(c) > 1})
        problems.append(f'duplicate check_id(s) in CHECK_MANIFEST: {dupes}')
    if fn_ids != manifest_set:
        problems.append(
            f'CHECK_FUNCTIONS vs CHECK_MANIFEST mismatch: '
            f'only in functions={sorted(fn_ids - manifest_set)}, '
            f'only in manifest={sorted(manifest_set - fn_ids)}')
    packet_union = set().union(*PACKET_CHECKS.values()) if PACKET_CHECKS else set()
    if fn_ids != packet_union:
        problems.append(
            f'CHECK_FUNCTIONS vs PACKET_CHECKS mismatch: '
            f'only in functions={sorted(fn_ids - packet_union)}, '
            f'only in packets={sorted(packet_union - fn_ids)}')
    if EXPECTED_SECTIONS.get('entity') != EXPECTED_SECTIONS.get('concept'):
        problems.append(
            "EXPECTED_SECTIONS['entity'] != EXPECTED_SECTIONS['concept']; "
            'section_lists_match_schema skips entity on the assumption they '
            'are identical')
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run schema consistency checks.'
    )
    parser.add_argument('project_root', nargs='?')
    parser.add_argument(
        '--checks',
        help='Comma-separated check IDs to run, e.g. A,B,C.',
    )
    parser.add_argument(
        '--packet',
        choices=sorted(PACKET_CHECKS),
        help='Named check packet to run.',
    )
    parser.add_argument(
        '--list-checks',
        action='store_true',
        help='Print check metadata and exit.',
    )
    args = parser.parse_args()

    # Guard the script's own wiring before doing any work: a function added
    # without its manifest/packet entry (or vice versa) would otherwise drift
    # silently. Emit the problem on stdout (as an (internal) finding the agent
    # can read) and stderr, and exit 2 (did not complete).
    wiring = _assert_manifest_consistency()
    if wiring:
        print(json.dumps([finding(
            check_id='manifest_parity',
            file='(internal)',
            message='WIRING ERROR: ' + '; '.join(wiring),
            fix_hint='Reconcile CHECK_FUNCTIONS, CHECK_MANIFEST, and '
            'PACKET_CHECKS in check_consistency.py.',
        )], indent=2))
        sys.stderr.write('manifest wiring error: ' + '; '.join(wiring) + '\n')
        return 2

    if args.list_checks:
        print(json.dumps(CHECK_MANIFEST, indent=2))
        return 0

    if not args.project_root:
        parser.error('project-root is required unless --list-checks is used')
    if args.checks and args.packet:
        parser.error('use either --checks or --packet, not both')

    root = Path(args.project_root).resolve()
    if not root.exists():
        sys.stderr.write(f'path not found: {root}\n')
        return 2

    selected = list(CHECK_FUNCTIONS)
    if args.packet:
        selected = PACKET_CHECKS[args.packet]
    elif args.checks:
        selected = parse_check_ids(raw=args.checks)
    unknown = sorted(set(selected) - set(CHECK_FUNCTIONS))
    if unknown:
        sys.stderr.write(f'unknown check id(s): {", ".join(unknown)}\n')
        return 2

    all_findings: list[dict[str, Any]] = []
    crashed = False
    for check_id in selected:
        try:
            all_findings.extend(CHECK_FUNCTIONS[check_id](root))
        except Exception as exc:  # noqa: BLE001 — one check must not abort the battery
            crashed = True
            all_findings.append(finding(
                check_id=check_id,
                file='(internal)',
                message=f'CHECK CRASHED ({type(exc).__name__}): {exc}. '
                'Treat as blocked — the battery did not run to completion.',
                fix_hint='Fix the check or its input; rerun before trusting a '
                'clean result.',
            ))

    # Sort findings once so output order is reproducible across platforms and
    # filesystems (most checks iterate glob/iterdir, which is not order-stable).
    # A stable order is what makes a golden-output regression test possible.
    all_findings.sort(key=lambda f: (
        f.get('check_id') or '', f.get('file') or '',
        f.get('line') or 0, f.get('message') or ''))
    print(json.dumps(all_findings, indent=2))
    # Exit codes:
    #   0  clean (no findings)
    #   1  ran to completion, found drift
    #   2  did NOT complete — a check crashed, the manifest wiring is broken, or
    #      the invocation was malformed (bad path / unknown check / bad --packet)
    # Distinguish the exit-2 cases by stdout: a crash or wiring error prints a
    # JSON array carrying an `(internal)` finding; an invocation error prints
    # nothing to stdout and a message to stderr. JSON is always printed first.
    if crashed:
        return 2
    return 0 if not all_findings else 1


if __name__ == '__main__':
    sys.exit(main())
