from __future__ import annotations

import csv
import hashlib
import io
import logging
import queue
import re
import sqlite3
import threading
from collections import Counter, deque
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
SENSITIVE_INTAKE_PATTERN = re.compile(
    r"\b(your name|your position|company|your email|your phone|hiring for|"
    r"job location|work arrangement|opportunity details|sender email|"
    r"sender phone|email password)\s*:",
    re.IGNORECASE,
)
WORD_PATTERN = re.compile(r"[a-z0-9+#.]+")
logger = logging.getLogger(__name__)


def redact_question(text: str) -> str:
    text = EMAIL_PATTERN.sub("[email redacted]", text)
    text = PHONE_PATTERN.sub("[phone redacted]", text)
    return re.sub(r"\s+", " ", text).strip()[:2_000]


def categorize_question(text: str) -> str:
    lowered = text.lower()
    categories = (
        ("email", ("email", "mail", "contact", "reach out")),
        ("availability", ("notice period", "join", "availability", "relocat")),
        ("leadership", ("leadership", "team", "mentor", "manage")),
        ("projects", ("project", "built", "architecture", "production")),
        ("experience", ("experience", "work", "career", "company", "role")),
        ("skills", ("skill", "technology", "stack", "python", "rag", "genai")),
        ("education", ("education", "degree", "college", "university", "certif")),
        ("personal", ("personal", "hobby", "interest")),
    )
    for category, terms in categories:
        if any(term in lowered for term in terms):
            return category
    return "general"


def _tokens(text: str) -> set[str]:
    return {token for token in WORD_PATTERN.findall(text.lower()) if len(token) > 2}


@dataclass(frozen=True)
class QuestionEvent:
    session_hash: str
    question: str
    answer: str
    category: str
    created_at: str


class QuestionAnalytics:
    """Non-blocking question logging with an in-memory FAQ hint cache."""

    def __init__(self, database_path: Path, retention_days: int = 90) -> None:
        self.database_path = database_path
        self.retention_days = max(retention_days, 1)
        self._queue: queue.Queue[QuestionEvent | None] = queue.Queue(maxsize=2_000)
        self._recent: deque[str] = deque(maxlen=500)
        self._counts: Counter[str] = Counter()
        self._memory_lock = threading.Lock()
        self._initialize()
        self._worker = threading.Thread(
            target=self._write_loop, name="question-analytics", daemon=True
        )
        self._worker.start()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_hash TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(questions)")
            }
            if "answer" not in columns:
                connection.execute(
                    "ALTER TABLE questions ADD COLUMN answer TEXT NOT NULL DEFAULT ''"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_questions_created_at "
                "ON questions(created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_questions_category "
                "ON questions(category)"
            )
            cutoff = (datetime.now(UTC) - timedelta(days=self.retention_days)).isoformat()
            connection.execute("DELETE FROM questions WHERE created_at < ?", (cutoff,))
            rows = connection.execute(
                "SELECT question FROM questions ORDER BY id DESC LIMIT 500"
            ).fetchall()
        for row in reversed(rows):
            self._remember(row["question"])

    def _remember(self, question: str) -> None:
        normalized = question.casefold()
        with self._memory_lock:
            self._recent.append(question)
            self._counts[normalized] += 1

    def record(self, session_id: str, question: str, answer: str) -> bool:
        if SENSITIVE_INTAKE_PATTERN.search(question):
            return False
        redacted = redact_question(question)
        if len(redacted) < 8 or redacted.lower() in {
            "ok send it", "send it", "cancel", "cancel email"
        }:
            return False
        event = QuestionEvent(
            session_hash=hashlib.sha256(session_id.encode()).hexdigest()[:20],
            question=redacted,
            answer=redact_question(answer)[:8_000],
            category=categorize_question(redacted),
            created_at=datetime.now(UTC).isoformat(),
        )
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            return False
        self._remember(redacted)
        return True

    def _write_loop(self) -> None:
        while True:
            event = self._queue.get()
            if event is None:
                self._queue.task_done()
                return
            try:
                with closing(self._connect()) as connection, connection:
                    connection.execute(
                        """
                        INSERT INTO questions
                            (session_hash, question, answer, category, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            event.session_hash,
                            event.question,
                            event.answer,
                            event.category,
                            event.created_at,
                        ),
                    )
            except sqlite3.Error:
                logger.exception("Could not persist an anonymized question event.")
            finally:
                self._queue.task_done()

    def related_popular_questions(self, query: str, limit: int = 3) -> list[str]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []
        with self._memory_lock:
            unique = list(dict.fromkeys(reversed(self._recent)))
            counts = self._counts.copy()
        candidates = []
        for question in unique:
            if question.casefold() == query.casefold():
                continue
            overlap = len(query_tokens & _tokens(question))
            frequency = counts[question.casefold()]
            if overlap and frequency >= 2:
                candidates.append((overlap * 2 + min(frequency, 5), question))
        candidates.sort(reverse=True)
        return [question for _, question in candidates[:limit]]

    def summary(self) -> dict:
        with closing(self._connect()) as connection, connection:
            total = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
            today = datetime.now(UTC).date().isoformat()
            today_count = connection.execute(
                "SELECT COUNT(*) FROM questions WHERE created_at >= ?", (today,)
            ).fetchone()[0]
            categories = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT category, COUNT(*) AS count
                    FROM questions
                    GROUP BY category
                    ORDER BY count DESC, category
                    """
                )
            ]
        return {"total": total, "today": today_count, "categories": categories}

    def list_questions(
        self, limit: int = 100, offset: int = 0, category: str | None = None
    ) -> list[dict]:
        query = (
            "SELECT id, session_hash, question, answer, category, created_at "
            "FROM questions"
        )
        parameters: list[object] = []
        if category:
            query += " WHERE category = ?"
            parameters.append(category)
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        parameters.extend((min(max(limit, 1), 500), max(offset, 0)))
        with closing(self._connect()) as connection, connection:
            return [dict(row) for row in connection.execute(query, parameters)]

    def export_csv(self) -> str:
        rows = self.list_questions(limit=500)
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=(
                "id",
                "session_hash",
                "question",
                "answer",
                "category",
                "created_at",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def flush(self) -> None:
        self._queue.join()
