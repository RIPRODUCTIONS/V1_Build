"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function TemplateDetailPage() {
  const params = useParams<{ id: string }>();
  const templateId = params?.id || "";
  const [tpl, setTpl] = useState<any>(null);
  const [usage, setUsage] = useState<any[]>([]);
  const [stats, setStats] = useState<any | null>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [newPresetName, setNewPresetName] = useState<string>("");
  const [targets, setTargets] = useState<string>("");
  const [resp, setResp] = useState<any>(null);

  async function load() {
    if (!templateId) return;
    const t = await fetch(`/api/templates/${templateId}`).then((x) => x.json());
    setTpl(t);
    const u = await fetch(`/api/templates/usage?template_id=${encodeURIComponent(templateId)}&limit=20`).then((x) => x.json());
    setUsage(u.items || []);
    const p = await fetch(`/api/templates/${templateId}/presets`).then((x)=>x.json()).catch(()=>({ items: [] }));
    setPresets(p.items || []);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
      const ci = (typeof window !== 'undefined' ? localStorage.getItem('ci_token') || '' : '');
      const r = await fetch(`${base}/admin/templates/roi`, { headers: { 'X-CI-Token': ci }});
      if (r.ok) {
        const data = await r.json();
        const row = (data.roi || []).find((x: any)=> x.id === templateId);
        setStats(row || null);
      }
    } catch {}
  }

  useEffect(() => {
    load();
  }, [templateId]);

  return (
    <section className="p-4 space-y-4 max-w-3xl">
      <h1 className="text-xl font-semibold">Template: {templateId}</h1>
      {tpl && (
        <div className="border rounded p-3 bg-white space-y-1">
          <div className="font-medium">{tpl.name}</div>
          <div className="text-xs text-gray-600">{tpl.category} · {tpl.difficulty || ""}</div>
          <p className="text-sm mt-1">{tpl.description}</p>
          {templateId === "contact_form_lead_generator" && (
            <div className="mt-3 space-y-2">
              <label className="text-sm">Target websites (comma-separated)</label>
              <input className="border px-2 py-1 rounded w-full" value={targets} onChange={(e)=>setTargets(e.target.value)} placeholder="https://example.com/contact, https://httpbin.org/forms/post" />
              <button className="border px-3 py-1 rounded" onClick={async ()=>{
                const body = {
                  target_websites: targets.split(",").map(s=>s.trim()).filter(Boolean),
                  contact_message_template: "Hello from automation",
                  sender_information: { name: "Tester", email: "test@example.com" }
                };
                const r = await fetch(`/api/templates/${templateId}/deploy`, { method: 'POST', headers: { 'content-type':'application/json' }, body: JSON.stringify(body)}).then(x=>x.json());
                setResp(r);
                load();
              }}>Deploy</button>
            </div>
          )}
        </div>
      )}

      {resp && (
        <pre className="bg-black text-white p-3 rounded text-xs overflow-auto">{JSON.stringify(resp, null, 2)}</pre>
      )}

      <div>
        <h2 className="text-lg font-medium mb-2">Recent Usage</h2>
        {stats && (
          <div className={`text-xs mb-2 ${((stats.last_24h?.success_rate ?? 1) < 0.8) ? 'text-red-700' : 'text-gray-700'}`}>
            Last 24h: runs {stats.last_24h?.runs ?? 0}, success {stats.last_24h?.success ?? 0}, failed {stats.last_24h?.failed ?? 0}, rate {((stats.last_24h?.success_rate ?? 0)*100).toFixed(1)}%
          </div>
        )}
        {usage.length === 0 && <div className="text-sm text-gray-600">No recent usage.</div>}
        <ul className="space-y-2">
          {usage.map((it, idx) => (
            <li key={`${it.created_at}-${idx}`} className="border rounded p-3 bg-white">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm">{it.template_id}</span>
                <span className="text-sm">{new Date(it.created_at).toLocaleString()}</span>
              </div>
              <div className="text-xs text-gray-600">Queued: {it.queued_tasks} · {it.success ? "ok" : "failed"}</div>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="text-lg font-medium mb-2">Presets</h2>
        <div className="flex items-center gap-2 mb-2">
          <input className="border px-2 py-1 rounded" placeholder="Preset name" value={newPresetName} onChange={(e)=>setNewPresetName(e.target.value)} />
          <button className="border px-3 py-1 rounded" onClick={async()=>{
            const params = { name: newPresetName || 'Preset', parameters: { target_websites: targets.split(',').map(s=>s.trim()).filter(Boolean) } };
            await fetch(`/api/templates/${templateId}/presets`, { method: 'POST', headers: { 'content-type':'application/json' }, body: JSON.stringify(params) });
            setNewPresetName("");
            load();
          }}>Save Preset</button>
        </div>
        <ul className="space-y-2">
          {presets.map((p)=> (
            <li key={p.id} className="border rounded p-3 bg-white flex items-center justify-between">
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-xs text-gray-700 max-w-xl break-all">{JSON.stringify(p.parameters)}</div>
              </div>
              <button className="border px-3 py-1 rounded" onClick={async()=>{
                await fetch(`/api/templates/${templateId}/presets/${p.id}/run`, { method: 'POST' });
              }}>Run</button>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}


