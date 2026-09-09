import tempfile
import unittest
import importlib.util
from pathlib import Path


VERIFIER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_docs.py"
VERIFIER_SPEC = importlib.util.spec_from_file_location("zmovie_verify_docs", VERIFIER_PATH)
if VERIFIER_SPEC is None or VERIFIER_SPEC.loader is None:
    raise ImportError(f"Unable to load documentation verifier from {VERIFIER_PATH}")
verify_docs = importlib.util.module_from_spec(VERIFIER_SPEC)
VERIFIER_SPEC.loader.exec_module(verify_docs)


class DocumentationVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def make_valid_fixture(self) -> None:
        for relative in verify_docs.REQUIRED_FILES:
            if relative.endswith(".md"):
                content = f"# {Path(relative).stem.replace('_', ' ').title()}\n\nValid documentation.\n"
            elif relative.endswith(".yml"):
                content = "name: Example\ndescription: Example\nbody: []\n"
            elif relative.endswith("CODEOWNERS"):
                content = "* @cvsz\n"
            elif relative.endswith("dependabot.yml"):
                content = "version: 2\nupdates: []\n"
            else:
                content = "Copyright (c) 2026 cvsz\n"
            self.write(relative, content)

        self.write(
            "README.md",
            "# zMovie\n\nSee [documentation](docs/INDEX.md) and [i18n](docs/I18N.md).\n",
        )
        self.write(
            "docs/I18N.md",
            "# Internationalization\n\nBCP 47 locales: `en-US` and `th-TH`.\n",
        )
        canonical_links = "\n".join(
            f"[{Path(relative).stem}]({Path(relative).name})"
            for relative in verify_docs.CANONICAL_DOCS
        )
        self.write("docs/INDEX.md", f"# Documentation\n\n{canonical_links}\n")
        self.write("docs/linked.md", "# Linked\n")
        self.write("docs/FAQ.md", "# FAQ\n\nSee [linked](linked.md).\n")
        self.write(
            ".github/ISSUE_TEMPLATE/config.yml",
            "blank_issues_enabled: false\ncontact_links:\n  - name: Support\n    url: https://github.com/cvsz/zmovie/discussions\n    about: Ask for help\n",
        )
        self.write(
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            "name: Bug report\ndescription: Report a reproducible bug\nbody:\n  - type: textarea\n    attributes:\n      label: Reproduction\n",
        )
        self.write(
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            "name: Feature request\ndescription: Propose a scoped feature\nbody:\n  - type: textarea\n    attributes:\n      label: Problem\n",
        )
        self.write(
            ".github/dependabot.yml",
            "version: 2\nupdates:\n  - package-ecosystem: pip\n    directory: /\n    schedule:\n      interval: weekly\n",
        )

    def test_accepts_valid_documentation_fixture(self) -> None:
        self.make_valid_fixture()

        self.assertEqual(verify_docs.validate(self.root), [])

    def test_rejects_missing_required_file(self) -> None:
        self.make_valid_fixture()
        (self.root / "LICENSE").unlink()

        issues = verify_docs.validate(self.root)

        self.assertTrue(any("missing required file: LICENSE" in issue for issue in issues))

    def test_rejects_broken_relative_markdown_link(self) -> None:
        self.make_valid_fixture()
        self.write("docs/broken.md", "# Broken\n\n[missing](does-not-exist.md)\n")

        issues = verify_docs.validate(self.root)

        self.assertTrue(any("broken relative link" in issue for issue in issues))

    def test_rejects_invalid_locale_tag(self) -> None:
        self.make_valid_fixture()
        self.write("docs/I18N.md", "# Internationalization\n\nBCP 47 locale: `en_us`.\n")

        issues = verify_docs.validate(self.root)

        self.assertTrue(any("invalid locale tag" in issue for issue in issues))

    def test_rejects_secret_like_added_text(self) -> None:
        self.make_valid_fixture()
        self.write(
            "docs/unsafe.md",
            '# Unsafe\n\nAWS_SECRET_ACCESS_KEY="not-a-placeholder-secret-value"\n',
        )

        issues = verify_docs.validate(self.root)

        self.assertTrue(any("secret-like" in issue for issue in issues))

    def test_rejects_missing_heading(self) -> None:
        self.make_valid_fixture()
        self.write("docs/no-heading.md", "Documentation without a level-one heading.\n")

        issues = verify_docs.validate(self.root)

        self.assertTrue(any("missing level-one heading" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
