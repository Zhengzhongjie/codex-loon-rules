#!/usr/bin/env python3
"""Check whether generated Loon rules still match reviewed upstream inputs."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

import build_loon_rules


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_DIR = REPO_ROOT / "rules"


def public_files(root: Path) -> dict[str, Path]:
    return {
        str(path.relative_to(root)): path
        for path in root.rglob("*")
        if path.is_file() and path.name != ".DS_Store" and "__pycache__" not in path.parts
    }


def unified_diff(current_text: str, rebuilt_text: str, rel_path: str) -> list[str]:
    return list(
        difflib.unified_diff(
            current_text.splitlines(keepends=True),
            rebuilt_text.splitlines(keepends=True),
            fromfile=f"current/{rel_path}",
            tofile=f"rebuilt/{rel_path}",
        )
    )


def report_tree(dialect, result, rules_dir: Path, diff: bool, max_diff_lines: int) -> int:
    """Diff one dialect's rebuilt tree against its committed tree. Returns 0 (match), 1 (missing), 2 (drift)."""
    generated_dir = (rules_dir / dialect.subdir / "generated").resolve()
    if not generated_dir.exists():
        print(f"FAIL: generated rule directory does not exist: {generated_dir}")
        return 1

    current_files = {name: path.read_text() for name, path in public_files(generated_dir).items()}
    rebuilt_files = build_loon_rules.render_tree(result.compiled, build_loon_rules.RULESETS, dialect)
    current_names = set(current_files)
    rebuilt_names = set(rebuilt_files)

    added = sorted(rebuilt_names - current_names)
    removed = sorted(current_names - rebuilt_names)
    changed = sorted(
        name for name in current_names & rebuilt_names if current_files[name] != rebuilt_files[name]
    )

    if not (added or removed or changed):
        print(f"OK: generated {dialect.subdir} rules match the current upstream snapshot")
        return 0

    print(f"DRIFT: generated {dialect.subdir} rules differ from the current upstream snapshot")
    if added:
        print("added: " + ", ".join(added))
    if removed:
        print("removed: " + ", ".join(removed))
    if changed:
        print("changed: " + ", ".join(changed))

    if diff:
        printed = 0
        for name in added + removed + changed:
            diff_lines = unified_diff(current_files.get(name, ""), rebuilt_files.get(name, ""), f"{dialect.subdir}/{name}")
            for line in diff_lines:
                if printed >= max_diff_lines:
                    print(f"... diff truncated after {max_diff_lines} lines")
                    return 2
                print(line, end="")
                printed += 1

    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild generated rules in memory and report upstream drift for every dialect."
    )
    parser.add_argument("--rules-dir", type=Path, default=DEFAULT_RULES_DIR)
    parser.add_argument("--diff", action="store_true", help="print a bounded unified diff for changed files")
    parser.add_argument("--max-diff-lines", type=int, default=300)
    args = parser.parse_args()

    contents, fetch_failures = build_loon_rules.fetch_all()
    result = build_loon_rules.compile_rules(build_loon_rules.RULESETS, contents)
    failures = fetch_failures + result.failures
    if failures:
        for failure in failures:
            print(f"FETCH_FAIL: {failure}")
        print("FAIL: cannot assess drift after upstream fetch or parse failures")
        return 1

    print("\n".join(build_loon_rules.stats_lines(result.stats)))

    rules_dir = args.rules_dir.resolve()
    exit_code = 0
    for dialect in build_loon_rules.DIALECTS:
        exit_code = max(exit_code, report_tree(dialect, result, rules_dir, args.diff, args.max_diff_lines))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
