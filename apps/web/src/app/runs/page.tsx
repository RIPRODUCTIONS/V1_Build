"use client";
import React from "react";
import { apiFetch } from "@/lib/api";

type Run = { id: number; status: string; intent?: string | null; department?: string | null; created_at: string };

export default function RunsPage() {
  const [items, setItems] = React.useState<Run[]>([]);
  const [status, setStatus] = React.useState<string>("");
  const [intent, setIntent] = React.useState<string>("");
  const [loading, setLoading] = React.useState(false);

  async function load() {
    setLoading(true);
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (intent) params.set("intent", intent);
    params.set("limit", "20");
    params.set("offset", "0");
    const res = await apiFetch<{ items: Run[] }>(`/runs?${params.toString()}`);
    setItems(res.items || []);
    setLoading(false);
  }

  React.useEffect(() => {
    load();
  }, []);

  return (
    <section className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Runs</h1>
      <div className="flex gap-2 items-end">
        <div>
          <label className="block text-sm">Status</label>
          <input className="border px-2 py-1 rounded" value={status} onChange={(e) => setStatus(e.target.value)} placeholder="completed" />
        </div>
        <div>
          <label className="block text-sm">Intent</label>
          <input className="border px-2 py-1 rounded" value={intent} onChange={(e) => setIntent(e.target.value)} placeholder="calendar" />
        </div>
        <button className="border px-3 py-1 rounded" onClick={load} disabled={loading}>{loading ? "Loading…" : "Apply"}</button>
      </div>
      {items.length === 0 ? (
        <div className="text-gray-600">No runs found.</div>
      ) : (
        <ul className="space-y-2">
          {items.map((r) => (
            <li key={r.id} className="p-3 rounded border bg-white grid grid-cols-4 gap-2 items-center">
              <span className="font-mono text-sm">#{r.id}</span>
              <span className="text-sm">{r.status}</span>
              <span className="text-sm text-gray-600 truncate" title={r.intent || ""}>{r.intent || "-"}</span>
              <span className="text-sm text-gray-500">{r.created_at}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
