// Mirrors shared/schemas.py. Keep the two in sync (change both in one PR).

export type RetrievedItem = {
  sentence_id: number;
  lang: "en" | "zh" | "th";
  text: string;
  translation: string | null;
  score: number;
};

export type Answer = {
  summary: string;
  explanation: string;
  examples: number[];
  // false = no real example supports this answer; must be shown as AI-generated.
  grounded: boolean;
};

export type AskResponse = {
  answer: Answer;
  retrieved: RetrievedItem[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function ask(query: string, userId = "anonymous"): Promise<AskResponse> {
  const res = await fetch(`${API_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, user_id: userId, channel: "web", top_k: 5 }),
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json();
}
