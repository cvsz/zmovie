from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class RuntimePathTests(unittest.TestCase):
    def test_legacy_app_honors_production_database_path(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "var" / "lib" / "zmovie" / "zmovie.db"
            env = os.environ.copy()
            env["ZMOVIE_DB_PATH"] = str(db_path)
            env.pop("ZMOVIE_DATA_DIR", None)
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
            code = (
                "import app; "
                "app.init_db(); "
                f"assert app.DB_PATH == __import__('pathlib').Path({str(db_path)!r}).resolve(); "
                "assert app.DATA_DIR == app.DB_PATH.parent"
            )
            subprocess.run([sys.executable, "-c", code], env=env, cwd=root, check=True)
            self.assertTrue(db_path.is_file())
            self.assertFalse((root / "data" / "zmovie.db").exists())


if __name__ == "__main__":
    unittest.main()
