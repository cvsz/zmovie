#!/usr/bin/env python3
"""Validate the repository documentation and GitHub community contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CHANGELOG.md",
    "docs/INDEX.md",
    "docs/ARCHITECTURE.md",
    "docs/API.md",
    "docs/CONFIGURATION.md",
    "docs/OPERATIONS.md",
    "docs/TROUBLESHOOTING.md",
    "docs/TESTING.md",
    "docs/RELEASE.md",
    "docs/STATUS.md",
    "docs/I18N.md",
    "docs/DOCUMENTATION_STANDARD.md",
    "docs/FAQ.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/dependabot.yml",
)

CANONICAL_DOCS = (
    "docs/ARCHITECTURE.md",
    "docs/API.md",
    "docs/CONFIGURATION.md",
    "docs/OPERATIONS.md",
    "docs/TROUBLESHOOTING.md",
    "docs/TESTING.md",
    "docs/RELEASE.md",
    "docs/STATUS.md",
    "docs/I18N.md",
    "docs/DOCUMENTATION_STANDARD.md",
    "docs/FAQ.md",
)

EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "data",
}

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\n]+)\)")
LEVEL_ONE_HEADING_RE = re.compile(r"^#\s+\S", re.MULTILINE)
INVALID_LOCALE_RE = re.compile(r"\b[a-z]{2,3}_[A-Za-z]{2,4}\b")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
TOKEN_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})\b"
)
ASSIGNED_SECRET_RE = re.compile(
    r"(?i)(?:\b(?:api[_-]?key|access[_-]?key|password|secret|token)\b|"
    r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_(?:secret|token|password|api[_-]?key)"
    r"(?:[_-][A-Z0-9]+)*)"
    r"\s*=\s*['\"]([^'\"]{8,})['\"]"
)
PRIVATE_PATH_RE = re.compile(r"(?<![\w])/(?:home|root|run)/[^\s)`'\"]+")
PLACEHOLDER_RE = re.compile(
    r"^(?:<[^>]+>|\$\{[^}]+\}|YOUR_[A-Z0-9_]+|REDACTED|"
    r"REPLACE_ME|EXAMPLE(?:_[A-Z0-9_]+)?)$"
)


def _relative_files(root: Path, suffix: str | None = None) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if suffix is None or path.name.endswith(suffix):
            files.append(path)
    return sorted(files)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    return target.strip()


def _is_external(target: str) -> bool:
    return target.startswith("#") or target.startswith("//") or bool(urlsplit(target).scheme)


def _check_required_files(root: Path) -> list[str]:
    return [f"missing required file: {relative}" for relative in REQUIRED_FILES if not (root / relative).is_file()]


def _check_headings(root: Path) -> list[str]:
    issues = []
    for path in _relative_files(root, ".md"):
        if not LEVEL_ONE_HEADING_RE.search(_read(path)):
            issues.append(f"{_relative(path, root)}: missing level-one heading")
    return issues


def _check_links(root: Path) -> list[str]:
    issues = []
    for path in _relative_files(root, ".md"):
        for match in MARKDOWN_LINK_RE.finditer(_read(path)):
            target = _link_target(match.group(1))
            if not target or _is_external(target):
                continue
            target_path = unquote(urlsplit(target).path)
            if not target_path:
                continue
            candidate = (path.parent / target_path).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                issues.append(f"{_relative(path, root)}: relative link escapes repository: {target}")
                continue
            if not candidate.exists():
                issues.append(f"{_relative(path, root)}: broken relative link: {target}")
    return issues


def _check_locale_contract(root: Path) -> list[str]:
    issues = []
    path = root / "docs/I18N.md"
    if not path.is_file():
        return issues
    text = _read(path)
    if "BCP 47" not in text:
        issues.append("docs/I18N.md: missing BCP 47 locale contract")
    for required in ("en-US", "th-TH"):
        if required not in text:
            issues.append(f"docs/I18N.md: missing required locale example: {required}")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\b(?:locale|language|lang)\b", line, re.IGNORECASE):
            if INVALID_LOCALE_RE.search(line):
                issues.append(f"docs/I18N.md:{line_number}: invalid locale tag; use BCP 47 hyphen casing")
    return issues


def _check_secret_and_path_hygiene(root: Path) -> list[str]:
    issues = []
    for path in _relative_files(root, ".md"):
        text = _read(path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PRIVATE_KEY_RE.search(line) or TOKEN_RE.search(line):
                issues.append(f"{_relative(path, root)}:{line_number}: secret-like credential material")
            assignment = ASSIGNED_SECRET_RE.search(line)
            if assignment and not PLACEHOLDER_RE.fullmatch(assignment.group(1).strip()):
                issues.append(f"{_relative(path, root)}:{line_number}: secret-like assignment")
            if PRIVATE_PATH_RE.search(line):
                issues.append(f"{_relative(path, root)}:{line_number}: private machine path")
    return issues


def _check_github_contract(root: Path) -> list[str]:
    issues = []

    readme = root / "README.md"
    if readme.is_file() and "docs/INDEX.md" not in _read(readme):
        issues.append("README.md: missing link to docs/INDEX.md")

    index = root / "docs/INDEX.md"
    if index.is_file():
        index_text = _read(index)
        for relative in CANONICAL_DOCS:
            if relative not in index_text and relative.removeprefix("docs/") not in index_text:
                issues.append(f"docs/INDEX.md: missing canonical guide link: {relative}")

    owners = root / ".github/CODEOWNERS"
    if owners.is_file() and "@cvsz" not in _read(owners):
        issues.append(".github/CODEOWNERS: missing @cvsz owner")

    issue_form_contracts = {
        ".github/ISSUE_TEMPLATE/bug_report.yml": ("name:", "description:", "body:"),
        ".github/ISSUE_TEMPLATE/feature_request.yml": ("name:", "description:", "body:"),
        ".github/ISSUE_TEMPLATE/config.yml": ("blank_issues_enabled:", "contact_links:"),
        ".github/dependabot.yml": ("version: 2", "updates:"),
    }
    for relative, required in issue_form_contracts.items():
        path = root / relative
        if not path.is_file():
            continue
        text = _read(path)
        for token in required:
            if token not in text:
                issues.append(f"{relative}: missing required YAML contract: {token}")
    return issues


def validate(root: Path) -> list[str]:
    """Return repository-relative documentation contract failures."""

    root = root.resolve()
    issues = []
    issues.extend(_check_required_files(root))
    issues.extend(_check_headings(root))
    issues.extend(_check_links(root))
    issues.extend(_check_locale_contract(root))
    issues.extend(_check_secret_and_path_hygiene(root))
    issues.extend(_check_github_contract(root))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root to validate (default: current directory)",
    )
    args = parser.parse_args(argv)
    issues = validate(args.root)
    if issues:
        print("Documentation verification failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    count = len(_relative_files(args.root.resolve(), ".md"))
    print(f"Documentation verification passed: {count} Markdown files checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
