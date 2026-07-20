#!/usr/bin/env python3
"""
check_kwargs.py — flag positional calls to user-defined functions.

Why a separate script? The keyword-arguments rule in
a-archive/style/coding-best-practices.md ('Pass arguments by keyword
whenever a function accepts them') is meant to apply to every .py file
under scripts/. As a judgement check it depended on the agent reading
every file every pass — and the agent kept missing call sites
distributed across multiple scripts. Promoting the check to a
deterministic script makes coverage mechanical: every Call node in
every .py file is examined.

Strategy: AST-walk each Python file under scripts/. For each Call node,
flag it when:
  - The call target is a bare Name (not an Attribute like obj.method()),
  - The name is NOT in the allow-list of built-ins, exception types,
    and PEP-8-exempt helpers from coding-best-practices.md, AND
  - The call has at least one positional argument.

Attribute calls (obj.method(), module.func()) are always allowed,
matching the project's exception list which exempts stdlib helpers like
json.load, pathlib.Path operations, and file methods. The allow-list
covers the bare-name exceptions explicitly enumerated in
coding-best-practices.md.

Output is the same JSON-finding shape as check_structure.py, with
check_id 'positional_call' and severity 'error' — best-coding-
practices.md marks this as a hard rule the user has flagged as theirs.

Usage:
    python check_kwargs.py <skill-dir-or-scripts-dir>
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

# Bare-name callables exempt from the keyword-only rule. Sourced from
# the 'Exceptions' list in a-archive/style/coding-best-practices.md
# (under 'Keyword arguments'). Keep in sync with that file.
ALLOW_LIST_BUILTINS = frozenset({
    # Built-ins commonly used positionally.
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
    'callable', 'chr', 'classmethod', 'complex', 'dict', 'dir',
    'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
    'getattr', 'hasattr', 'hash', 'hex', 'id', 'int', 'isinstance',
    'issubclass', 'iter', 'len', 'list', 'map', 'max', 'memoryview',
    'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print',
    'property', 'range', 'repr', 'reversed', 'round', 'set',
    'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
    'super', 'tuple', 'type', 'vars', 'zip',
})

# Standard exception constructors — instantiated positionally with a
# message string is universal.
ALLOW_LIST_EXCEPTIONS = frozenset({
    'ArithmeticError', 'AssertionError', 'AttributeError',
    'BlockingIOError', 'BrokenPipeError', 'BufferError', 'BytesWarning',
    'ChildProcessError', 'ConnectionAbortedError', 'ConnectionError',
    'ConnectionRefusedError', 'ConnectionResetError',
    'DeprecationWarning', 'EOFError', 'EnvironmentError', 'Exception',
    'FileExistsError', 'FileNotFoundError', 'FloatingPointError',
    'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError',
    'ImportWarning', 'IndentationError', 'IndexError',
    'InterruptedError', 'IsADirectoryError', 'KeyError',
    'KeyboardInterrupt', 'LookupError', 'MemoryError',
    'ModuleNotFoundError', 'NameError', 'NotADirectoryError',
    'NotImplementedError', 'OSError', 'OverflowError',
    'PendingDeprecationWarning', 'PermissionError',
    'ProcessLookupError', 'RecursionError', 'ReferenceError',
    'ResourceWarning', 'RuntimeError', 'RuntimeWarning',
    'StopAsyncIteration', 'StopIteration', 'SyntaxError',
    'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError',
    'TimeoutError', 'TypeError', 'UnboundLocalError',
    'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError',
    'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning',
    'ValueError', 'Warning', 'ZeroDivisionError',
})

# Other bare-name stdlib helpers where positional is universal. Sourced
# from the 'Standard library helpers where positional is universal'
# clause in coding-best-practices.md. Conservative — add to this list
# only when a real call site is flagged that the user decides should be
# allowed.
ALLOW_LIST_OTHER = frozenset({
    # pathlib — Path('some/path') is the documented constructor form.
    'Path', 'PurePath', 'PurePosixPath', 'PureWindowsPath',
    'PosixPath', 'WindowsPath',
    # datetime — datetime(2026, 1, 1) is the documented constructor.
    'date', 'datetime', 'time', 'timedelta', 'timezone',
    # decimal / fractions — same positional pattern.
    'Decimal', 'Fraction',
    # collections — Counter(['a', 'b']), deque([...]), etc.
    'Counter', 'OrderedDict', 'defaultdict', 'deque', 'namedtuple',
})

ALLOW_LIST = (
    ALLOW_LIST_BUILTINS | ALLOW_LIST_EXCEPTIONS | ALLOW_LIST_OTHER
)


def call_has_positional_args(call: ast.Call) -> bool:
    """Return True if the call passes at least one positional argument.

    `*args` unpacking counts as positional (the unpacked values arrive
    positionally at the callee). `**kwargs` unpacking is fine.
    """
    return len(call.args) > 0


def call_target_name(call: ast.Call) -> str | None:
    """Return the bare-name function being called, or None.

    Returns None for attribute calls (obj.method()), subscript calls
    (foo[0]()), and lambda calls — all of which fall outside the
    keyword-arg rule's scope.
    """
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    return None


def find_positional_calls(file_path: Path) -> list[dict]:
    """Walk one .py file and return findings for positional calls.

    A finding is emitted when the call target is a bare name not in
    ALLOW_LIST and the call has one or more positional args.
    """
    try:
        source = file_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as exc:
        # A non-UTF-8 / unreadable .py must surface as an actionable
        # finding, never crash the scanner (an uncaught error here exits
        # 1 with no JSON and blocks the lint loop). Parallels the
        # script_syntax_error path below.
        return [{
            'severity': 'error',
            'check_id': 'script_unreadable',
            'file': file_path.name,
            'line': None,
            'message': f'Script could not be read as UTF-8 text: {exc}',
            'fix_hint': (
                'Re-save the file as UTF-8, or remove it from scripts/ '
                'if it is not a Python source file.'
            ),
        }]
    try:
        tree = ast.parse(source=source, filename=str(file_path))
    except SyntaxError as exc:
        return [{
            'severity': 'error',
            'check_id': 'script_syntax_error',
            'file': file_path.name,
            'line': exc.lineno,
            'message': f'Python syntax error: {exc.msg}',
            'fix_hint': 'Fix the syntax error before re-running checks.',
        }]

    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_target_name(call=node)
        if name is None:
            continue
        if name in ALLOW_LIST:
            continue
        if not call_has_positional_args(call=node):
            continue
        findings.append({
            'severity': 'error',
            'check_id': 'positional_call',
            'file': file_path.name,
            'line': node.lineno,
            'message': (
                f"Call to '{name}' passes positional argument(s); "
                f"coding-best-practices.md requires keyword arguments "
                f"for non-stdlib calls."
            ),
            'fix_hint': (
                f"Rewrite the call to use keyword arguments "
                f"(e.g., '{name}(arg=value)' instead of "
                f"'{name}(value)'). If '{name}' is a stdlib helper or "
                f"a project-wide exception, add it to ALLOW_LIST_OTHER "
                f"in scripts/check_kwargs.py with a one-line "
                f"justification."
            ),
        })
    return findings


def resolve_target_files(target: Path) -> list[Path]:
    """Return the list of .py files to scan for a given input path.

    A skill directory yields every scripts/*.py.
    A scripts/ directory yields every *.py inside it.
    A single .py file yields just that file.
    """
    if target.is_dir():
        scripts_dir = (
            target if target.name == 'scripts' else target / 'scripts'
        )
        if not scripts_dir.is_dir():
            return []
        return sorted(
            path for path in scripts_dir.glob('*.py')
            if path.is_file()
        )
    if target.suffix == '.py' and target.is_file():
        return [target]
    return []


def annotate_findings_with_relative_path(
    findings: list[dict],
    file_path: Path,
    skill_root: Path,
) -> None:
    """Rewrite each finding's 'file' field to be relative to skill_root.

    A script under scripts/ becomes 'scripts/<name>.py'.
    """
    try:
        relative = file_path.relative_to(skill_root)
    except ValueError:
        relative = Path(file_path.name)
    relative_str = str(relative)
    for finding in findings:
        finding['file'] = relative_str


def main() -> int:
    if len(sys.argv) != 2:
        print(
            'Usage: python check_kwargs.py <skill-dir-or-scripts-dir>',
            file=sys.stderr,
        )
        return 2

    target = Path(sys.argv[1]).expanduser().resolve()
    if not target.exists():
        print(f'Error: path not found: {target}', file=sys.stderr)
        return 2

    files = resolve_target_files(target=target)
    if not files:
        # No scripts/ folder means nothing to check — emit empty list
        # rather than erroring. Many skills have no bundled scripts.
        print(json.dumps([], indent=2))
        return 0

    if target.is_dir() and target.name != 'scripts':
        skill_root = target
    elif target.is_dir():
        skill_root = target.parent
    else:
        skill_root = target.parent

    all_findings: list[dict] = []
    for file_path in files:
        file_findings = find_positional_calls(file_path=file_path)
        annotate_findings_with_relative_path(
            findings=file_findings,
            file_path=file_path,
            skill_root=skill_root,
        )
        all_findings.extend(file_findings)

    print(json.dumps(all_findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
