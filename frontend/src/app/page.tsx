"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryStats, type QueryResponse } from "@/lib/api";

const EXAMPLE_QUESTIONS = [
  "What is Shohei Ohtani's OPS this season?",
  "Who hit the most home runs in 2024?",
  "Show me the top 5 pitchers by ERA in 2025.",
  "What is Aaron Judge's career WAR?",
  "Who had the highest batting average in 2023?",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submitQuestion(q: string) {
    const trimmed = q.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await queryStats(trimmed);
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await submitQuestion(question);
  }

  function handleChipClick(q: string) {
    setQuestion(q);
    void submitQuestion(q);
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <div className="mx-auto max-w-3xl px-4 py-16">
        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            MLB StatBat
          </h1>
          <p className="mt-2 text-zinc-500 dark:text-zinc-400">
            Ask anything about MLB stats in plain language
          </p>
        </header>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What is Shohei Ohtani's OPS this season?"
            className="min-h-[48px] resize-none"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <Button type="submit" disabled={loading || !question.trim()}>
            {loading ? "..." : "Ask"}
          </Button>
        </form>

        <div className="mt-4 flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => handleChipClick(q)}
              disabled={loading}
              className="rounded-full border border-zinc-300 bg-white px-3 py-1 text-sm text-zinc-600 transition-colors hover:border-zinc-400 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-zinc-600 dark:hover:bg-zinc-800"
            >
              {q}
            </button>
          ))}
        </div>

        {error && (
          <Card className="mt-6 border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
            <CardContent className="pt-6 text-red-700 dark:text-red-400">
              {error}
            </CardContent>
          </Card>
        )}

        {loading && (
          <div className="mt-6 space-y-4">
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="h-4 w-3/4 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
                  <div className="h-4 w-1/2 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {response && !loading && (
          <div className="mt-6 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Answer</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-zinc-700 dark:text-zinc-300">
                  {response.answer}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-zinc-500">
                  Generated SQL
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="overflow-x-auto rounded bg-zinc-100 p-3 text-sm dark:bg-zinc-900">
                  <code>{response.sql}</code>
                </pre>
              </CardContent>
            </Card>

            {response.result.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-500">
                    Results
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          {Object.keys(response.result[0]).map((key) => (
                            <th
                              key={key}
                              className="px-3 py-2 text-left font-medium text-zinc-500"
                            >
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {response.result.map((row, i) => (
                          <tr key={i} className="border-b last:border-0">
                            {Object.values(row).map((val, j) => (
                              <td
                                key={j}
                                className="px-3 py-2 text-zinc-700 dark:text-zinc-300"
                              >
                                {String(val ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
