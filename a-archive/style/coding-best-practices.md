# Best coding practices

> Two-part rule sheet for code Claude writes or reviews. Part 1 covers language-agnostic design principles; Part 2 covers Python style.
>
> **Sources.** Part 1 distils Robert C. Martin (*Clean Code 2e*, *Functional Design*, *The Clean Coder*) and John Ousterhout (*A Philosophy of Software Design 2e*). Part 2 follows PEP 8 + PEP 257 with NumPy-style docstrings.
>
> **Conflict resolution.** Where Martin and Ousterhout disagree (method length, comments, TDD, short variable names), the Ousterhout position usually fits research code better; the four disagreements are flagged inline.

---

# Part 1 — Design principles

Hard rules first; principles second; reading list at the end.

## Layer 1 — Hard rules

Apply mechanically. If a rule blocks something specific, drop to Layer 2.

### Names

- Use intention-revealing names. Variable, function, and class names should answer *what is this, what does it do, why does it exist* without a comment.
- Replace cryptic names with meaningful ones. Exception: loop counters `i, j, k` in tight numeric loops, and well-known math symbols inside a function whose docstring defines them.
- No type-prefix encodings (`strName`, `iCount`, `lst_users`). Type hints carry the type; names carry meaning.
- Pronounceable names. `gen_ymdhms` → `generation_timestamp`.
- Searchable names. Replace magic numbers with named constants (`MAX_RETRIES = 5`).
- Class names are nouns or noun phrases. Function and method names are verbs or verb phrases.
- One word per concept. If `fetch`, `retrieve`, and `get` all show up for the same operation, pick one.
- Don't disinformatively name. `accountList` should actually be a list.
- Avoid noise words in class names: `Manager`, `Processor`, `Data`, `Info` add nothing.
- **Hard to pick a name = design smell.** If you can't name a variable precisely, it probably represents more than one concept. Split it.
- **Use names consistently.** Same name → same purpose; different purpose → different name. The Sprite OS bug (six months to debug) came from `block` referring to both *physical disk block* and *logical file block*. When you need two of a kind, prefix (`srcFileBlock`, `dstFileBlock`).

### Functions

- Functions should be small. Default ceiling: ~20 lines for research code, ~10 lines for shared code. The hard 4-line floor of *Clean Code 1e* is gone in 2e — small still wins, but not at the cost of clarity.
- Functions do one thing. If you can extract a sub-section and name it cleanly, you should.
- One level of abstraction per function (the Stepdown Rule).
- Argument count: 0 is best, 1–2 fine, 3 suspicious, 4+ requires justification. Bundle related args into a dataclass.
- No flag arguments. `do_thing(x, fast=True)` ⇒ split into `do_thing_fast(x)` and `do_thing_careful(x)`. Exception: the flag is genuinely a parameter of one operation (`sort(key=..., reverse=True)`).
- Command–query separation: a function either *does* (returns nothing useful, may have side effects) or *answers* (returns a value, no side effects).
- Return early. Guard clauses over deep `if/else` pyramids.
- Don't return `None` from a collection-returning function. Return an empty list/dict.
- Prefer pure functions. A pure function depends only on its arguments and produces no side effects.

**Counter-view (Ousterhout).** Large cohesive methods can be clearer than many small ones; deep modules with simple interfaces hide complexity better than wide modules with many small public methods. **Depth > length.** Don't extract a 5-line helper just to satisfy a small-functions reflex if the result is more naming overhead than clarity gain. Bad splits create *conjoined methods* — neither readable alone.

### Comments

- Don't comment what the code says. `# increment counter` next to `counter += 1` is noise.
- Acceptable comment kinds: legal/license headers; intent that can't be expressed in code (the *why*); warnings about non-obvious consequences; TODO markers with date and owner; public-API docstrings.
- Delete commented-out code. Version control keeps it.
- Update comments when you update code, or delete them. Stale comments are worse than none.

**Counter-view (Ousterhout).** Comments are essential to abstraction. Function signatures cannot capture units, side effects, preconditions, ordering constraints, or design rationale. **If callers must read the implementation to use a method, there is no abstraction.** A comment explaining *why* the retry limit is 3, what units `timeout_ms` is in, or which RFC a header format follows is genuinely useful and shouldn't be cut on a "comments are failure" reflex. Lower-level comments add precision (units, boundary inclusivity, null semantics, ownership, invariants); higher-level comments enhance intuition (what the block is trying to do; how the reader gets here).

### Error handling

- Use exceptions, not return codes.
- Raise narrow, meaningful types. `raise ValueError("...")` beats `raise Exception("...")`.
- Don't catch `Exception` broadly. Catch the specific exception you can handle. If you must catch wide (top-level loop, retry logic), re-raise or log with full context.
- Define exception classes by *what the caller needs to handle*, not by what raised them.
- Don't swallow exceptions silently. Even a logged warning beats a bare `except: pass`.
- A `try` block is one thing — extract the body if you're tempted to do more.

**Define errors out of existence (Ousterhout).** The best fix for an exception is to redesign the API so the exceptional condition becomes a normal case. Tcl `unset` should be idempotent; Python list slicing returns empty for out-of-range indices instead of throwing. Apply when feasible: it removes the handler from every caller. Other techniques: *mask* exceptions low (TCP retransmits internally), *aggregate* high (one dispatcher-level handler turns the exception's message into an error response), or *just crash* with a clear diagnostic for unrecoverable errors (out-of-memory, internal inconsistency).

### Tests

- Every public function and every non-trivial branch is tested.
- Tests must be **F.I.R.S.T.**: Fast, Independent, Repeatable, Self-validating, Timely.
- One concept per test. If a test asserts five unrelated things, split it.
- Test code uses the same naming/clarity standards as production code. Test code is read more, not less.
- Don't test what types prove (simple property accessors). Test boundaries, edge cases, error paths, regressions.
- For research code: at minimum, test the data-loading layer, the metric computation, and any function whose bug would silently corrupt results.
- Prefer property-based tests (Hypothesis in Python) for anything that operates over a domain (numerics, parsers, transformers).
- Mocks are a code smell. Heavy mocking signals tight coupling. Reach for fakes or in-process equivalents first.
- The REPL is not a substitute for tests. Encode REPL findings into tests.

**Counter-view (Ousterhout) on TDD.** Strict test-driven development "focuses attention on getting specific features working, rather than finding the best design. This is tactical programming pure and simple" (*A Philosophy of Software Design*, §19.4). Endorses unit testing strongly; endorses test-first only when **fixing a bug** (write the failing test, confirm it triggers the bug, then fix). For new code, prefer **Small Bundles** (write a chunk, then test it) — design happens first.

### Classes and types

- Use a class when behaviour and the state it operates on belong together. Otherwise, prefer a function and plain data (a `dataclass` or `TypedDict`).
- Classes should be small, with a single responsibility (one reason to change).
- Don't expose mutable internal state. If a class holds a list, return a copy or an immutable view.
- Don't write a getter and a setter for every attribute. Use direct attribute access (Python has properties for the rare case computation or invariant enforcement is needed). **Getters/setters are shallow methods that violate information hiding** (Ousterhout).
- Data classes for data; behavioural classes for behaviour. Don't mix.
- **Prefer composition over inheritance.** Implementation inheritance creates tight parent-child coupling and leaks state across the hierarchy. Inherit only when the subclass *is-a* the parent in the Liskov sense.
- Don't talk to strangers (Law of Demeter). `a.b.c.d.do_thing()` couples your code to the entire chain. Talk to direct collaborators only.

### Modules and design (Ousterhout core)

- **Modules should be deep.** Powerful functionality behind simple interfaces. Cost = interface area; benefit = functionality. Maximize functionality / interface.
- **Information hiding.** Each module encapsulates a few design decisions (data structures, formats, algorithms). `private` ≠ information hiding — public getters that expose internal state still leak it.
- **Information leakage** (red flag). Same design decision shows up in multiple modules. Worst form is back-door leakage: two classes share knowledge of a fact even though neither exposes it in its interface. Cultivate sensitivity to this.
- **Different layers, different abstractions.** Adjacent layers with the same abstraction = a layer is contributing nothing. Watch for *pass-through methods* (forwards arguments to a same-signature method) and *pass-through variables* (threaded through methods that don't use them — use a context object instead).
- **General-purpose modules are deeper.** Specialized APIs (`backspace(cursor)`, `delete(cursor)`, `deleteSelection(sel)`) leak UI concepts into lower layers and produce many shallow methods. General APIs (`insert(pos, str)`, `delete(start, end)`) push specialization to the edges.
- **Pull complexity downwards.** Better the developer of a module suffers than its users. Configuration parameter you can't justify? Compute the value internally. Network retry interval can be derived from observed RTT — no parameter needed, and it self-tunes.
- **Make the common case as simple as possible.** Defaults, sensible behaviour without configuration, no choices the caller doesn't care about (Java's `BufferedInputStream` over `FileInputStream` is the canonical anti-example).
- **Eliminate special cases in code.** Best fix: design the normal case so edge cases fall out automatically. Editor selection: instead of a "no selection" state variable, represent it as an empty selection (start == end). Single guard test that rules out *all* special cases at once is the best pattern.

### Immutability and state

- Default to immutable data. Mutate only when there's a measured reason.
- A function that takes data, returns transformed data, and mutates nothing is the unit you should reach for first.
- When you do mutate, contain the mutation: one place, named, documented.
- Avoid global mutable state. If you're tempted by a module-level dict, ask whether it should be passed in as a parameter or wrapped in a class with explicit ownership.
- Pipelines (`map`, `filter`, `reduce`, list comprehensions) over imperative loops when data transformation is the point.

### Concurrency

- Don't reach for threads or async unless you have a measured reason. Most "performance" intuitions are wrong without a profiler.
- Concurrency is a decoupling strategy: it separates *what* is done from *when* it's done. Don't reach for it just for speed.
- Shared mutable state across threads is the bug factory. Pass immutable data; if you need shared state, lock it explicitly.
- Concurrency code goes in its own module, separated from business logic.
- Test single-threaded behaviour first; only then add concurrency tests.

### Source control and process

- Boy Scout rule: leave the code cleaner than you found it.
- Commit small, working units. Green test suite per commit, not per branch.
- Prefer feature toggles over long-lived branches. New features stay on main behind a toggle.
- YAGNI: don't write code, parameters, or abstractions for use cases that don't exist yet.
- Don't ship commented-out code, debug `print` calls, or `TODO` markers without owner+date.
- Don't leave dead code in the codebase. Delete it; version control remembers.

### Working with LLM-generated code

- Treat the LLM as autopilot, not pilot. You are the final arbiter of what gets committed.
- Read every line before committing. LLM output looks plausible at the surface and fails on edge cases the prompt didn't enumerate.
- Use LLMs for low-hanging fruit: naming sweeps, boilerplate, refactor mechanics, test scaffolding.
- Don't trust LLMs for architecture, dependency direction, or layer assignments.
- Maintain your own coding skill. You can't oversee an autopilot you can't fly without.

## Layer 2 — Principles with mechanism

When a hard rule is in tension with reality, drop here.

- **Code is read more than it is written.** Save your future self and collaborators time at the cost of slightly more time now. The trade is always worth it.
- **Software is SOFT.** Software exists because we needed easy-to-change machine behaviour. Code that's hard to change defeats the entire reason software exists. Structure has equal or greater value than behaviour.
- **Don't repeat yourself, but don't over-DRY.** Duplication is debt; premature abstraction is a different debt that's harder to undo. If two pieces of code look alike but represent different concepts, leave them duplicated.
- **YAGNI vs general-purpose.** Tension to manage. YAGNI says don't generalize speculatively; Ousterhout says general-purpose modules are deeper. Resolution: **somewhat general-purpose** — functionality matches today's need, interface is broad enough for several uses.
- **Strategic vs tactical programming.** Tactical = "smallest change that makes this work right now." Strategic = working code is necessary but not sufficient; primary goal is design that supports future change. Invest ~10–20% of dev time on design. Crossover happens in months, not years.
- **Design it twice.** First idea is rarely best. For each big decision (interface, implementation, decomposition), sketch at least two radically different options before committing. The comparison is the value, even if the first option wins.
- **Decide what matters.** Good design separates the important from the unimportant. Make important things prominent (interface comments, names, central modules); hide the rest. Two failure modes: treating too many things as important (clutter, shallow classes), or failing to recognize importance (hidden info, missing functionality, unknown unknowns).
- **SOLID.**
  - *SRP* — single responsibility, identified by stakeholder, not line count.
  - *OCP* — open to extension, closed to modification. Add new behaviour as new code, not edits to tested code.
  - *LSP* — subtypes are substitutable for parents. If your subclass throws on parent methods, it's not a subclass.
  - *ISP* — don't force clients to depend on methods they don't use.
  - *DIP* — high-level modules don't depend on low-level modules; both depend on abstractions. Pass dependencies in; don't reach out and grab them.
- **F.I.R.S.T. tests enable change.** Without tests, every refactor risks silent regression; with tests, you can clean fearlessly. Loss of this is the cost of dirty tests.
- **Estimates ≠ commitments.** An estimate is a probability distribution with error bars; a commitment is a promise to deliver. Conflating them creates dishonest planning.
- **Pressure → lean on disciplines, not abandon them.** When pressure rises, the temptation is to skip tests, refactoring, review. That's exactly when those disciplines are paying for themselves.

## Layer 3 — Red flags (Ousterhout)

See one, stop and reconsider:

- **Shallow module** — interface nearly as complex as implementation.
- **Information leakage** — same design decision in multiple modules.
- **Temporal decomposition** — module boundaries follow execution order rather than knowledge ownership.
- **Overexposure** — common-feature API forces callers to learn rare features.
- **Pass-through method** — does nothing except forward arguments to a same-signature method.
- **Pass-through variable** — threaded through methods that don't use it.
- **Conjoined methods** — neither understandable without the other.
- **Repetition** — same nontrivial code appears more than once.
- **Special-general mixture** — general-purpose mechanism contaminated with code specialized for one use of it.
- **Comment repeats code** — the comment can be derived from the code next to it.
- **Implementation documentation contaminates interface** — interface comment describes how rather than how-to-use.
- **Vague name** — `getCount`, `result`, `data`, `blinkStatus`.
- **Hard to pick a name** — variable represents more than one concept; split it.
- **Hard to describe** — interface comment can't be both short and complete; the abstraction is wrong.
- **Nonobvious code** — first guess about behaviour is wrong; reduce information needed, lean on conventions, or document the surprise.

## Reading list

If a rule looks wrong for your situation, read the source:

- Robert C. Martin. *Clean Code: A Handbook of Agile Software Craftsmanship, 2nd Edition* (2025). The mechanical rules layer.
- Robert C. Martin. *Functional Design: Principles, Patterns, and Practices* (2023). Immutability, functional patterns, SOLID restated functionally.
- Robert C. Martin. *The Clean Coder: A Code of Conduct for Professional Programmers* (2011). Professional discipline, pressure handling, estimation.
- John Ousterhout. *A Philosophy of Software Design, 2nd Edition* (2021). Design philosophy, deep modules, complexity reduction.

---

# Part 2 — Python code style

PEP 8 + PEP 257 + NumPy-style docstrings. Enforced via `ruff` (formatter and linter) and `mypy` or `pyright` (strict type checking).

## Imports

Imports go at the top of the file, after the module docstring. **One import per line.** Group imports into three blocks separated by a blank line:

1. Standard library
2. Third-party packages
3. Local modules

Within each block:

- Place `import X` lines before `from X import Y` lines.
- Sort each subgroup alphabetically by module name.

Prefer **absolute imports** — they survive file moves and are easier to trace. **Relative imports** (`from .data import x`) are acceptable for intra-package imports only. **Avoid wildcard imports** (`from module import *`); they pollute the namespace.

```python
# Good
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from my_project.data import load_experiments
from my_project.metrics import compute_moving_average

# Bad — multiple imports per line, no grouping, wildcard import.
import os, sys, json
from numpy import *
```

## Blank lines

- **Two blank lines** between top-level functions and classes.
- **One blank line** between methods inside a class.
- **Use blank lines sparingly inside functions.** If a function needs internal blank lines to be readable, that's usually a sign to split it into smaller functions.

```python
import json


def load_config(path: str) -> dict:
    """Load JSON config from disk."""
    with open(path) as f:
        return json.load(f)


def save_config(path: str, config: dict) -> None:
    """Write JSON config to disk."""
    with open(path, 'w') as f:
        json.dump(config, f)


class Greeter:
    """Formats greetings for a named user."""

    user_id: int

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def greet(self, message: str) -> str:
        return self._format(message=message)

    def _format(self, message: str) -> str:
        return f'[{self.user_id}] {message}'
```

## Line length

| Element  | Limit                                            |
|----------|--------------------------------------------------|
| Code     | 79 characters                                    |
| Comments | 72 characters (including `#` and leading space)  |

Comment lines must be **packed tight**: every line except the last contains as many whole words as fit within 72 characters. If the next word would still fit on the current line, it belongs there — breaking earlier is a violation.

```python
# Good — each line packed to within a few chars of 72.
# Retry up to three times to handle transient network errors from the
# remote API.
for attempt in range(3):
    ...

# Bad — first line wraps early when more would still fit.
# Retry up to three times to handle transient
# network errors from the remote API.
for attempt in range(3):
    ...

# Bad — single line exceeds the 72-char comment limit.
# Retry the request up to three times in order to gracefully handle temporary,
# intermittent network issues.
for attempt in range(3):
    ...
```

### Line continuation

When a line would exceed 79 characters, prefer **implicit continuation** (parentheses, brackets, or braces) over backslashes (`\`). Backslashes are error-prone — a stray trailing space breaks them.

```python
# Good — wrap in parentheses to enable implicit continuation.
income = (
    gross_wages
    + taxable_interest
    + dividends
    - ira_deduction
)

# Bad — backslash continuation in an expression with no natural
# brackets.
income = gross_wages \
    + taxable_interest \
    + dividends \
    - ira_deduction
```

For long strings, exploit Python's implicit string concatenation inside parentheses:

```python
# Good
message = (
    'Retry up to three times to handle transient '
    'network errors from the remote API.'
)

# Bad
message = 'Retry up to three times to handle transient ' \
    'network errors from the remote API.'
```

**Hanging indents** are the standard style for wrapped function calls and definitions: no arguments on the opening line, continuation lines indented one extra level, closing delimiter on its own line.

```python
# Good — hanging indent.
tracker = CostTracker(
    log_path=path,
    cost_per_m_input=2.5,
    cost_per_m_cached=0.25,
    cost_per_m_output=10.0,
)

# Bad — arguments on the opening line defeat the hanging indent.
tracker = CostTracker(log_path=path,
    cost_per_m_input=2.5,
    cost_per_m_cached=0.25,
    cost_per_m_output=10.0)
```

**Break before binary operators**, not after. This keeps each operator visually attached to its operand and reads more like math.

```python
# Good — operators lead each line.
total_cost = (
    input_tokens * cost_per_m_input
    + cached_tokens * cost_per_m_cached
    + output_tokens * cost_per_m_output
)

# Bad — operators trail, harder to scan the operation on each line.
total_cost = (
    input_tokens * cost_per_m_input +
    cached_tokens * cost_per_m_cached +
    output_tokens * cost_per_m_output
)
```

## Whitespace

**One space around binary operators** — assignment, comparison, arithmetic, boolean:

```python
# Good
total = input_tokens + output_tokens
if count >= max_attempts:
    ...

# Bad
total=input_tokens+output_tokens
if count>=max_attempts:
    ...
```

**No space around `=` in keyword arguments or unannotated defaults.** When a default has a type annotation, use spaces around `=` (`retries: int = 3`):

```python
# Good
def load(path: str, retries: int = 3) -> str:
    ...

result = load(path='file.csv', retries=5)

# Bad
def load(path: str, retries: int=3) -> str:
    ...

result = load(path = 'file.csv', retries = 5)
```

**No extraneous whitespace** inside brackets, before commas, or before colons:

```python
# Good
items = [1, 2, 3]
data = {'key': 'value'}
func(arg=value, kwarg=1)

# Bad
items = [ 1, 2 , 3 ]
data = { 'key' : 'value' }
func( arg=value , kwarg=1 )
```

**Optional precedence relaxation:** PEP 8 lets you drop spaces around higher-precedence operators when mixing precedences, to make binding visible. This is the one allowed exception to the "one space" rule above — both forms below are valid.

```python
# Standard — uniform spacing.
hypot = x * x + y * y

# Optional — tighter binding around * highlights precedence.
hypot = x*x + y*y
```

Note that `ruff format` and `black` always put one space around every binary operator. If you use either formatter, you'll get the first form.

## String quotes

Use single quotes for strings, with two exceptions:

- When the string contains a single quote, use double quotes to avoid escaping.
- Triple-quoted strings (docstrings, multi-line literals) always use double quotes (`"""`), per PEP 257.

```python
# Good
name = 'Claude'
path = '/home/user/file.pdf'
message = "It's working"

# Bad
name = "Claude"
```

## Comments

### Philosophy

Comment only where the code's intent isn't obvious from the code itself.

- **Prefer one short line.** If a comment spans more than 2–3 wrapped lines, tighten it or move the detail into a docstring.
- **Explain *why*, not *what*.** Reserve comments for intent, constraints, edge cases, or context a reader can't infer from the code.
- **Assume the reader knows Python, not your codebase.** Explain project-specific context, not language syntax.

### Inline comments

Inline comments go on the line immediately above the code they describe.

- **Write explanatory comments as complete sentences.** Conventional markers (`# Good`, `# Bad`, `# TODO`, `# noqa`) are exempt.
- **Capitalize the first word and end with a period**, unless the sentence starts with an identifier (variable, function, or module name) — never alter the case of an identifier.
- **Don't restate what the code already says.**

```python
# Good
# Download PDF and extract text from first page.
result = extract_first_page(pdf_url=url)

# Good — sentence begins with an identifier; lowercase preserved.
# extract_first_page returns None when the PDF has no text layer.
result = extract_first_page(pdf_url=url)

# Bad — restates the code.
# pdf extraction
result = extract_first_page(pdf_url=url)
```

```python
# Good
# Retry up to three times to handle transient network errors.
for attempt in range(3):
    ...

# Bad — paraphrases the next line.
# Loop three times.
for attempt in range(3):
    ...
```

## Docstrings

Every function, method, and class needs a docstring. PEP 8 defers conventions to **PEP 257**: triple double quotes, summary on its own line for multi-line docstrings, closing `"""` on its own line.

For a one-liner, keep the closing `"""` on the same line:

```python
def extract_first_page(pdf_url: str) -> str:
    """Download a PDF and return the text of the first page."""
    ...
```

For anything longer, use **NumPy style** — the standard in scientific Python (used by NumPy, SciPy, pandas, scikit-learn, matplotlib). Section headers underlined with dashes make dense signatures easy to scan, and Sphinx renders them natively via the `napoleon` extension.

```python
def compute_moving_average(
    values: list[float],
    window_size: int = 10,
) -> list[float]:
    """
    Compute the moving average of a numeric series.

    Parameters
    ----------
    values : list of float
        The input series, one sample per step.
    window_size : int, optional
        Number of samples per averaging window (default: 10).

    Returns
    -------
    list of float
        The average over each full window, in order.

    Raises
    ------
    ValueError
        If values is empty or window_size < 1.

    Examples
    --------
    >>> compute_moving_average(values=[1.0, 2.0, 3.0, 4.0], window_size=2)
    [1.5, 2.5, 3.5]
    """
    ...
```

Standard sections, in order:

- **Parameters** — every argument, formatted as `name : type` with the description indented on the line(s) below.
- **Returns** — the return value's type and meaning. Skip for `-> None` returns.
- **Yields** — for generators, in place of Returns.
- **Raises** — exceptions the function deliberately raises.
- **Examples** — runnable doctest blocks (`>>>` prompts) for non-obvious usage.
- **Notes** — caveats, references, or implementation details that don't fit elsewhere.

Skip any section that doesn't apply. A function that takes no arguments and returns nothing only needs the summary line.

**Classes** use NumPy style with an `Attributes` section in place of `Parameters`. The class docstring documents what the class is and its public attributes:

```python
class DataSeries:
    """
    A sequence of timestamped samples.

    Attributes
    ----------
    series_id : int
        Unique identifier for the series.
    samples : list of tuple
        List of (timestamp, value) pairs in temporal order.
    metadata : dict
        Free-form metadata: source ID, collection settings, etc.
    """

    series_id: int
    samples: list[tuple[str, str]]
    metadata: dict

    def __init__(
        self,
        series_id: int,
        samples: list[tuple[str, str]],
        metadata: dict,
    ) -> None:
        self.series_id = series_id
        self.samples = samples
        self.metadata = metadata
```

Public methods need their own docstrings. `__init__` and other dunders can be skipped if the class docstring covers their behaviour; otherwise document them like any other method.

## Type hints

Annotate every function parameter, every return value (including `-> None`), and every instance attribute. Local variables don't require annotation — let the type checker infer them.

**Use modern syntax (Python 3.10+):**

- Built-in generics, not `typing` aliases: `list[int]` not `List[int]`; `dict[str, float]` not `Dict[str, float]`.
- `X | Y` for unions, not `Union[X, Y]`. `X | None` for optionals, not `Optional[X]`.
- `Any` is allowed but should be a deliberate choice — if you reach for it, ask whether the type can be made more specific first.

```python
# Good
def parse(raw: list[str], limit: int | None = None) -> dict[str, int]:
    ...

# Bad — outdated typing imports.
from typing import Dict, List, Optional

def parse(raw: List[str], limit: Optional[int] = None) -> Dict[str, int]:
    ...
```

## Keyword arguments

Pass arguments by keyword whenever a function accepts them. This labels each value at the call site and prevents misordering.

**Exceptions** where positional is idiomatic:

- **Operators** — no kwarg form exists.
- **Built-ins** — `len`, `range`, `open`, `print`, `isinstance`, `type`, `hasattr`, `getattr`, `min`, `max`, `sum`, `enumerate`, `zip`, `map`, `filter`, `sorted`, `iter`, `next`, `str`, `int`, `repr`, etc.
- **Exception constructors** — `ValueError(msg)`, `TypeError(msg)`, etc.
- **Standard library helpers** where positional is universal — `json.load`/`dump`, file methods (`f.read`, `f.write`), `os.path.*`, `pathlib.Path` operations.
- **Test framework assertions** — `unittest`'s `assertEqual`, `assertTrue`, `assertRaises`, etc.

When in doubt, match the convention shown in the function's own documentation.

```python
# Good
result = extract_first_page(pdf_url=url)
tracker = CostTracker(
    log_path=path,
    cost_per_m_input=2.5,
    cost_per_m_cached=0.25,
    cost_per_m_output=10.0,
)

# Bad — positional arguments are unlabelled and easy to misorder.
result = extract_first_page(url)
tracker = CostTracker(path, 2.5, 0.25, 10.0)
```

## Idiomatic patterns

From PEP 8's "Programming Recommendations" — the ones worth memorizing:

**Use `is` and `is not` for `None` comparisons**, never `==`:

```python
# Good
if value is None:
    ...

# Bad
if value == None:
    ...
```

**Don't compare booleans with `==`.** Use the value directly:

```python
# Good
if is_active:
    ...

# Bad
if is_active == True:
    ...
```

**Use truthiness for empty-sequence checks**, not `len()`:

```python
# Good
if not items:
    raise ValueError('items must not be empty')

# Bad
if len(items) == 0:
    raise ValueError('items must not be empty')
```

**Use `isinstance()` for type checks**, not `type()`:

```python
# Good
if isinstance(value, int):
    ...

# Bad
if type(value) == int:
    ...
```

**Use `str.startswith()` and `str.endswith()`** instead of slicing:

```python
# Good
if filename.endswith('.csv'):
    ...

# Bad
if filename[-4:] == '.csv':
    ...
```

**Prefer `def` over assigning a lambda to a name.** A named lambda has all the downsides of a function (it shows up by name in tracebacks) and none of the benefits (no docstring, no annotations):

```python
# Good
def square(x: int) -> int:
    return x * x

# Bad
square = lambda x: x * x
```

**Inherit from `Exception`, not `BaseException`**, for custom exceptions. `BaseException` is reserved for things like `KeyboardInterrupt` that callers should almost never catch.

## Testing

Whenever you add or meaningfully change a helper with testable logic — parsing, matching, span math, payload building, normalization, etc. — write unit tests in `tests/`.

### File and class layout

- **One test file per script:** `tests/test_<scriptname>.py`. Helpers in `<NN>_quotes.py` are tested in `tests/test_quotes.py`.
- **Use `unittest`.** Group tests by the function under test into their own `TestCase` subclass (e.g. `TestParseQuotes`, `TestDiagnoseUnmatchedQuote`).
- **Digit-prefixed scripts** must be loaded via `tests/_script_loader.py`. Add a binding there (e.g. `quotes_script = _load_script(script_filename='<NN>_quotes.py', module_name='quotes_script')`) and import it in the test file.

### Coverage

Every public helper needs at least:

- One test for the happy path.
- One test for each of the edge cases that matter (empty input, boundary values).
- One test for each distinct code path through the function.

### Writing tests

- **Independence.** Each test runs in isolation — no shared mutable state, no dependency on test execution order. Reordering or running a single test should always work.
- **Descriptive names.** A test name should tell you what broke without reading the body. Use `test_<function>_<condition>_<expected>` form, e.g. `test_parse_quotes_returns_empty_list_when_input_has_no_quotes`.
- **Arrange / Act / Assert.** Inside each test body, separate the three phases with blank lines: set up inputs, call the code under test, assert on the result.
- **Test behaviour, not implementation.** Assert on outputs and observable side effects, not on internal state or which methods got called. This lets you refactor freely.
- **Descriptive assertion messages.** Pass `msg=...` to assertions so failure output is informative — e.g. `msg='moving average of a constant series should equal that constant'`.
- **Keep tests fast.** Anything over a second should be marked slow and excluded from the default run; you'll be running the suite many times a day during a refactor.

### Running tests

After writing or editing tests, run the full suite and confirm everything passes before declaring the task done:

```bash
python3 -m unittest discover -s tests -t .
```

## Tooling

### Linters and formatters

- **`ruff`** for linting and formatting. Configure with `line-length = 79`. `ruff format` keeps single quotes by default.
- **`mypy`** or **`pyright`** in strict mode for type checking — required to enforce the type-hints rule.

### VS Code

To get NumPy-style docstrings auto-generated:

- Install the **autoDocstring** extension.
- Set `"autoDocstring.docstringFormat": "numpy"` in `settings.json`.
- Use **Pylance** as the language server (this is the default — confirm with `"python.languageServer": "Pylance"`).

With type hints on the function signature, autoDocstring pre-fills the `Parameters` section with the correct types when you type `"""` on the line below a `def`.
