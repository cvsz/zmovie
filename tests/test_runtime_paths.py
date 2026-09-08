from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class RuntimePathTests(unittest.TestCase):
    def test_legacy_app_honors_production_database_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "var" / "lib" / "zmovie" / "zmovie.db"
            env = os.environ.copy()
            env["ZMOVIE_DB_PATH"] = str(db_path)
            env.pop("ZMOVIE_DATA_DIR", None)
            code = (
                "import app; "
                "app.init_db(); "
                "assert app.DB_PATH == __import__('pathlib').Path(r'%s').resolve(); "
                "assert app.DATA_DIR == app.DB_PATH.parent"
            ) % str(db_path)
            subprocess.run([sys.executable, "-c", code], env=env, check=True)
            self.assertTrue(db_path.is_file())
            self.assertFalse((Path.cwd() / "data" / "zmovie.db").exists())


if __name__ == "__main__":
    unittest.main()
