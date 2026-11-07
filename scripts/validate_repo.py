#!/usr/bin/env python3
"""Repository validation audit for zMovie.

Run by .github/workflows/automated-audit-review-approve.yml (policedbc).
Read-only checks only — never modifies files, never emits secrets.

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"ok: {msg}")


def check_no_tracked_secret_files() -> None:
    """Reject any secret-bearing file tracked by git (except .env.example)."""
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        fail("git ls-files failed")
        return

    secret_re = re.compile(
        r"(^|/)(\.env$|id_rsa|id_ed25519|.*\.pem|.*\.key)$"
    )
    tracked_secrets = [
        line
        for line in result.stdout.splitlines()
        if secret_re.search(line) and line != ".env.example"
    ]
    if tracked_secrets:
        for f in tracked_secrets:
            fail(f"Potential secret-bearing file is tracked: {f}")
    else:
        ok("No secret-bearing files tracked by git")


def check_workflow_yaml_valid() -> None:
    """Validate every GitHub Actions workflow YAML parses."""
    try:
        import yaml  # type: ignore
    except ImportError:
        fail("PyYAML is not installed — cannot validate workflow YAML")
        return

    workflow_dir = ROOT / ".github" / "workflows"
    if not workflow_dir.is_dir():
        fail(".github/workflows directory missing")
        return

    any_files = False
    for pattern in ("*.yml", "*.yaml"):
        for path in sorted(workflow_dir.glob(pattern)):
            any_files = True
            try:
                with path.open("r", encoding="utf-8") as fh:
                    yaml.safe_load(fh)
                ok(f"Valid YAML: {path.relative_to(ROOT)}")
            except Exception as exc:  # noqa: BLE001 - report any YAML error
                fail(f"Invalid YAML in {path.relative_to(ROOT)}: {exc}")
    if not any_files:
        fail("No workflow YAML files found in .github/workflows")


def check_required_files_exist() -> None:
    """Ensure canonical files the project and CI depend on are present."""
    required = [
        "README.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "SUPPORT.md",
        "LICENSE",
        "CHANGELOG.md",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        ".gitignore",
        "Makefile",
        "main.py",
        "app.py",
        "zmovie.py",
        "zmovie_platform/__init__.py",
        "docs/INDEX.md",
        "docs/STATUS.md",
        "docs/CONFIGURATION.md",
        "docs/ARCHITECTURE.md",
        "docs/OPERATIONS.md",
        "docs/TESTING.md",
        "docs/RELEASE.md",
        "docs/DOCUMENTATION_STANDARD.md",
        "docs/I18N.md",
        "docs/SECURITY.md" if (ROOT / "docs" / "SECURITY.md").exists() else "SECURITY.md",
        ".github/workflows/test.yml",
        ".github/pull_request_template.md",
        "scripts/verify_docs.py",
    ]
    missing = [r for r in required if not (ROOT / r).exists()]
    if missing:
        for m in missing:
            fail(f"Missing required file: {m}")
    else:
        ok("All required canonical files exist")


def check_validate_repo_exists() -> None:
    """The audit workflow itself depends on this script; it must exist."""
    if (ROOT / "scripts" / "validate_repo.py").exists():
        ok("scripts/validate_repo.py exists (self-reference satisfied)")
    else:
        fail("scripts/validate_repo.py is missing but referenced by CI workflow")


def check_docker_compose_loopback_default() -> None:
    """docker-compose.yml must bind to loopback by default (security hardening)."""
    compose = ROOT / "docker-compose.yml"
    if not compose.exists():
        fail("docker-compose.yml missing — cannot check bind host")
        return
    text = compose.read_text(encoding="utf-8")
    if 'ZMOVIE_HOST: "0.0.0.0"' in text or "ZMOVIE_HOST: 0.0.0.0" in text:
        fail("docker-compose.yml binds ZMOVIE_HOST to 0.0.0.0 (non-loopback); must default to 127.0.0.1")
    elif 'ZMOVIE_HOST: "127.0.0.1"' in text or "ZMOVIE_HOST: 127.0.0.1" in text:
        ok("docker-compose.yml defaults ZMOVIE_HOST to 127.0.0.1 (loopback)")
    else:
        fail("docker-compose.yml does not set ZMOVIE_HOST explicitly")


def check_env_example_has_zmovioe_secret_key() -> None:
    """The .env.example must document ZMOVIE_SECRET_KEY."""
    example = ROOT / ".env.example"
    if not example.exists():
        fail(".env.example missing")
        return
    text = example.read_text(encoding="utf-8")
    if "ZMOVIE_SECRET_KEY" in text:
        ok(".env.example documents ZMOVIE_SECRET_KEY")
    else:
        fail(".env.example missing ZMOVIE_SECRET_KEY documentation")


def check_no_active_secrets_in_tracked_files() -> None:
    """Scan tracked non-example files for placeholder-looking real secrets."""
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return

    secret_patterns = [
        re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
        re.compile(r"github_pat_[0-9a-zA-Z_]{20,}"),
        re.compile(r"ghp_[0-9a-zA-Z]{20,}"),
        re.compile(r"sk_live_[0-9a-zA-Z]{24,}"),
        re.compile(r"sk_test_[0-9a-zA-Z]{24,}"),
    ]
    scanned = 0
    for line in result.stdout.splitlines():
        path = ROOT / line
        if not path.is_file():
            continue
        if line == ".env.example":
            continue
        try:
            data = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeError):
            continue
        scanned += 1
        for pat in secret_patterns:
            if pat.search(data):
                fail(f"Possible active secret in tracked file: {line}")
    ok(f"Scanned {scanned} tracked files for active secrets")


def main() -> int:
    print("=== zMovie repository validation audit ===")
    print(f"Root: {ROOT}")
    print()

    check_no_tracked_secret_files()
    check_workflow_yaml_valid()
    check_required_files_exist()
    check_validate_repo_exists()
    check_docker_compose_loopback_default()
    check_env_example_has_zmovioe_secret_key()
    check_no_active_secrets_in_tracked_files()

    print()
    if FAILURES:
        print(f"=== AUDIT FAILED: {len(FAILURES)} issue(s) ===")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("=== AUDIT PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
