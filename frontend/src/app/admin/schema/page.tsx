"use client";

import { useEffect, useState } from "react";
import { schemaApi, SchemaColumn } from "@/lib/api";
import { Eye, EyeOff, Plus, Pencil, Trash2, RefreshCw } from "lucide-react";

export default function SchemaPage() {
  const [liveSchema, setLiveSchema] = useState<Record<string, Record<string, string>>>({});
  const [columns, setColumns] = useState<SchemaColumn[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ description: "", synonyms: "", is_sensitive: false });

  const load = async () => {
    setLoading(true);
    const [schemaRes, colsRes] = await Promise.all([
      schemaApi.introspect(),
      schemaApi.listColumns(),
    ]);
    setLiveSchema(schemaRes.data.schema);
    setColumns(colsRes.data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const getColumnMeta = (table: string, col: string) =>
    columns.find((c) => c.table_name === table && c.column_name === col);

  const startEdit = (col: SchemaColumn) => {
    setEditingId(col.id);
    setEditForm({
      description: col.description || "",
      synonyms: col.synonyms.join(", "),
      is_sensitive: col.is_sensitive,
    });
  };

  const saveEdit = async (id: number) => {
    await schemaApi.updateColumn(id, {
      description: editForm.description,
      synonyms: editForm.synonyms.split(",").map((s) => s.trim()).filter(Boolean),
      is_sensitive: editForm.is_sensitive,
    });
    setEditingId(null);
    load();
  };

  const toggleSensitive = async (col: SchemaColumn) => {
    await schemaApi.updateColumn(col.id, { is_sensitive: !col.is_sensitive });
    load();
  };

  return (
    <div className="p-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Schema Manager</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Browse live tables, add descriptions and synonyms, mark sensitive columns.
          </p>
        </div>
        <button onClick={load} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading schema…</p>
      ) : (
        <div className="space-y-6">
          {Object.entries(liveSchema).map(([tableName, cols]) => (
            <div key={tableName} className="bg-white rounded-xl border shadow-sm overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b">
                <span className="font-mono font-semibold text-sm text-sky-700">{tableName}</span>
                <span className="ml-2 text-xs text-gray-400">{Object.keys(cols).length} columns</span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-xs text-gray-500">
                    <th className="px-4 py-2 text-left">Column</th>
                    <th className="px-4 py-2 text-left">Type</th>
                    <th className="px-4 py-2 text-left">Description</th>
                    <th className="px-4 py-2 text-left">Synonyms</th>
                    <th className="px-4 py-2 text-center">Sensitive</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(cols).map(([colName, colType]) => {
                    const meta = getColumnMeta(tableName, colName);
                    const isEditing = meta && editingId === meta.id;

                    return (
                      <tr key={colName} className="border-b last:border-0 hover:bg-gray-50">
                        <td className="px-4 py-2 font-mono text-xs text-gray-800">{colName}</td>
                        <td className="px-4 py-2 text-xs text-gray-500">{colType}</td>
                        <td className="px-4 py-2">
                          {isEditing ? (
                            <input
                              className="w-full border rounded px-2 py-1 text-xs"
                              value={editForm.description}
                              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                              placeholder="Column description…"
                            />
                          ) : (
                            <span className="text-xs text-gray-600">{meta?.description || "—"}</span>
                          )}
                        </td>
                        <td className="px-4 py-2">
                          {isEditing ? (
                            <input
                              className="w-full border rounded px-2 py-1 text-xs"
                              value={editForm.synonyms}
                              onChange={(e) => setEditForm({ ...editForm, synonyms: e.target.value })}
                              placeholder="revenue, income, …"
                            />
                          ) : (
                            <span className="text-xs text-gray-500">
                              {meta?.synonyms.join(", ") || "—"}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-center">
                          {meta ? (
                            <button onClick={() => toggleSensitive(meta)}>
                              {meta.is_sensitive ? (
                                <EyeOff className="w-4 h-4 text-red-500 mx-auto" />
                              ) : (
                                <Eye className="w-4 h-4 text-gray-400 mx-auto" />
                              )}
                            </button>
                          ) : "—"}
                        </td>
                        <td className="px-4 py-2 text-right">
                          {isEditing ? (
                            <button
                              onClick={() => saveEdit(meta!.id)}
                              className="text-xs bg-sky-600 text-white px-2 py-1 rounded hover:bg-sky-700"
                            >
                              Save
                            </button>
                          ) : meta ? (
                            <button onClick={() => startEdit(meta)}>
                              <Pencil className="w-3.5 h-3.5 text-gray-400 hover:text-gray-700" />
                            </button>
                          ) : (
                            <button
                              className="text-xs text-sky-600 hover:underline"
                              onClick={async () => {
                                await schemaApi.createColumn({
                                  table_name: tableName,
                                  column_name: colName,
                                });
                                load();
                              }}
                            >
                              <Plus className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
