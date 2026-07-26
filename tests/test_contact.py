from __future__ import annotations

import unittest
from pathlib import Path

from backend.contact import extract_verified_phone, is_phone_request


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "Document.docx"


class ContactTests(unittest.TestCase):
    def test_extracts_verified_phone_from_document(self) -> None:
        self.assertEqual(extract_verified_phone(DOCUMENT), "+91 9674078742")

    def test_recognizes_direct_phone_question(self) -> None:
        self.assertTrue(is_phone_request("What is his phone number?"))

    def test_recognizes_phone_follow_up(self) -> None:
        conversation = [
            ("user", "What is his phone number?"),
            ("assistant", "It is not specified."),
            ("user", "It is present, take a good look."),
        ]
        self.assertTrue(
            is_phone_request("It is present, take a good look.", conversation)
        )

    def test_does_not_treat_unrelated_follow_up_as_phone_request(self) -> None:
        conversation = [
            ("user", "Tell me about his projects."),
            ("assistant", "He has several corporate projects."),
        ]
        self.assertFalse(is_phone_request("Check again.", conversation))


if __name__ == "__main__":
    unittest.main()
