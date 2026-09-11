from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smb_docs_keep_active_state_local():
    text = (ROOT / "docs/SMB_STORAGE.md").read_text()
    assert "Never place the SQLite queue/database" in text
    assert "SHA-256" in text
    assert "cifs" in text


def test_smb_layout_has_capacity_tiers():
    text = (ROOT / "docs/SMB_LAYOUT.md").read_text()
    for name in ("source/", "videos/", "exports/", "archive/", "backups/", "evidence/"):
        assert name in text
