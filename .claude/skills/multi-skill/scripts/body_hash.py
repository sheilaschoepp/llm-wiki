#!/usr/bin/env python3
"""Print the SHA-256 of a wiki page's body — the content after the YAML frontmatter.

`audit` runs this to stamp `verified_hash:` when it sets a page `verified`; `lint`
runs it to detect a `verified` page whose checked content changed since (hash
mismatch -> the page is reset to `draft`). Both skills must hash identically, so
both call this one script. The body excludes frontmatter, so mechanical metadata
edits (`updated:`, `status:`, `verified_hash:` itself) do not change the hash.

The hash also excludes any bullet line carrying the `*[unverified]*` claim marker
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
import hashlib
import re
import sys

_FM_OPEN = '---\n'     # frontmatter opening delimiter
_FM_CLOSE = '\n---\n'  # frontmatter closing delimiter
# The claim-level "awaiting a raw fact-check" marker (literal asterisks are part
# of the token, not Markdown emphasis). Lines carrying it are excluded from the
# hashed body so a pending claim does not count toward the page's checked content.
# NOTE: this pattern is duplicated as `UNVERIFIED_MARKER_RE` in check_wiki.py
# (lint counts markers there; here we mask them). Both blank inline-code spans
# before testing for the marker (below / `_mask_code_spans` there), so a literal
# `*[unverified]*` MENTION inside backticks is not treated as a real marker. Keep
# the pattern and the code-span masking identical in both, or masking (here) and
# counting (there) silently disagree — change both together.
_UNVERIFIED_RE = re.compile(r'\*\[unverified\]\*')
# Blank inline-code spans (single-backtick, mirroring check_wiki.py's
# `_mask_code_spans`) before the marker test, so a `*[unverified]*` mentioned
# inside `code` — documentation of the marker, not a pending claim — does not drop
# the line's real content from the hashed body.
_CODE_SPAN_RE = re.compile(r'`[^`]*`')


def body_hash(path: str) -> str:
    """Return the hex SHA-256 of the page body — the text after the YAML frontmatter, with every `*[unverified]*` claim line excluded (claim-level verification; see module docstring).

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
    body = '\n'.join(
        line for line in body.split('\n')
        if not _UNVERIFIED_RE.search(_CODE_SPAN_RE.sub('', line))
    )
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: body_hash.py <page.md>')
    try:
        print(body_hash(path=sys.argv[1]))
    except (OSError, ValueError) as err:
        sys.exit(f'body_hash.py: {err}')
