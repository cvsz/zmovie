from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smb_closeout_is_fail_closed_and_checksum_verified():
    text = (ROOT / "scripts/runtime-closeout-smb.sh").read_text()
    assert "findmnt -T" in text
    assert "cifs|smb3" in text
    assert "sha256sum -c" in text
    assert "runtime-closeout.sh" in text
    assert "MIN_LOCAL_GB" in text


def test_smb_installer_uses_credentials_file_and_automount():
    text = (ROOT / "scripts/install-smb-storage.sh").read_text()
    assert "credentials=$CRED" in text
    assert "x-systemd.automount" in text
    assert "password=" not in text
