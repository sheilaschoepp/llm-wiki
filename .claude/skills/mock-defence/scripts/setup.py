#!/usr/bin/env python3
"""Guided setup for the mock-defence skill.

Walks you through the two things that are yours to provide — the document you
are defending (references/defaults.md) and your real committee's member
profiles. The generic machinery and the fictional panels (proxy, cognitive,
specialist) already work as shipped; this only fills in your parts.

    python scripts/setup.py

Nothing is overwritten without asking. Re-run any time to add more members.
Stdlib only, no dependencies.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS = SKILL_ROOT / "references" / "defaults.md"
COMMITTEES = SKILL_ROOT / "references" / "committees"

DEFAULTS_PLACEHOLDER = "path/to/your-document.pdf"

DEFAULTS_PROSE = (
    "User-maintained; the skill reads this at Step 2. Set the document you are "
    "currently defending and the event slug that names its occasion (the slug "
    "also names the report files). Edit the values when the defended document "
    "changes; when this file is missing or names no document, the skill asks "
    "instead. The timezone is optional — it pins report timestamps so filenames "
    "sort consistently when the vault syncs across machines; drop the line to "
    "use local time."
)

PREREQUISITES = """\
Before you begin, gather these — or skip any now and fill it in later:

  - Your document: the proposal or thesis you are defending, and its file path.
  - Your committee roster: your supervisor(s), any co-supervisor, and the
    arm's-length examiners. Your supervisor is a member too — add them.
  - Per member: name, role/title, institution, and public info to fill the
    profile — faculty page, Google Scholar, research focus, a few key papers.
  - Optional, per member: a BibTeX (.bib) export of their recent publications,
    saved where you can point this script at it (Google Scholar / Semantic
    Scholar / Zotero -> export as BibTeX). It grounds questions on their own work.

Only Python 3 (standard library) is needed to run this wizard.
"""

MEMBER_TEMPLATE = """\
# {name}

> Profile — {header}. Neutral ground-truth facts only; sources at the bottom.

## Identity

- **Title**: {title}
- **Affiliations**:
- **Office**:
- **Email**:
- **Education**:

## Research focus

- One or two sentences on what this person actually works on — their area and
  central research question. Neutral facts only, not your read of how they will
  examine (that inference lives in the event prep file, never here).

## Key themes

- Recurring topics, methods, named systems, and benchmarks their work centres on.

## Selected recent works (2020–)

- **Author(s) (year). Title.** Venue. One line on what it did.

## Sources

- Personal / lab website:
- Google Scholar:
- Institutional page:
"""

COMMITTEE_MANIFEST = """\
# {display}

- **kind**: real-people
- **summary**: {summary}
- **members**: every profile in `profiles/` (a leading-underscore `_TEMPLATE.md` is a scaffold, not a member).
- **question source**: the event prep companion in this folder (`<event>-prep.md`), when present. Profiles give each member's lens (neutral facts); the prep file gives questioning style and seed questions.
- **fabrication rule**: real people — ground every question in the member's real profile and what the document actually says. Never invent a member's paper, position, or stance.
- **profile shape**: neutral ground-truth facts only (Identity, Research focus, Key themes, Selected recent works, Sources).
"""


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        reply = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        print()
        return default
    return reply or default


def confirm(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    reply = ask(f"{prompt} ({hint})").lower()
    return default if not reply else reply.startswith("y")


def kebab(name: str) -> str:
    """Jane A. Khan -> jane-a-khan; folds accents (Muñoz -> munoz)."""
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_name = decomposed.encode("ascii", "ignore").decode("ascii").replace(".", " ")
    parts = re.split(r"[^A-Za-z0-9]+", ascii_name)
    return "-".join(p.lower() for p in parts if p)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(SKILL_ROOT))
    except ValueError:
        return str(path)


def banner(text: str) -> None:
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72)


def write_file(path: Path, content: str, kind: str, overwrite_marker: str = "") -> bool:
    """Write, but never clobber real content silently.

    overwrite_marker: if the existing file contains this string it is treated as
    an untouched shipped placeholder and replaced without asking.
    """
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            print(f"  unchanged: {rel(path)}")
            return False
        is_placeholder = bool(overwrite_marker) and overwrite_marker in existing
        if not is_placeholder and not confirm(f"  {rel(path)} exists — overwrite?", default=False):
            print(f"  kept existing: {rel(path)}")
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {kind}: {rel(path)}")
    return True


def setup_defaults() -> str:
    banner("Step 1 of 3 — the document you're defending")
    print("Written to references/defaults.md. The skill defends this by default;")
    print("you can always name another document when you start a session.\n")
    document = ask("Path to your document", DEFAULTS_PLACEHOLDER)
    event = ask("Event slug (also names the report files)", "candidacy")
    timezone = ask("Timezone, IANA e.g. UTC (blank = local time)", "")

    lines = [
        "# Defaults — the document under defence",
        "",
        DEFAULTS_PROSE,
        "",
        f"- document: `{document}`",
        f"- event: `{event}`",
    ]
    if timezone:
        lines.append(f"- timezone: `{timezone}`")
    write_file(DEFAULTS, "\n".join(lines) + "\n", "defaults", overwrite_marker=DEFAULTS_PLACEHOLDER)
    return event


def pick_committee() -> Path:
    """Return the profiles/ dir of the chosen committee, creating it if new."""
    name = ask("Committee folder name", "real-committee")
    folder = COMMITTEES / name
    profiles = folder / "profiles"
    if folder.exists():
        profiles.mkdir(parents=True, exist_ok=True)
        return profiles

    print(f"  new committee — creating {rel(folder)}")
    display = ask("  Committee display name", name.replace("-", " ").capitalize())
    summary = ask("  One-line summary", "Your actual examiners.")
    profiles.mkdir(parents=True, exist_ok=True)
    write_file(
        folder / "committee.md",
        COMMITTEE_MANIFEST.format(display=display, summary=summary),
        "manifest",
    )
    return profiles


def make_profile(name: str, role: str, institution: str) -> str:
    bits = [b for b in (role, institution) if b]
    header = ", ".join(bits) if bits else "<role>, <institution>"
    title = ", ".join(bits) if bits else "<rank, department, institution>"
    return MEMBER_TEMPLATE.format(name=name, header=header, title=title)


def copy_bib(src: Path, dest: Path) -> None:
    if not src.exists():
        print(f"  no file at {src} — skipped the .bib (you can add it later)")
        return
    write_file(dest, src.read_text(encoding="utf-8", errors="replace"), "bib")


def setup_members(profiles: Path) -> list[str]:
    banner("Step 2 of 3 — your committee members")
    print("Add one profile per member. Each is a neutral-facts scaffold you then")
    print("fill in (README.md has a prompt you can paste a member's Scholar page")
    print("or .bib into). Leave the name blank to finish.\n")
    added: list[str] = []
    while True:
        name = ask("Member full name (blank to finish)")
        if not name:
            break
        stem = ask("  Filename stem", kebab(name))
        role = ask("  Role / title (optional)", "")
        institution = ask("  Institution (optional)", "")
        write_file(profiles / f"{stem}.md", make_profile(name, role, institution), "profile")
        bib = ask("  Path to a .bib export for this member (optional)", "")
        if bib:
            copy_bib(Path(bib).expanduser(), profiles / f"{stem}.bib")
        added.append(name)
        print()
    return added


def setup_prep(folder: Path, event: str, members: list[str]) -> None:
    banner("Step 3 of 3 — event prep file (optional)")
    lines = [
        f"# {event.capitalize()} committee — prep notes",
        "",
        "> Prep companion to the neutral profiles in `profiles/`. Holds the "
        "cross-cutting design pressure points and, per member, their likely "
        "questions and questioning style — the profiles give the lens, this file "
        "gives the style. Agent-refinable; the profiles stay ground truth.",
        "",
        "## Design pressure points (any member may push here)",
        "",
        "- The methodological soft spots any examiner could press; fill these in "
        "from your document's load-bearing assumptions, confounds, and most-"
        "exposed claims.",
    ]
    for name in members:
        lines += [
            "",
            f"## {name}",
            "",
            "### What they probe in an exam",
            "",
            "- ",
            "",
            "### Likely questions",
            "",
            "- ",
        ]
    write_file(folder / f"{event}-prep.md", "\n".join(lines) + "\n", "prep")


def summarize(event: str, members: list[str]) -> None:
    banner("Done")
    if members:
        print(f"Created / updated {len(members)} profile(s): {', '.join(members)}")
    print("\nNext steps:")
    print("  1. Fill in each profile with neutral public facts. README.md has a")
    print("     drafting prompt — paste a member's faculty page / Scholar list / .bib")
    print("     into it, then verify the draft against the sources.")
    print("  2. Drop a same-stem .bib beside any profile to ground own-work questions")
    print("     (see profiles/_TEMPLATE.bib for the shape).")
    print(f'  3. Start a drill: ask the skill "Run a mock defence" (event: {event}).')
    print("\nThe fictional panels (proxy, cognitive, specialist) work now with no setup.")


def main() -> int:
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__)
        return 0

    banner("mock-defence — guided setup")
    print(f"Skill folder: {SKILL_ROOT}")
    print("This fills in the parts that are yours: your document and your committee.\n")
    print(PREREQUISITES)
    if not confirm("Ready to continue?"):
        print("\nNo problem — gather what you need, then re-run: python scripts/setup.py")
        return 0

    event = "candidacy"
    if confirm("\nSet up the defended document now?"):
        event = setup_defaults()

    members: list[str] = []
    profiles: Path | None = None
    if confirm("\nSet up a real committee now?"):
        profiles = pick_committee()
        members = setup_members(profiles)

    if profiles is not None and members and confirm("\nScaffold an event prep file for these members?"):
        setup_prep(profiles.parent, event, members)

    summarize(event, members)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nSetup cancelled. Nothing further written.")
        sys.exit(1)
