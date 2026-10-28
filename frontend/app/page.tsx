"use client";

import { useState } from "react";
import { ask, type AskResponse } from "../lib/api";

const EXAMPLES = ["改天我请你吃饭", "下定决心", "make vs do", "抱歉回复晚了"];

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(q: string) {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await ask(q.trim()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const cited = new Set(result?.answer.examples ?? []);

  return (
    <main className="wrap">
      <header>
        <h1>LingoRAG</h1>
        <p className="lede">想表达什么？用中文说，找到地道的英文 / 泰文说法和真实例句。</p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(query);
        }}
      >
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：改天我请你吃饭"
          rows={3}
          maxLength={500}
        />
        <div className="row">
          <div className="chips">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                className="chip"
                onClick={() => {
                  setQuery(ex);
                  submit(ex);
                }}
              >
                {ex}
              </button>
            ))}
          </div>
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? "查询中…" : "查询"}
          </button>
        </div>
      </form>

      {error && <p className="error">请求失败：{error}</p>}

      {result && (
        <section className="result">
          {!result.answer.grounded && (
            <p className="badge-ungrounded">AI 生成，无真实例句佐证，仅供参考</p>
          )}
          <p className="summary">{result.answer.summary}</p>
          {result.answer.explanation && (
            <p className="explanation">{result.answer.explanation}</p>
          )}
          <h2>例句</h2>
          {result.retrieved.length === 0 && (
            <p className="empty">知识库里没有找到足够相关的真实例句。</p>
          )}
          <ul className="examples">
            {result.retrieved.map((r) => (
              <li key={r.sentence_id} className={cited.has(r.sentence_id) ? "cited" : ""}>
                <span className="text">{r.text}</span>
                {r.translation && <span className="translation">{r.translation}</span>}
                <span className="meta">
                  #{r.sentence_id} · {r.lang} · {r.score.toFixed(2)}
                  {cited.has(r.sentence_id) && " · 已引用"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer>
        例句数据来自 <a href="https://tatoeba.org">Tatoeba</a>（CC BY 2.0 FR）。
      </footer>
    </main>
  );
}
