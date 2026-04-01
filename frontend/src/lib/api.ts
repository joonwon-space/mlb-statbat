const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface QueryResponse {
  question: string;
  sql: string;
  result: Record<string, unknown>[];
  answer: string;
}

export async function queryStats(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }

  return res.json();
}
