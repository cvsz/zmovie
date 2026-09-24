import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SMBStorageDocsTests(unittest.TestCase):
    def test_smb_docs_keep_active_state_local(self):
        text = (ROOT / "docs/SMB_STORAGE.md").read_text(encoding="utf-8")
        self.assertIn("Never place the SQLite queue/database", text)
        self.assertIn("SHA-256", text)
        self.assertIn("cifs", text)

    def test_smb_layout_has_capacity_tiers(self):
        text = (ROOT / "docs/SMB_LAYOUT.md").read_text(encoding="utf-8")
        for name in ("source/", "videos/", "exports/", "archive/", "backups/", "evidence/"):
            self.assertIn(name, text)

    def test_reboot_not_claimed_as_automated(self):
        text = (ROOT / "docs/SMB_REBOOT.md").read_text(encoding="utf-8")
        self.assertIn("not yet been implemented", text)


if __name__ == "__main__":
    unittest.main()
