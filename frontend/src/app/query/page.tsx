"use client";

import { useState } from "react";
import { Send, Loader2, AlertCircle, Code2, ChevronDown, ChevronUp } from "lucide-react";
import { queryApi, QueryResponse, ErrorResponse } from "@/lib/api";
import { clsx } from "clsx";

interface Message {
  role: "user" | "assistant" | "error";
  content: string;
  data?: QueryResponse;
}

export default function QueryPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedSql, setExpandedSql] = useState<number | null>(null);

  const handleSubmit = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const { data } = await queryApi.run(question);
      if ("error" in data) {
        setMessages((prev) => [
          ...prev,
          { role: "error", content: (data as ErrorResponse).detail || data.error },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: (data as QueryResponse).result.nl_summary, data: data as QueryResponse },
        ]);
      }
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "error", content: e.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-white">
        <h1 className="text-lg font-semibold">Query</h1>
        <p className="text-sm text-gray-500">Ask any question in plain English</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-lg">Ask anything about your data</p>
            <p className="text-sm mt-1">e.g. "What were the top 5 products by revenue last month?"</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={clsx("max-w-3xl", msg.role === "user" ? "ml-auto" : "mr-auto")}
          >
            {/* Bubble */}
            <div
              className={clsx(
                "rounded-xl px-4 py-3 text-sm",
                msg.role === "user" && "bg-sky-600 text-white",
                msg.role === "assistant" && "bg-white border shadow-sm text-gray-800",
                msg.role === "error" && "bg-red-50 border border-red-200 text-red-700"
              )}
            >
              {msg.role === "error" && (
                <div className="flex items-center gap-2 mb-1 font-medium">
                  <AlertCircle className="w-4 h-4" /> Error
                </div>
              )}
              <p>{msg.content}</p>
            </div>

            {/* Result table + SQL */}
            {msg.data && (
              <div className="mt-2 space-y-2">
                {/* Stats bar */}
                <div className="flex items-center gap-4 text-xs text-gray-500 px-1">
                  <span>{msg.data.result.row_count} rows</span>
                  <span>{msg.data.latency_ms.toFixed(0)}ms</span>
                  <span className="bg-gray-100 rounded px-1.5 py-0.5">{msg.data.query_type}</span>
                </div>

                {/* Data table */}
                {msg.data.result.table.length > 0 && (
                  <div className="overflow-x-auto rounded-lg border bg-white text-xs">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          {msg.data.result.columns.map((col) => (
                            <th key={col} className="px-3 py-2 text-left font-medium text-gray-600">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.result.table.slice(0, 20).map((row, ri) => (
                          <tr key={ri} className="border-b last:border-0 hover:bg-gray-50">
                            {msg.data!.result.columns.map((col) => (
                              <td key={col} className="px-3 py-2 text-gray-700">
                                {String(row[col] ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* SQL toggle */}
                <button
                  onClick={() => setExpandedSql(expandedSql === i ? null : i)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 px-1"
                >
                  <Code2 className="w-3.5 h-3.5" />
                  View SQL
                  {expandedSql === i ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                </button>
                {expandedSql === i && (
                  <pre className="bg-gray-900 text-green-300 rounded-lg p-3 text-xs overflow-x-auto">
                    {msg.data.generated_sql}
                  </pre>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" /> Generating query…
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Ask a question about your data…"
            className="flex-1 border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            className="bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white rounded-lg px-4 py-2.5 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
