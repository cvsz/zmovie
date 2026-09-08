import random
import unittest

import zmovie


class ZMovieTests(unittest.TestCase):
    def test_seeded_generation_is_deterministic(self):
        first = zmovie.generate(random.Random(42))
        second = zmovie.generate(random.Random(42))
        self.assertEqual(first, second)

    def test_generated_prompt_contains_full_timeline(self):
        item = zmovie.generate(random.Random(7))
        prompt = item["main_prompt"]
        for marker in (
            "[0:00–0:03]",
            "[0:03–0:06]",
            "[0:06–0:09]",
            "[0:09–0:12]",
            "[0:12–0:16]",
            "[0:16–0:18]",
            "[0:18–0:20]",
        ):
            self.assertIn(marker, prompt)

    def test_prompt_requires_one_continuous_shot(self):
        item = zmovie.generate(random.Random(1))
        prompt = item["main_prompt"].lower()
        self.assertIn("one uninterrupted shot", prompt)
        self.assertIn("no cuts", prompt)
        self.assertIn("continuity", prompt)

    def test_output_shape(self):
        item = zmovie.generate(random.Random(10))
        self.assertEqual(
            set(item),
            {
                "title",
                "main_prompt",
                "negative_prompt",
                "parameter_breakdown",
                "variation_ideas",
            },
        )
        self.assertEqual(len(item["variation_ideas"]), 3)
        self.assertIn("setting", item["parameter_breakdown"])
        self.assertIn("finisher", item["parameter_breakdown"])

    def test_cli_count_guard(self):
        with self.assertRaises(SystemExit):
            zmovie.parse_args(["--count", "0"])


if __name__ == "__main__":
    unittest.main()
