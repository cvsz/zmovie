#!/usr/bin/env python3
"""Emit a release manifest describing exactly what would be deployed.

The manifest is the traceability record required by the release gate: it
pins the application commit, component versions, migration set, container
image digest, artifact checksums, timestamp and the rollback reference.

It is read-only with respect to the repository and prints JSON to stdout.
Use it locally or in CI; never commit its output.

    .venv/bin/python scripts/release-manifest.py --image zmovie:test
    .venv/bin/python scripts/release-manifest.py --checksums sha256sums.txt
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PLUGIN_HEADER_RE = re.compile(r"^\s*\*\s*Version:\s*(?P<version>\S+)", re.MULTILINE)
THEME_HEADER_RE = re.compile(r"^Version:\s*(?P<version>\S+)", re.MULTILINE)
LICENSE_VERSION_RE = re.compile(r'version\s*=\s*"(?P<version>[^"]+)"')
PYPROJECT_VERSION_RE = re.compile(r'^version\s*=\s*"(?P<version>[^"]+)"', re.MULTILINE)


def _run(*args: str) -> str:
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                              timeout=60, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _read(relative: str) -> str:
    path = ROOT / relative
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _plugin_version() -> str:
    match = PLUGIN_HEADER_RE.search(_read("wp-plugins/zwp-cinema/zwp-cinema.php"))
    return match.group("version") if match else "unknown"


def _theme_version() -> str:
    text = _read("themes/zwp-cinema/style.css")
    match = THEME_HEADER_RE.search(text)
    return match.group("version") if match else "unknown"


def _license_server_version() -> str:
    for name in ("services/license-server/server.py", "services/license-server/app.py"):
        match = LICENSE_VERSION_RE.search(_read(name))
        if match:
            return match.group("version")
    return "unknown"


def _cinema_api_version() -> str:
    for name in ("services/cinema-api/pyproject.toml", "services/cinema-api/app.py"):
        text = _read(name)
        match = PYPROJECT_VERSION_RE.search(text) or LICENSE_VERSION_RE.search(text)
        if match:
            return match.group("version")
    return "unknown"


def _migration_versions() -> list[str]:
    probe = (
        "import json,sys;from zmovie_platform import migrations;"
        "print(json.dumps(list(migrations.MIGRATION_VERSIONS)))"
    )
    raw = _run(sys.executable, "-c", probe)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return ["unknown"]


def _image_digest(image: str | None) -> str:
    if not image:
        return "not-supplied"
    out = _run("docker", "image", "inspect", image, "--format",
               "{{index .RepoDigests 0}}|{{.Id}}")
    if not out:
        return "unavailable"
    repo_digest, _, local_id = out.partition("|")
    return repo_digest or local_id or "unavailable"


def _checksums(path: Path | None) -> dict[str, str]:
    if not path or not path.is_file():
        return {}
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and len(parts[0]) == 64:
            entries[parts[1].lstrip("*").strip()] = parts[0]
    return entries


def build_manifest(image: str | None = None, checksums: Path | None = None) -> dict[str, object]:
    commit = _run("git", "rev-parse", "HEAD")
    return {
        "schema": "zmovie.release-manifest/v1",
        "generated_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "application": {
            "repository": _run("git", "config", "--get", "remote.origin.url"),
            "commit": commit,
            "branch": _run("git", "rev-parse", "--abbrev-ref", "HEAD"),
            "tree_clean": _run("git", "status", "--porcelain") == "",
        },
        "components": {
            "wordpress_plugin_zwp_cinema": _plugin_version(),
            "wordpress_theme_zwp_cinema": _theme_version(),
            "license_server": _license_server_version(),
            "cinema_api": _cinema_api_version(),
            "migrations": _migration_versions(),
        },
        "container": {"image": image or "not-supplied", "digest": _image_digest(image)},
        "artifact_checksums_sha256": _checksums(checksums),
        "rollback": {
            "application": f"git checkout {commit or '<previous-commit>'} && "
                           "sudo bash install.sh upgrade",
            "database": "restore the pre-deployment SQLite online backup "
                        "(docs/BACKUP_AND_RECOVERY.md)",
            "wordpress": "reinstall the previous plugin/theme tarball "
                         "(docs/production/ROLLBACK_EVIDENCE.md)",
        },
        "gates": {
            "live_payments": "blocked-pending-approval",
            "live_ticket_sales": "blocked-pending-approval",
            "public_auto_publish": "blocked-pending-approval",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=None, help="local image tag to digest")
    parser.add_argument("--checksums", type=Path, default=None, help="sha256sums file")
    parser.add_argument("--out", type=Path, default=None, help="optional output file")
    args = parser.parse_args(argv)
    manifest = build_manifest(args.image, args.checksums)
    text = json.dumps(manifest, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
