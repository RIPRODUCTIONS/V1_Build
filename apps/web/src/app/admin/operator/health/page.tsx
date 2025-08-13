"use client";
import { useEffect, useState } from "react";

type Template = { id: string; name: string; category: string };
type Bucket = { t: number; success: number; failed: number };

export default function OperatorHealthPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [recentRuns, setRecentRuns] = useState<{ run_id: string; status: string; meta?: any }[]>([]);
  const [metricSummary, setMetricSummary] = useState<any | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const tpl = await fetch(`/api/templates`).then((x) => x.json());
        setTemplates(tpl.templates || []);
      } catch {}
      try {
        const rec = await fetch(`/api/automation/recent?limit=10`).then((x) => x.json());
        setRecentRuns(rec.items || []);
      } catch {}
      try {
        const m = await fetch(`/api/operator/metrics/summary`).then((x)=>x.json());
        setMetricSummary(m);
      } catch {}
    })();
  }, []);

  return (
    <section className="p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Operator Health</h1>
        <a className="underline text-sm" href="/admin/templates/failures">View Failures</a>
      </div>

      <div>
        <h2 className="text-lg font-medium mb-2">Templates</h2>
        {metricSummary && (
          <div className="text-sm text-gray-700 mb-2">
            Started: {metricSummary.tasks_started}
            {" "}· Completed: {Object.entries(metricSummary.tasks_completed||{}).map(([k,v])=>`${k}:${v}`).join(' ')}
            {" "}· Actions: {Object.entries(metricSummary.actions||{}).map(([k,v])=>`${k}:${v}`).join(' ')}
            {" "}· ActionErrors: {Object.entries(metricSummary.action_errors||{}).map(([k,v])=>`${k}:${v}`).join(' ')}
            {metricSummary.p95_ms !== undefined && (
              <>
                {" "}· p95: {metricSummary.p95_ms} ms
              </>
            )}
            {metricSummary.grafana?.dashboard_url && (
              <>
                {" "}· <a className="underline" href={`${metricSummary.grafana.dashboard_url}`} target="_blank" rel="noreferrer">Open Grafana</a>
              </>
            )}
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {templates.map((t) => (
            <TemplateCard key={t.id} id={t.id} name={t.name} />
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-lg font-medium mb-2">Recent Runs</h2>
        <ul className="space-y-2">
          {recentRuns.map((r) => (
            <li key={r.run_id} className="border rounded p-3 bg-white flex items-center justify-between">
              <span className="font-mono text-sm">{r.run_id}</span>
              <span className="text-sm">{r.status}</span>
              <span className="text-xs text-gray-700">{r.meta?.intent}</span>
            </li>
          ))}
          {!recentRuns.length && <div className="text-sm text-gray-600">No recent runs.</div>}
        </ul>
      </div>
    </section>
  );
}

function TemplateCard({ id, name }: { id: string; name: string }) {
  const [series, setSeries] = useState<Bucket[] | null>(null);
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`/api/templates/usage/summary?template_id=${id}&hours=24&buckets=24`);
        if (!r.ok) return;
        const d = await r.json();
        setSeries(d.series || []);
      } catch {}
    })();
  }, [id]);
  const max = Math.max(1, ...(series || []).map((b) => b.success + b.failed));
  return (
    <div className="border rounded p-3 bg-white">
      <div className="font-medium">{name}</div>
      <div className="text-xs text-gray-600">{id}</div>
      <div className="mt-2">
        {series ? (
          <div>
            <div className="grid grid-cols-24 gap-px items-end" aria-label={`sparkline-${id}`}>
              {series.map((b, i) => {
                const total = b.success + b.failed;
                const h = Math.max(2, Math.round((total / max) * 40));
                const okh = Math.round((b.success / Math.max(1, total)) * h);
                return (
                  <div key={i} className="w-2 bg-red-300 relative h-[40px]">
                    <div className="absolute bottom-0 left-0 right-0 bg-green-500" style={{ height: okh }} />
                  </div>
                );
              })}
            </div>
            <div className="text-[10px] text-gray-500 mt-1">24h success/failed</div>
          </div>
        ) : (
          <div className="text-xs text-gray-600">Loading…</div>
        )}
      </div>
      <div className="mt-2 text-xs">
        <a className="underline" href={`/templates/${id}`}>Details</a>
        <span className="mx-1">·</span>
        <a className="underline" href={`/admin/templates/failures?template_id=${id}`}>Failures</a>
      </div>
    </div>
  );
}


