"use client";

import { useEffect, useState } from "react";
import { logsApi, QueryLog } from "@/lib/api";
import { clsx } from "clsx";
import { ChevronDown, ChevronUp } from "lucide-react";

export default function LogsPage() {
  const [logs, setLogs] = useState<QueryLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const PAGE_SIZE = 20;

  const load = async () => {
    const { data } = await logsApi.list(page, PAGE_SIZE, statusFilter || undefined);
    setLogs(data.items);
    setTotal(data.total);
  };

  useEffect(() => { load(); }, [page, statusFilter]);

  const statusColor = (s: string) => ({
    success: "bg-green-100 text-green-700",
    error: "bg-red-100 text-red-700",
    blocked: "bg-yellow-100 text-yellow-700",
  }[s] || "bg-gray-100 text-gray-600");

  return (
    <div className="p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Query Logs</h1>
        <p className="text-sm text-gray-500 mt-0.5">Full audit log of every query.</p>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        {["", "success", "error", "blocked"].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={clsx("text-xs px-3 py-1.5 rounded-full border", statusFilter === s ? "bg-sky-600 text-white border-sky-600" : "hover:bg-gray-50")}
          >
            {s || "All"}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-400 self-center">{total} total</span>
      </div>

      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b text-xs text-gray-500">
            <tr>
              <th className="px-4 py-3 text-left">Time</th>
              <th className="px-4 py-3 text-left">Question</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Rows</th>
              <th className="px-4 py-3 text-right">Latency</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <>
                <tr key={log.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate text-gray-800">{log.nl_query}</td>
                  <td className="px-4 py-3">
                    {log.query_type && (
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{log.query_type}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx("text-xs px-2 py-0.5 rounded", statusColor(log.status))}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-gray-500">{log.row_count ?? "—"}</td>
                  <td className="px-4 py-3 text-right text-xs text-gray-500">
                    {log.latency_ms ? `${log.latency_ms.toFixed(0)}ms` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {log.generated_sql && (
                      <button onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}>
                        {expandedId === log.id ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                    )}
                  </td>
                </tr>
                {expandedId === log.id && (
                  <tr key={`${log.id}-expanded`} className="bg-gray-50">
                    <td colSpan={7} className="px-4 py-3">
                      <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                        {log.generated_sql}
                      </pre>
                      {log.error_message && (
                        <p className="text-xs text-red-600 mt-2">{log.error_message}</p>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4 text-sm">
        <button
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
          className="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-gray-50"
        >
          Previous
        </button>
        <span className="text-gray-500">Page {page} of {Math.ceil(total / PAGE_SIZE)}</span>
        <button
          disabled={page >= Math.ceil(total / PAGE_SIZE)}
          onClick={() => setPage(page + 1)}
          className="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
