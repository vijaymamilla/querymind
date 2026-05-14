"use client";

import { useEffect, useState } from "react";
import { modelConfigApi, ModelConfig } from "@/lib/api";
import { Settings2 } from "lucide-react";

const SELECT_OPTIONS: Record<string, string[]> = {
  dialect: ["postgresql", "mysql", "sqlite"],
  model: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
};

export default function ModelConfigPage() {
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [localValues, setLocalValues] = useState<Record<string, string>>({});

  const load = async () => {
    const { data } = await modelConfigApi.list();
    setConfigs(data);
    setLocalValues(Object.fromEntries(data.map((c) => [c.key, c.value])));
  };

  useEffect(() => { load(); }, []);

  const save = async (key: string) => {
    setSaving(key);
    await modelConfigApi.update(key, localValues[key]);
    await load();
    setSaving(null);
  };

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Model Config</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Configure the LLM, SQL dialect, and generation parameters.
        </p>
      </div>

      <div className="bg-white rounded-xl border shadow-sm divide-y">
        {configs.map((cfg) => (
          <div key={cfg.key} className="px-5 py-4">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <Settings2 className="w-4 h-4 text-gray-400" />
                <span className="font-mono text-sm font-medium">{cfg.key}</span>
              </div>
            </div>
            {cfg.description && (
              <p className="text-xs text-gray-500 ml-6 mb-2">{cfg.description}</p>
            )}
            <div className="ml-6 flex gap-2">
              {SELECT_OPTIONS[cfg.key] ? (
                <select
                  value={localValues[cfg.key] ?? cfg.value}
                  onChange={(e) => setLocalValues({ ...localValues, [cfg.key]: e.target.value })}
                  className="border rounded-lg px-3 py-1.5 text-sm"
                >
                  {SELECT_OPTIONS[cfg.key].map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              ) : (
                <input
                  value={localValues[cfg.key] ?? cfg.value}
                  onChange={(e) => setLocalValues({ ...localValues, [cfg.key]: e.target.value })}
                  className="border rounded-lg px-3 py-1.5 text-sm w-40"
                />
              )}
              <button
                onClick={() => save(cfg.key)}
                disabled={saving === cfg.key || localValues[cfg.key] === cfg.value}
                className="text-sm bg-sky-600 text-white px-3 py-1.5 rounded-lg hover:bg-sky-700 disabled:opacity-40"
              >
                {saving === cfg.key ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        ))}

        {configs.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">
            No model config found. Make sure the database is seeded.
          </p>
        )}
      </div>
    </div>
  );
}
