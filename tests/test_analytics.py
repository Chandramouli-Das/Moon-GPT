from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.analytics import QuestionAnalytics, categorize_question, redact_question


class QuestionAnalyticsTests(unittest.TestCase):
    def test_redacts_email_and_phone(self) -> None:
        cleaned = redact_question(
            "Contact me at recruiter@example.com or +91 98765 43210 about his work"
        )
        self.assertNotIn("recruiter@example.com", cleaned)
        self.assertNotIn("98765", cleaned)
        self.assertIn("[email redacted]", cleaned)
        self.assertIn("[phone redacted]", cleaned)

    def test_classifies_common_topics(self) -> None:
        self.assertEqual(categorize_question("What is his notice period?"), "availability")
        self.assertEqual(categorize_question("Which projects has he built?"), "projects")

    def test_records_in_background_and_returns_popular_hints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analytics = QuestionAnalytics(Path(directory) / "questions.db")
            analytics.record("session-one", "What projects has he built?", "Answer one")
            analytics.record("session-two", "What projects has he built?", "Answer two")
            analytics.record(
                "session-three", "Tell me about his project experience", "Answer three"
            )
            analytics.flush()
            self.assertEqual(analytics.summary()["total"], 3)
            hints = analytics.related_popular_questions(
                "Could you describe his projects?"
            )
            self.assertIn("What projects has he built?", hints)
            row = analytics.list_questions(limit=1)[0]
            self.assertNotEqual(row["session_hash"], "session-three")
            self.assertEqual(row["answer"], "Answer three")

    def test_skips_structured_email_intake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analytics = QuestionAnalytics(Path(directory) / "questions.db")
            saved = analytics.record(
                "session-private",
                "Your email: recruiter@example.com Your phone: +91 9876543210",
                "Private response",
            )
            analytics.flush()
            self.assertFalse(saved)
            self.assertEqual(analytics.summary()["total"], 0)


if __name__ == "__main__":
    unittest.main()
