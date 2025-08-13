"use client";
import { useEffect, useMemo, useState } from "react";

type Usage = {
  template_id: string;
  queued_tasks: number;
  success: boolean;
  created_at: string;
  parameters?: any;
};

export default function AdminTemplateFailuresPage() {
  const [templateId, setTemplateId] = useState<string>("");
  const [items, setItems] = useState<Usage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(() => {
    const p = new URLSearchParams({ success: "false", limit: "200" });
    if (templateId) p.set("template_id", templateId);
    return p.toString();
  }, [templateId]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/templates/usage?${query}`);
      if (!r.ok) throw new Error("load");
      const data = await r.json();
      setItems(data.items || []);
    } catch (e) {
      setError("Failed to load failures");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [query]);

  return (
    <section className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Admin · Template Failures</h1>
      <div className="flex items-center gap-2">
        <input className="border px-2 py-1 rounded" placeholder="Filter by template_id (optional)" value={templateId} onChange={(e)=>setTemplateId(e.target.value)} />
        <button className="border px-3 py-1 rounded" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
        <a className="underline text-sm" href={`/api/templates/usage?${query}`}>View JSON</a>
        <a className="underline text-sm" href={`/api/templates/usage?${query}&format=csv`}>Export CSV</a>
        <button className="border px-3 py-1 rounded" onClick={async()=>{
          if (!templateId) return;
          await fetch(`/api/templates/${templateId}/rerun_bulk`, { method: 'POST' });
        }}>Re-run all last 24h</button>
        <button className="border px-3 py-1 rounded" onClick={async()=>{
          if (!templateId) return;
          const name = prompt('Preset name?', 'Last Failed');
          if (!name) return;
          await fetch(`/api/templates/${templateId}/presets/save_last_failed`, { method: 'POST', headers: { 'content-type':'application/json' }, body: JSON.stringify({ name }) });
        }}>Save last failed as preset</button>
      </div>
      {error && <div className="text-red-700 text-sm">{error}</div>}
      <div className="overflow-auto">
        <table className="min-w-full text-sm border">
          <thead>
            <tr className="bg-gray-50">
              <th className="border px-2 py-1 text-left">Time</th>
              <th className="border px-2 py-1 text-left">Template</th>
              <th className="border px-2 py-1 text-left">Queued</th>
              <th className="border px-2 py-1 text-left">Parameters</th>
              <th className="border px-2 py-1 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={`${it.template_id}-${idx}-${it.created_at}`}>
                <td className="border px-2 py-1">{new Date(it.created_at).toLocaleString()}</td>
                <td className="border px-2 py-1 font-mono">{it.template_id}</td>
                <td className="border px-2 py-1">{it.queued_tasks}</td>
                <td className="border px-2 py-1">
                  <pre className="max-w-xl whitespace-pre-wrap break-all">{JSON.stringify(it.parameters, null, 2)}</pre>
                </td>
                <td className="border px-2 py-1">
                  <button
                    className="text-blue-700 underline"
                    onClick={async()=>{
                      await fetch(`/api/templates/${it.template_id}/rerun`, { method: 'POST', headers: { 'content-type':'application/json' }, body: JSON.stringify(it.parameters || {})});
                    }}
                  >Re-run</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && !loading && <div className="text-gray-600 text-sm mt-2">No failures found.</div>}
      </div>
    </section>
  );
}


