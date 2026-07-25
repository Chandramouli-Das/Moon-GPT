from __future__ import annotations

import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from main import clean_visible_answer


class ResponseCleaningTests(unittest.TestCase):
    def test_removes_single_and_grouped_source_markers(self) -> None:
        answer = (
            "He has 7+ years of experience. [S4][S5]\n\n"
            "- He led a team of 10+. [S2]\n"
            "- He is based in Bangalore.[S1]"
        )
        cleaned = clean_visible_answer(answer)
        self.assertNotRegex(cleaned, r"\[S\d+\]")
        self.assertIn("7+ years", cleaned)
        self.assertIn("Bangalore.", cleaned)

    def test_removes_trailing_sources_section(self) -> None:
        answer = (
            "Chandramouli is a Lead Data Scientist.\n\n"
            "### Sources\n"
            "- S1: Professional Profile\n"
            "- S2: Professional Experience"
        )
        self.assertEqual(
            clean_visible_answer(answer),
            "Chandramouli is a Lead Data Scientist.",
        )


if __name__ == "__main__":
    unittest.main()
