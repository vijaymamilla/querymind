"use client";

import { useEffect, useState } from "react";
import { guardrailsApi, GuardrailConfig } from "@/lib/api";
import { Shield } from "lucide-react";

const BOOL_KEYS = ["allow_select", "allow_insert", "allow_update", "allow_delete"];

export default function GuardrailsPage() {
  const [configs, setConfigs] = useState<GuardrailConfig[]>([]);
  const [saving, setSaving] = useState<string | null>(null);

  const load = async () => {
    const { data } = await guardrailsApi.list();
    setConfigs(data);
  };

  useEffect(() => { load(); }, []);

  const toggle = async (cfg: GuardrailConfig) => {
    setSaving(cfg.key);
    const newVal = cfg.value === "true" ? "false" : "true";
    await guardrailsApi.update(cfg.key, newVal);
    await load();
    setSaving(null);
  };

  const updateValue = async (key: string, value: string) => {
    setSaving(key);
    await guardrailsApi.update(key, value);
    await load();
    setSaving(null);
  };

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Guardrails Config</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Control what SQL operations are permitted and result limits.
        </p>
      </div>

      <div className="bg-white rounded-xl border shadow-sm divide-y">
        {configs.map((cfg) => (
          <div key={cfg.key} className="px-5 py-4 flex items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-gray-400" />
                <span className="font-mono text-sm font-medium">{cfg.key}</span>
              </div>
              {cfg.description && (
                <p className="text-xs text-gray-500 mt-0.5 ml-6">{cfg.description}</p>
              )}
            </div>

            {BOOL_KEYS.includes(cfg.key) ? (
              <button
                onClick={() => toggle(cfg)}
                disabled={saving === cfg.key}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  cfg.value === "true" ? "bg-sky-600" : "bg-gray-300"
                } disabled:opacity-50`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    cfg.value === "true" ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            ) : (
              <input
                type="number"
                defaultValue={cfg.value}
                onBlur={(e) => updateValue(cfg.key, e.target.value)}
                className="w-24 border rounded-lg px-3 py-1.5 text-sm text-right"
              />
            )}
          </div>
        ))}

        {configs.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">
            No guardrail config found. Make sure the database is seeded.
          </p>
        )}
      </div>
    </div>
  );
}
