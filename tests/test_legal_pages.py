from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

import main


class LegalPagesTests(unittest.TestCase):
    def test_terms_pages_are_public_and_link_privacy_policy(self) -> None:
        client = TestClient(main.app)
        for path in ("/terms", "/terms-of-service"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("Terms of Service", response.text)
                self.assertIn('href="/privacy"', response.text)
                self.assertIn("sea@zeaz.dev", response.text)

    def test_privacy_pages_are_public_and_describe_data_controls(self) -> None:
        client = TestClient(main.app)
        for path in ("/privacy", "/privacy-policy"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("Privacy Policy", response.text)
                self.assertIn("/api/v2/privacy/export", response.text)
                self.assertIn("/api/v2/privacy/delete", response.text)
                self.assertIn("sea@zeaz.dev", response.text)


if __name__ == "__main__":
    unittest.main()
