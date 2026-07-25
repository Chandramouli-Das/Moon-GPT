"use client";

import { FormEvent, useCallback, useState } from "react";
import {
  BarChart3,
  Download,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  MessageSquareText,
  RefreshCw,
  Search,
} from "lucide-react";
import styles from "./questions.module.css";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

type Question = {
  id: number;
  session_hash: string;
  question: string;
  answer: string;
  category: string;
  created_at: string;
};

type Summary = {
  total: number;
  today: number;
  categories: { category: string; count: number }[];
};

function authorization(username: string, password: string) {
  return `Basic ${btoa(`${username}:${password}`)}`;
}

export default function QuestionsAdminPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [credentials, setCredentials] = useState("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async (auth: string, selectedCategory = "") => {
    setLoading(true);
    setError("");
    try {
      const query = selectedCategory
        ? `?limit=500&category=${encodeURIComponent(selectedCategory)}`
        : "?limit=500";
      const [summaryResponse, questionsResponse] = await Promise.all([
        fetch(`${API_URL}/api/admin/questions/summary`, {
          headers: { Authorization: auth },
          cache: "no-store",
        }),
        fetch(`${API_URL}/api/admin/questions${query}`, {
          headers: { Authorization: auth },
          cache: "no-store",
        }),
      ]);
      if (!summaryResponse.ok || !questionsResponse.ok) {
        const payload = await summaryResponse.json().catch(() => ({}));
        throw new Error(payload.detail ?? "Could not access question analytics.");
      }
      setSummary(await summaryResponse.json());
      const payload = await questionsResponse.json();
      setQuestions(payload.questions);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Could not load analytics.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  function signIn(event: FormEvent) {
    event.preventDefault();
    const auth = authorization(username, password);
    setCredentials(auth);
    void loadData(auth);
  }

  async function exportCsv() {
    const response = await fetch(`${API_URL}/api/admin/questions/export`, {
      headers: { Authorization: credentials },
    });
    if (!response.ok) {
      setError("Could not export questions.");
      return;
    }
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "moongpt-questions.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!credentials || (error && !summary)) {
    return (
      <main className={styles.loginShell}>
        <form className={styles.loginCard} onSubmit={signIn}>
          <div className={styles.lock}><LockKeyhole size={24} /></div>
          <span className={styles.eyebrow}>MoonGPT private analytics</span>
          <h1>Question intelligence</h1>
          <p>Sign in to review anonymized questions visitors ask MoonGPT.</p>
          <label>
            Admin username
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label>
            Admin password
            <input
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error && <div className={styles.error}>{error}</div>}
          <button type="submit">
            {loading ? <LoaderCircle className={styles.spin} size={18} /> : <LockKeyhole size={18} />}
            Open dashboard
          </button>
        </form>
      </main>
    );
  }

  const visibleQuestions = questions.filter((item) =>
    item.question.toLowerCase().includes(search.toLowerCase()),
  );
  const topCategory = summary?.categories[0];

  return (
    <main className={styles.dashboard}>
      <header>
        <div>
          <span className={styles.eyebrow}>MoonGPT analytics</span>
          <h1>What visitors are asking</h1>
          <p>Privacy-safe question patterns from your portfolio assistant.</p>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.secondaryButton} onClick={() => void loadData(credentials, category)}>
            <RefreshCw size={17} /> Refresh
          </button>
          <button className={styles.primaryButton} onClick={() => void exportCsv()}>
            <Download size={17} /> Export CSV
          </button>
          <button
            aria-label="Sign out"
            className={styles.iconButton}
            onClick={() => {
              setCredentials("");
              setSummary(null);
              setPassword("");
            }}
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      <section className={styles.metrics}>
        <article><MessageSquareText /><span>Total questions</span><strong>{summary?.total ?? 0}</strong></article>
        <article><BarChart3 /><span>Questions today</span><strong>{summary?.today ?? 0}</strong></article>
        <article><Search /><span>Top topic</span><strong>{topCategory?.category ?? "—"}</strong><small>{topCategory ? `${topCategory.count} questions` : "No data yet"}</small></article>
      </section>

      <section className={styles.content}>
        <aside>
          <h2>Topics</h2>
          <button
            className={!category ? styles.activeTopic : ""}
            onClick={() => {
              setCategory("");
              void loadData(credentials);
            }}
          >
            All questions <span>{summary?.total ?? 0}</span>
          </button>
          {summary?.categories.map((item) => (
            <button
              className={category === item.category ? styles.activeTopic : ""}
              key={item.category}
              onClick={() => {
                setCategory(item.category);
                void loadData(credentials, item.category);
              }}
            >
              {item.category} <span>{item.count}</span>
            </button>
          ))}
        </aside>

        <div className={styles.questionPanel}>
          <div className={styles.panelHeader}>
            <div><h2>Recent questions</h2><p>{visibleQuestions.length} visible records</p></div>
            <label className={styles.searchBox}>
              <Search size={17} />
              <input
                placeholder="Search questions"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
          </div>
          {loading ? (
            <div className={styles.empty}><LoaderCircle className={styles.spin} /> Loading questions…</div>
          ) : visibleQuestions.length ? (
            <div className={styles.tableWrap}>
              <table>
                <thead><tr><th>Question</th><th>LLM answer</th><th>Topic</th><th>Asked</th></tr></thead>
                <tbody>
                  {visibleQuestions.map((item) => (
                    <tr key={item.id}>
                      <td>{item.question}</td>
                      <td className={styles.answerCell}>{item.answer || "—"}</td>
                      <td><span className={styles.category}>{item.category}</span></td>
                      <td>{new Date(item.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className={styles.empty}>No matching questions yet.</div>
          )}
          {error && <div className={styles.error}>{error}</div>}
        </div>
      </section>
    </main>
  );
}
