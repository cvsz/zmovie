from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SMBCloseoutScriptsTests(unittest.TestCase):
    def test_smb_closeout_is_fail_closed_and_checksum_verified(self):
        text = (ROOT / "scripts/runtime-closeout-smb.sh").read_text(encoding="utf-8")
        for marker in ("findmnt -T", "cifs|smb3", "sha256sum -c", "runtime-closeout.sh", "MIN_LOCAL_GB", 'rc=0', 'still BLOCKED'):
            self.assertIn(marker, text)

    def test_smb_installer_uses_credentials_file_and_automount(self):
        text = (ROOT / "scripts/install-smb-storage.sh").read_text(encoding="utf-8")
        self.assertIn("credentials=$CRED", text)
        self.assertIn("x-systemd.automount", text)
        self.assertNotIn("password=", text)

    def test_shell_syntax(self):
        scripts = [
            ROOT / "scripts/runtime-closeout-smb.sh",
            ROOT / "scripts/install-smb-storage.sh",
            ROOT / "scripts/smb-storage-doctor.sh",
        ]
        subprocess.run(["bash", "-n", *map(str, scripts)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
