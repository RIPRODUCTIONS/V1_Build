"use client";
import { useEffect, useMemo, useState } from "react";

type Detail = {
  task_id: string;
  kind: string;
  status: string;
  parameters?: any;
  result_summary?: any;
  created_at?: string;
  updated_at?: string;
};

export default function InvestigationDetailPage({ params }: { params: { task_id: string } }) {
  const taskId = params.task_id;
  const [detail, setDetail] = useState<Detail | null>(null);
  const [live, setLive] = useState<any | null>(null);
  const [msg, setMsg] = useState<string>("");

  const status = live?.status || detail?.status || "pending";
  const kind = detail?.kind || "";
  const summary = useMemo(() => {
    if (live?.result) return live.result;
    return detail?.result_summary || null;
  }, [live, detail]);

  const load = async () => {
    try {
      const res = await fetch(`/api/investigations/${taskId}`).then((x) => x.json());
      setDetail(res);
    } catch {}
  };

  useEffect(() => {
    load();
    const es = new EventSource(`/api/investigations/stream/${taskId}`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setLive(data);
      } catch {}
    };
    es.onerror = () => {
      es.close();
    };
    return () => es.close();
  }, [taskId]);

  const runAgain = async () => {
    try {
      if (kind === "osint") {
        const subject = detail?.parameters?.subject || {};
        const res = await fetch(`/api/investigations/osint/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subject }),
        }).then((x) => x.json());
        setMsg(`Requeued OSINT: ${res.task_id || "queued"}`);
      } else {
        const subject = detail?.parameters?.subject || {};
        const res = await fetch(`/api/investigations/autopilot/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subject }),
        }).then((x) => x.json());
        setMsg(`Requeued Autopilot: ${res.task_id || "queued"}`);
      }
    } catch (e: any) {
      setMsg(`Error: ${e?.message || "failed"}`);
    }
  };

  const osintPdfUrl = detail?.task_id ? `/api/investigations/osint/report/${detail.task_id}` : undefined;
  const fxPdfUrl = detail?.task_id ? `/api/investigations/forensics/report/${detail.task_id}` : undefined;
  const mwPdfUrl = detail?.task_id ? `/api/investigations/malware/report/${detail.task_id}` : undefined;

  // Extract aggregated artifacts for autopilot shape
  const autopilot = Array.isArray(summary?.steps) ? summary : null;
  const osint = autopilot ? (summary.steps.find((s: any) => s.osint)?.osint || null) : (summary && summary.plan ? summary : null);
  const ents: string[] = osint?.entities || summary?.entities || [];
  const tl = (osint?.timeline || summary?.timeline || []).slice(0, 50);
  const iocs = autopilot ? (summary.steps.find((s: any) => s.malware_dynamic)?.malware_dynamic?.iocs || {}) : (summary?.iocs || {});

  return (
    <section className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Investigation</h1>
        <div className={`text-sm ${status === 'completed' ? 'text-green-600' : status === 'error' ? 'text-red-600' : 'text-gray-600'}`}>{status}</div>
      </div>
      <div className="text-xs text-gray-600">Task: {taskId}</div>
      <div className="text-xs text-gray-600">Kind: {kind}</div>

      <div className="flex items-center gap-3">
        <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm" onClick={runAgain}>Run again</button>
        {kind === 'osint' && osintPdfUrl && (
          <a href={osintPdfUrl} target="_blank" rel="noreferrer" className="underline text-blue-700 text-sm">Download OSINT PDF</a>
        )}
        {kind === 'forensics_timeline' && fxPdfUrl && (
          <a href={fxPdfUrl} target="_blank" rel="noreferrer" className="underline text-blue-700 text-sm">Forensics PDF</a>
        )}
        {kind === 'malware_dynamic' && mwPdfUrl && (
          <a href={mwPdfUrl} target="_blank" rel="noreferrer" className="underline text-blue-700 text-sm">Malware PDF</a>
        )}
      </div>
      {msg && <div className="text-xs text-gray-700">{msg}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Entities</div>
          {!ents?.length && <div className="text-sm text-gray-600">No entities.</div>}
          {!!ents?.length && (
            <ul className="text-sm list-disc pl-5">
              {ents.slice(0, 100).map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Timeline</div>
          {!tl?.length && <div className="text-sm text-gray-600">No timeline events.</div>}
          {!!tl?.length && (
            <ul className="text-sm list-disc pl-5">
              {tl.map((ev: any, i: number) => (
                <li key={i}><span className="font-mono">{ev.date_text || ev.timestamp}</span> — <span>{(ev.context || ev.event || "").toString().slice(0, 120)}</span></li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="border rounded p-4 bg-white">
        <div className="font-medium mb-2">IOCs</div>
        {!(iocs && (iocs.domains || iocs.ips || iocs.mutexes || iocs.registry_keys)) && (
          <div className="text-sm text-gray-600">No IOCs.</div>
        )}
        {(iocs?.domains || iocs?.ips || iocs?.mutexes || iocs?.registry_keys) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <div className="font-medium">Domains</div>
              <ul className="list-disc pl-5">{(iocs.domains || []).slice(0, 20).map((d: string, i: number) => <li key={i}>{d}</li>)}</ul>
            </div>
            <div>
              <div className="font-medium">IPs</div>
              <ul className="list-disc pl-5">{(iocs.ips || []).slice(0, 20).map((d: string, i: number) => <li key={i}>{d}</li>)}</ul>
            </div>
            <div>
              <div className="font-medium">Mutexes</div>
              <ul className="list-disc pl-5">{(iocs.mutexes || []).slice(0, 20).map((d: string, i: number) => <li key={i}>{d}</li>)}</ul>
            </div>
            <div>
              <div className="font-medium">Registry Keys</div>
              <ul className="list-disc pl-5">{(iocs.registry_keys || []).slice(0, 20).map((d: string, i: number) => <li key={i}>{d}</li>)}</ul>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}


