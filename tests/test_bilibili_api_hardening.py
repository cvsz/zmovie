import unittest

from zmovie_platform.api_schemas import BilibiliPrepareRequest


class BilibiliApiHardeningTests(unittest.TestCase):
    def test_prepare_schema_exposes_no_server_filesystem_paths(self):
        fields = set(BilibiliPrepareRequest.model_fields)
        self.assertNotIn("video_path", fields)
        self.assertNotIn("cover_path", fields)
        self.assertNotIn("subtitle_path", fields)
        self.assertEqual(
            fields,
            {"title", "description", "tags", "playlist", "content_type", "schedule_at"},
        )


if __name__ == "__main__":
    unittest.main()
