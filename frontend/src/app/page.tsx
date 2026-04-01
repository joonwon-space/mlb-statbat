"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryStats, type QueryResponse } from "@/lib/api";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await queryStats(question);
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
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

        {error && (
          <Card className="mt-6 border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
            <CardContent className="pt-6 text-red-700 dark:text-red-400">
              {error}
            </CardContent>
          </Card>
        )}

        {response && (
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
