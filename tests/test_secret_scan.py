"""Regression tests for scripts/secret-scan.sh.

The scanner must be PEM-structure aware: documentation prose that merely
names a marker type passes, while realistic key blocks fail. All fixtures
use synthetic obviously-fake data in disposable temp repos; nothing here is
a real secret and no fixture is ever committed.

NOTE for future editors: never write a contiguous literal such as
'-----BEGIN ... PRIVATE KEY-----' or the previously exposed credential
pattern in this file, or the committed scanner itself would flag it.
Markers below are assembled from fragments for exactly this reason.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "secret-scan.sh"

# Fragments keep full marker patterns out of this tracked source file.
PEM_BEGIN = "-----BEGIN " + "PRIVATE KEY-----"
PEM_END = "-----END " + "PRIVATE KEY-----"
RSA_BEGIN = "-----BEGIN RSA " + "PRIVATE KEY-----"
RSA_END = "-----END RSA " + "PRIVATE KEY-----"
EC_BEGIN = "-----BEGIN EC " + "PRIVATE KEY-----"
EC_END = "-----END EC " + "PRIVATE KEY-----"
SSH_BEGIN = "-----BEGIN OPENSSH " + "PRIVATE KEY-----"
SSH_END = "-----END OPENSSH " + "PRIVATE KEY-----"
# Synthetic base64-looking body (decodes to repeated "FAKE-TEST-KEY-DATA").
FAKE_BODY = "RkFLRS1URVNULUtFWS1EQVRBLUZBS0UtVEVTVC1LRVktREFUQQ=="
EXPOSED_PATTERN = "zeaz-cinema-" + "2026-testprobe" + "-rotated"
PASSWORD_FLAG = "--password=" + "test-only-fake"


def run_scan(files: dict[str, str]) -> int:
    """Stage given files in a throwaway repo and return scanner exit code."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, timeout=60)
        for name, content in files.items():
            path = Path(tmp) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=tmp, check=True, timeout=60)
        proc = subprocess.run(["bash", str(SCRIPT)], cwd=tmp, capture_output=True,
                              text=True, timeout=120, check=False)
        return proc.returncode


def fake_pem(begin: str = PEM_BEGIN, end: str = PEM_END) -> str:
    return f"{begin}\n{FAKE_BODY}\n{end}\n"


class SecretScanTests(unittest.TestCase):
    def test_prose_mention_passes(self) -> None:
        """Documentation phrase without dashes/body/closing marker passes."""
        files = {"docs/example.md": "# Doc\n\nScans `BEGIN PRIVATE KEY`, passwords and env files.\n"}
        self.assertEqual(run_scan(files), 0)

    def test_fake_pem_block_fails(self) -> None:
        self.assertNotEqual(run_scan({"keys/fake.pem": fake_pem()}), 0)

    def test_rsa_block_fails(self) -> None:
        self.assertNotEqual(run_scan({"keys/fake-rsa.pem": fake_pem(RSA_BEGIN, RSA_END)}), 0)

    def test_ec_block_fails(self) -> None:
        self.assertNotEqual(run_scan({"keys/fake-ec.pem": fake_pem(EC_BEGIN, EC_END)}), 0)

    def test_openssh_block_fails(self) -> None:
        self.assertNotEqual(run_scan({"keys/fake-ssh.pem": fake_pem(SSH_BEGIN, SSH_END)}), 0)

    def test_incomplete_block_passes(self) -> None:
        """Opening marker alone (no body, no closing marker) is not a key."""
        files = {"docs/note.md": f"# Note\n\nExample marker: `{PEM_BEGIN}` without body.\n"}
        self.assertEqual(run_scan(files), 0)

    def test_exposed_pattern_fails(self) -> None:
        files = {"docs/leak.md": f"# Leak\n\nOld value {EXPOSED_PATTERN} here.\n"}
        self.assertNotEqual(run_scan(files), 0)

    def test_password_flag_fails(self) -> None:
        files = {"scripts/deploy.sh": f"#!/usr/bin/env bash\nmysql {PASSWORD_FLAG}secret\n"}
        self.assertNotEqual(run_scan(files), 0)

    def test_tracked_env_fails(self) -> None:
        self.assertNotEqual(run_scan({"svc/.env.test": "X=1\n"}), 0)

    def test_env_example_passes(self) -> None:
        self.assertEqual(run_scan({"svc/.env.example": "X=\n"}), 0)

    def test_current_tree_passes(self) -> None:
        """The real repository tree (with the docs prose) must scan clean."""
        proc = subprocess.run(["bash", str(SCRIPT)], cwd=SCRIPT.parents[1],
                              capture_output=True, text=True, timeout=120, check=False)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
