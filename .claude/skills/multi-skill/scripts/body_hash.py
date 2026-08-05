#!/usr/bin/env python3
"""Print the SHA-256 of a wiki page's body — the content after the YAML frontmatter.

`audit` runs this to stamp `verified_hash:` when it sets a page `verified`; `lint`
runs it to detect a `verified` page whose checked content changed since (hash
mismatch -> the page is reset to `draft`). Both skills must hash identically, so
both call this one script. The body excludes frontmatter, so mechanical metadata
edits (`updated:`, `status:`, `verified_hash:` itself) do not change the hash.

The hash also excludes any callout bullet line carrying the `*[unverified]*`
claim marker in its canonical position immediately after `> - `
(CLAUDE.md -> Page Status, Bullet Markers): verification is claim-level, so a
claim still pending a raw fact-check must not count toward the page's checked
content. This is what lets a `verified` page accept an incremental ADDITION (a new claim
bullet, a new citation on its own bullet) marked `*[unverified]*` without tripping
the hash and demoting the whole page: a masked new line was never in the hash.
Changing an existing claim is different — altering its text, or newly marking a
previously-unmarked (already-hashed) claim, moves the hash and demotes the page;
editing or adding an UNMARKED claim likewise changes the hash and demotes it (the
involuntary backstop). A page with no markers
hashes exactly as it did before this masking existed, so existing stamps stay
valid. Keep a marked claim to its single bullet line — only the line carrying the
marker is masked, so a multi-line marked bullet's continuation still counts.

The hash function itself is deliberately simple: it masks only `*[unverified]*`
claim lines and frontmatter, nothing else. The verification-neutral edit
allowlist (CLAUDE.md -> Page Status) is enforced at the skill level, not here: a
skill that applies an allowlisted determinate edit (a format fix, an
open-compound de-hyphenation, a spelling normalization, or wrapping an existing
reference in a wikilink) recomputes this hash and re-stamps `verified_hash:` in
the same pass, keeping the page `verified`. So adding allowlist handling does not
touch this script — it only changes whether a skill re-stamps or demotes after a
hash change.

Requires Python 3.10+ (the shared lint-script suite floor; this module alone uses
only 3.8-compatible syntax, but the suite is pinned to 3.10+ by check_wiki.py).
"""

from __future__ import annotations
import hashlib
import re
import sys

_FM_OPEN = '---\n'     # frontmatter opening delimiter
_FM_CLOSE = '\n---\n'  # frontmatter closing delimiter
# The claim-level "awaiting a raw fact-check" marker (literal asterisks are part
# of the token, not Markdown emphasis). Canonically marked callout-bullet lines
# are excluded from the hashed body so a pending claim does not count toward the
# page's checked content. Marker-shaped text elsewhere remains semantic.
# NOTE: this pattern is duplicated as `UNVERIFIED_MARKER_RE` in check_wiki.py.
# Both lint and hashing call the fence/comment-aware helper here; keep the
# duplicate exported pattern identical for its wiring regression. Inline/fenced
# examples, HTML comments, and noncanonical marker-shaped text remain part of
# the semantic body.
_UNVERIFIED_RE = re.compile(
    r'^(> -[ \t]+)\*\[unverified\]\*[ \t]?', re.MULTILINE
)
_MARKDOWN_FENCE = re.compile(
    r'^((?: {0,3}> ?)* {0,3})(`{3,}|~{3,})(.*)$'
)


def _fence_match(
    line: str, fence_character: str | None
) -> re.Match[str] | None:
    """Match a CommonMark fence; backtick info strings cannot use backticks."""
    fence = _MARKDOWN_FENCE.match(line)
    if (
        fence is not None
        and fence_character is None
        and fence.group(2)[0] == '`'
        and '`' in fence.group(3)
    ):
        return None
    return fence


def _mask_inline_code_spans(line: str) -> str:
    """Blank complete CommonMark-style backtick spans on one physical line."""
    masked = list(line)
    index = 0
    while index < len(line):
        if line[index] != '`':
            index += 1
            continue
        run_end = index + 1
        while run_end < len(line) and line[run_end] == '`':
            run_end += 1
        run_length = run_end - index
        search = run_end
        closing_end = -1
        while search < len(line):
            next_tick = line.find('`', search)
            if next_tick < 0:
                break
            candidate_end = next_tick + 1
            while candidate_end < len(line) and line[candidate_end] == '`':
                candidate_end += 1
            if candidate_end - next_tick == run_length:
                closing_end = candidate_end
                break
            search = candidate_end
        if closing_end < 0:
            index = run_end
            continue
        masked[index:closing_end] = ' ' * (closing_end - index)
        index = closing_end
    return ''.join(masked)


def _html_comment_state(line: str, in_comment: bool) -> bool:
    """Return comment state after one line, ignoring inline-code literals."""
    scan = line if in_comment else _mask_inline_code_spans(line=line)
    position = 0
    while position < len(scan):
        if in_comment:
            closing = scan.find('-->', position)
            if closing < 0:
                return True
            in_comment = False
            position = closing + len('-->')
            scan = scan[:position] + _mask_inline_code_spans(
                line=scan[position:]
            )
            continue
        opening = scan.find('<!--', position)
        if opening < 0:
            return False
        in_comment = True
        position = opening + len('<!--')
    return in_comment


def _unverified_line_indexes(text: str) -> set[int]:
    """Return canonical marker lines outside fences and HTML comments."""
    indexes: set[int] = set()
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth = 0
    in_html_comment = False
    for index, line in enumerate(text.splitlines(keepends=True)):
        if in_html_comment:
            in_html_comment = _html_comment_state(
                line=line, in_comment=True
            )
            continue
        fence = _fence_match(line=line, fence_character=fence_character)
        if fence:
            quote_depth = fence.group(1).count('>')
            marker = fence.group(2)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                fence_quote_depth = quote_depth
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and quote_depth == fence_quote_depth
                and not fence.group(3).strip()
            ):
                fence_character = None
                fence_length = 0
                fence_quote_depth = 0
            continue
        if fence_character is not None:
            continue
        marker = _UNVERIFIED_RE.match(line)
        if marker:
            indexes.add(index)
        in_html_comment = _html_comment_state(
            line=line, in_comment=False
        )
    return indexes


def count_unverified_claim_markers(text: str) -> int:
    """Count canonical process markers outside fences and HTML comments."""
    return len(_unverified_line_indexes(text=text))


def body_hash(path: str) -> str:
    """Hash the body with canonical unfenced process-marker lines excluded.

    Line endings are normalized to LF first so a CRLF file is not hashed with its
    frontmatter as body. A page with no frontmatter is hashed whole. A page that
    opens frontmatter (`---`) but has no clean closing `---` line is malformed:
    rather than silently hashing the whole file (frontmatter included) and returning
    a valid-looking hash — which would later demote a correctly-verified page on any
    mechanical frontmatter edit — this raises ValueError so the caller fails loudly
    instead of corrupting the verified-hash trail.

    Raises
    ------
    ValueError
        The page opens a frontmatter block but has no closing `---` delimiter line.
    """
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    # CRLF->LF leaves already-LF files (the common case) byte-identical, so existing
    # verified_hash stamps stay valid; both audit and lint call this one function.
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if text.startswith(_FM_OPEN):
        end = text.find(_FM_CLOSE, len(_FM_OPEN))
        if end == -1:
            raise ValueError(
                f'{path}: frontmatter opened with "---" but has no closing "---" '
                'delimiter line; refusing to hash the whole file as the body'
            )
        body = text[end + len(_FM_CLOSE):]
    else:
        body = text
    # Exclude `*[unverified]*` claim lines from the hashed content (claim-level
    # verification). Dropping the whole line means a pending claim can be edited
    # freely while marked; clearing the marker re-includes it, changing the hash
    # so audit re-stamps. A page with no markers is unchanged.
    masked_indexes = _unverified_line_indexes(text=body)
    body = ''.join(
        line for index, line in enumerate(body.splitlines(keepends=True))
        if index not in masked_indexes
    )
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: body_hash.py <page.md>')
    try:
        print(body_hash(path=sys.argv[1]))
    except (OSError, ValueError) as err:
        sys.exit(f'body_hash.py: {err}')
