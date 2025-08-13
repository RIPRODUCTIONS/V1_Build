"use client";
import { useEffect, useState } from "react";

type ROI = { id: string; name: string; usage: number; estimated_time_saved_hours: number; estimated_cost_savings_usd: number };

export default function AdminTemplatesROIPage() {
  const [ciToken, setCiToken] = useState<string>("");
  const [rows, setRows] = useState<ROI[]>([]);
  const [rate, setRate] = useState<number>(50);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

  async function load() {
    const res = await fetch(`${API_BASE}/admin/templates/roi`, { headers: { "X-CI-Token": ciToken } });
    if (!res.ok) return;
    const data = await res.json();
    setRate(data.hourly_rate);
    setRows(data.roi || []);
  }

  useEffect(() => { if (ciToken) load(); }, [ciToken]);

  const total = rows.reduce((acc, r) => acc + (r.estimated_cost_savings_usd || 0), 0);

  return (
    <section className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Admin · Template ROI</h1>
      <div className="flex gap-2 items-center">
        <label className="text-sm">X-CI-Token</label>
        <input className="border px-2 py-1 rounded w-96" value={ciToken} onChange={(e)=>setCiToken(e.target.value)} placeholder="paste CI token" />
        <button className="border px-3 py-1 rounded" onClick={load} disabled={!ciToken}>Refresh</button>
      </div>
      <div className="text-sm text-gray-700">Hourly rate: ${rate}/hr · Total estimated savings: ${total.toFixed(2)}</div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {rows.map((r)=> (
          <div key={r.id} className="border rounded p-3 bg-white">
            <div className="font-medium">{r.name}</div>
            <div className="text-xs text-gray-600">{r.id}</div>
            <div className="text-sm mt-2">Usage: {r.usage}</div>
            <div className="text-sm">Time saved: {r.estimated_time_saved_hours.toFixed(2)} hours</div>
            <div className="text-sm font-semibold">Savings: ${r.estimated_cost_savings_usd.toFixed(2)}</div>
            {r.last_24h && (
              <div className="mt-2 text-xs text-gray-700">
                <div>Last 24h: runs {r.last_24h.runs}, success {r.last_24h.success}, failed {r.last_24h.failed}, rate {(r.last_24h.success_rate*100).toFixed(1)}%</div>
              </div>
            )}
            {r.last_24h && r.last_24h.success_rate < 0.8 && (
              <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2 space-y-1">
                <div>Alert: Success rate below threshold. Investigate recent failures.</div>
                <div className="flex gap-2">
                  <a className="underline" href={`/api/templates/usage?template_id=${r.id}&success=false&limit=50`}>View failed (JSON)</a>
                  <a className="underline" href={`/api/templates/usage?template_id=${r.id}&success=false&limit=200&format=csv`}>Export failed (CSV)</a>
                  <button
                    className="underline"
                    onClick={async()=>{
                      // basic rerun: pull last failed parameters and re-run
                      const failed = await fetch(`/api/templates/usage?template_id=${r.id}&success=false&limit=1`).then(x=>x.json()).catch(()=>({ items: []}));
                      const params = (failed.items && failed.items[0] && failed.items[0].parameters) || {};
                      await fetch(`/api/templates/${r.id}/rerun`, { method: 'POST', headers: { 'content-type':'application/json' }, body: JSON.stringify(params)});
                    }}
                  >Re-run (basic)</button>
                </div>
              </div>
            )}
            <Sparkline templateId={r.id} />
          </div>
        ))}
      </div>
    </section>
  );
}

function Sparkline({ templateId }: { templateId: string }) {
  const [data, setData] = useState<{ series: { t: number; success: number; failed: number }[] } | null>(null);
  const [hours, setHours] = useState<number>(24);
  const [buckets, setBuckets] = useState<number>(24);
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`/api/templates/usage/summary?template_id=${templateId}&hours=${hours}&buckets=${buckets}`);
        if (!r.ok) return;
        const d = await r.json();
        setData(d);
      } catch {}
    })();
  }, [templateId, hours, buckets]);
  if (!data) return null;
  const max = Math.max(1, ...data.series.map((b) => b.success + b.failed));
  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 text-[10px] text-gray-600 mb-1">
        <label>Hours</label>
        <select className="border px-1 py-0.5 rounded" value={hours} onChange={(e)=>setHours(Number(e.target.value))}>
          {[6, 12, 24, 48, 168].map(h=>(<option key={h} value={h}>{h}</option>))}
        </select>
        <label>Buckets</label>
        <select className="border px-1 py-0.5 rounded" value={buckets} onChange={(e)=>setBuckets(Number(e.target.value))}>
          {[6, 12, 24, 36, 48].map(b=>(<option key={b} value={b}>{b}</option>))}
        </select>
      </div>
      <div className="flex gap-1 items-end" aria-label="24h sparkline">
        {data.series.map((b, i) => {
          const total = b.success + b.failed;
          const h = Math.max(2, Math.round((total / max) * 40));
          const okh = Math.round((b.success / Math.max(1, total)) * h);
          return (
            <div key={i} className="w-2 bg-red-300 relative" style={{ height: h }}>
              <div className="absolute bottom-0 left-0 right-0 bg-green-500" style={{ height: okh }} />
            </div>
          );
        })}
      </div>
      <div className="text-[10px] text-gray-500 mt-1">Success (green) vs Failed (red) — last {hours}h</div>
    </div>
  );
}


