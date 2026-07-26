from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np

from backend.rag import RAGEngine, build_retrieval_query, load_structured_docx, tokenize


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "Document.docx"


def deterministic_embedder(texts: list[str], dimensions: int = 384) -> np.ndarray:
    matrix = np.zeros((len(texts), dimensions), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode()).digest()
            position = int.from_bytes(digest[:4], "big") % dimensions
            matrix[row, position] += 1
    return matrix


class StructuredDocumentTests(unittest.TestCase):
    def test_docx_is_split_on_real_sections(self) -> None:
        chunks = load_structured_docx(DOCUMENT)
        labels = {chunk.label for chunk in chunks}
        self.assertGreater(len(chunks), 20)
        self.assertTrue(any("Professional Experience" in label for label in labels))
        self.assertTrue(any("Recruiter FAQ" in label for label in labels))
        self.assertTrue(all(len(chunk.text.split()) <= 220 for chunk in chunks))

    def test_follow_up_query_includes_previous_topic(self) -> None:
        conversation = [
            ("user", "Tell me about his availability"),
            ("assistant", "He is based in Bangalore."),
            ("user", "What about his notice period?"),
        ]
        query = build_retrieval_query(
            "What about his notice period?", conversation
        )
        self.assertIn("availability", query)
        self.assertIn("notice period", query)


class HybridRetrievalTests(unittest.TestCase):
    def test_notice_period_query_returns_recruiter_information(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine = RAGEngine(
                document_path=DOCUMENT,
                embedding_model="test-embedding",
                embedder=deterministic_embedder,
                cache_dir=Path(temporary_directory),
            )
            results = engine.search(
                "What is his notice period and how quickly can he join?", count=5
            )
            combined = " ".join(result.chunk.text.lower() for result in results)
            self.assertIn("60 days", combined)
            self.assertIn("30 days", combined)

    def test_phone_query_returns_verified_contact_information(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine = RAGEngine(
                document_path=DOCUMENT,
                embedding_model="test-embedding",
                embedder=deterministic_embedder,
                cache_dir=Path(temporary_directory),
            )
            results = engine.search("What is his phone number?", count=5)
            combined = " ".join(result.chunk.text.lower() for result in results)
            self.assertIn("9674078742", combined.replace(" ", ""))
            self.assertEqual(
                results[0].chunk.section,
                "Contact & Professional Links",
            )

    def test_phone_follow_up_keeps_contact_context(self) -> None:
        conversation = [
            ("user", "What is his phone number?"),
            ("assistant", "It is not specified."),
            ("user", "It is present, take another look."),
        ]
        query = build_retrieval_query(conversation[-1][1], conversation)
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine = RAGEngine(
                DOCUMENT,
                "test-embedding",
                deterministic_embedder,
                Path(temporary_directory),
            )
            results = engine.search(query, count=5)
            combined = " ".join(result.chunk.text for result in results)
            self.assertIn("9674078742", combined.replace(" ", ""))

    def test_index_is_reused_from_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache = Path(temporary_directory)
            first = RAGEngine(
                DOCUMENT, "test-embedding", deterministic_embedder, cache
            )
            first.ensure_ready()
            second = RAGEngine(
                DOCUMENT, "test-embedding", deterministic_embedder, cache
            )
            second.ensure_ready()
            self.assertTrue(second.loaded_from_cache)
            self.assertEqual(first.chunk_count, second.chunk_count)

    def test_generic_work_query_prioritizes_corporate_experience(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine = RAGEngine(
                DOCUMENT,
                "test-embedding",
                deterministic_embedder,
                Path(temporary_directory),
            )
            results = engine.search("Tell me about his work and projects", count=5)
            sections = [result.chunk.section for result in results]
            self.assertIn("Professional Experience", sections[:3])
            self.assertNotEqual(sections[0], "Personal AI & Data Projects")


if __name__ == "__main__":
    unittest.main()
