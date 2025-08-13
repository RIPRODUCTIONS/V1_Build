"use client";
import { useEffect, useState } from "react";

type Run = { run_id: string; status: string; detail?: any };

export default function AutomationRuns() {
  const [ids, setIds] = useState<string[]>([]);
  const [runs, setRuns] = useState<Record<string, Run>>({});
  const [stream, setStream] = useState<EventSource | null>(null);

  async function poll(id: string) {
    const r = await fetch(`/api/automation/runs/${id}`).then((x) => x.json());
    setRuns((prev) => ({ ...prev, [id]: r }));
  }

  useEffect(() => {
    const t = setInterval(() => ids.forEach((id) => poll(id)), 1000);
    return () => clearInterval(t);
  }, [ids]);

  useEffect(() => {
    if (!ids[0]) return;
    // Bind to first run for demo streaming
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
    const es = new EventSource(`${base}/operator/runs/${ids[0]}/stream`);
    es.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data);
        // naive: refresh list on messages
        poll(ids[0]);
      } catch {}
    };
    setStream(es);
    return () => { es.close(); setStream(null); };
  }, [ids]);

  return (
    <section className="space-y-4 p-4">
      <h1 className="text-xl font-semibold">Automations</h1>
      <div className="flex gap-2">
        <button
          className="border px-3 py-1 rounded"
          onClick={async () => {
            const r = await fetch("/api/automation/submit", {
              method: "POST",
              headers: { "content-type": "application/json" },
              body: JSON.stringify({
                intent: "lead.intake",
                payload: { lead: { name: "Alice" } },
                idempotency_key: crypto.randomUUID(),
              }),
            }).then((x) => x.json());
            setIds((prev) => [r.run_id, ...prev]);
          }}
        >
          Run: Lead Intake
        </button>
        <button
          className="border px-3 py-1 rounded"
          onClick={async () => {
            const r = await fetch("/api/automation/submit", {
              method: "POST",
              headers: { "content-type": "application/json" },
              body: JSON.stringify({
                intent: "agent.prototype",
                payload: { name: "Demo", prompt: "Hello world" },
                idempotency_key: crypto.randomUUID(),
              }),
            }).then((x) => x.json());
            setIds((prev) => [r.run_id, ...prev]);
          }}
        >
          Run: Prototype
        </button>
      </div>
      <ul className="space-y-2">
        {ids.map((id) => (
          <li key={id} className="border rounded p-3 bg-white">
            <div className="text-sm text-gray-700 font-mono">{id}</div>
            <div className="text-sm">
              {runs[id]?.status ?? "queued"} — {runs[id]?.detail?.executed?.join(" → ") ?? ""}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
