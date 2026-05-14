"use client";

import { useEffect, useState } from "react";
import { examplesApi, FewShotExample } from "@/lib/api";
import { Plus, Trash2, Pencil, RefreshCw, Database } from "lucide-react";
import { clsx } from "clsx";

const QUERY_TYPES = ["SELECT_SIMPLE", "SELECT_AGGREGATE", "SELECT_JOIN", "SELECT_TEMPORAL"];

const EMPTY_FORM = { question: "", sql: "", query_type: "SELECT_SIMPLE" };

export default function ExamplesPage() {
  const [examples, setExamples] = useState<FewShotExample[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [syncing, setSyncing] = useState(false);

  const load = async () => {
    const { data } = await examplesApi.list(filter || undefined);
    setExamples(data);
  };

  useEffect(() => { load(); }, [filter]);

  const handleSave = async () => {
    if (editId) {
      await examplesApi.update(editId, form);
    } else {
      await examplesApi.create(form);
    }
    setShowForm(false);
    setEditId(null);
    setForm(EMPTY_FORM);
    load();
  };

  const handleEdit = (ex: FewShotExample) => {
    setEditId(ex.id);
    setForm({ question: ex.question, sql: ex.sql, query_type: ex.query_type });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this example?")) return;
    await examplesApi.delete(id);
    load();
  };

  const handleSync = async () => {
    setSyncing(true);
    await examplesApi.syncEmbeddings();
    setSyncing(false);
  };

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Examples Manager</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Curate few-shot (question → SQL) pairs for prompting.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-1.5 text-sm border rounded-lg px-3 py-2 hover:bg-gray-50 disabled:opacity-50"
          >
            <Database className="w-4 h-4" />
            {syncing ? "Syncing…" : "Sync Embeddings"}
          </button>
          <button
            onClick={() => { setShowForm(true); setEditId(null); setForm(EMPTY_FORM); }}
            className="flex items-center gap-1.5 text-sm bg-sky-600 text-white rounded-lg px-3 py-2 hover:bg-sky-700"
          >
            <Plus className="w-4 h-4" /> Add Example
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setFilter("")}
          className={clsx("text-xs px-3 py-1.5 rounded-full border", !filter ? "bg-sky-600 text-white border-sky-600" : "hover:bg-gray-50")}
        >
          All ({examples.length})
        </button>
        {QUERY_TYPES.map((qt) => (
          <button
            key={qt}
            onClick={() => setFilter(qt)}
            className={clsx("text-xs px-3 py-1.5 rounded-full border", filter === qt ? "bg-sky-600 text-white border-sky-600" : "hover:bg-gray-50")}
          >
            {qt}
          </button>
        ))}
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white border rounded-xl p-4 mb-4 shadow-sm">
          <h3 className="font-medium text-sm mb-3">{editId ? "Edit Example" : "New Example"}</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Question</label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm"
                value={form.question}
                onChange={(e) => setForm({ ...form, question: e.target.value })}
                placeholder="What were the top 5 products by revenue last month?"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">SQL</label>
              <textarea
                className="w-full border rounded-lg px-3 py-2 text-sm font-mono h-24 resize-none"
                value={form.sql}
                onChange={(e) => setForm({ ...form, sql: e.target.value })}
                placeholder="SELECT p.name, SUM(oi.line_total) as revenue FROM ..."
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Query Type</label>
              <select
                className="border rounded-lg px-3 py-2 text-sm"
                value={form.query_type}
                onChange={(e) => setForm({ ...form, query_type: e.target.value })}
              >
                {QUERY_TYPES.map((qt) => <option key={qt} value={qt}>{qt}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <button onClick={handleSave} className="bg-sky-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-sky-700">
              Save
            </button>
            <button onClick={() => setShowForm(false)} className="text-sm px-4 py-2 rounded-lg border hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* List */}
      <div className="space-y-2">
        {examples.map((ex) => (
          <div key={ex.id} className="bg-white border rounded-xl p-4 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 mb-1">{ex.question}</p>
                <pre className="text-xs font-mono text-gray-500 bg-gray-50 rounded p-2 overflow-x-auto whitespace-pre-wrap">
                  {ex.sql}
                </pre>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{ex.query_type}</span>
                <button onClick={() => handleEdit(ex)}>
                  <Pencil className="w-4 h-4 text-gray-400 hover:text-gray-700" />
                </button>
                <button onClick={() => handleDelete(ex.id)}>
                  <Trash2 className="w-4 h-4 text-red-400 hover:text-red-600" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {examples.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">No examples yet. Add your first one.</p>
        )}
      </div>
    </div>
  );
}
