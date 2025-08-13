"use client";
import { useEffect, useState } from "react";

export default function PersonalDashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [onboarding, setOnboarding] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const s = await fetch(`/api/onboarding/status`).then((x) => x.json());
        setOnboarding(s);
      } catch {}
      try {
        const m = await fetch(`/api/operator/metrics/summary`).then((x) => x.json());
        setSummary(m);
      } catch {}
    })();
  }, []);

  const widgets = [
    { title: "Email Status", data: "—", automation: "personal_email_manager" },
    { title: "Finance Summary", data: "—", automation: "personal_finance_tracker" },
    { title: "Social Media", data: "—", automation: "social_media_manager" },
    { title: "Research Queue", data: "—", automation: "research_assistant" },
  ];

  return (
    <section className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Your Personal AI Assistant</h1>
      {onboarding && (
        <div className="border rounded p-4 bg-white">
          <div className="font-medium">Credits: ${onboarding.balance_usd?.toFixed?.(2) ?? "0.00"}</div>
          <div className="text-sm text-gray-600">Onboarding Steps:</div>
          <ul className="list-disc ml-5">
            {onboarding.checklist?.map((s: any, i: number) => (
              <li key={i} className={s.completed ? "text-green-700" : ""}>{s.title}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {widgets.map((w) => (
          <div key={w.automation} className="border rounded p-4 bg-white">
            <div className="font-medium">{w.title}</div>
            <div className="text-sm text-gray-700">{w.data}</div>
            <div className="mt-2">
              <a className="underline text-sm" href={`/templates/${w.automation}`}>Open</a>
            </div>
          </div>
        ))}
      </div>
      {summary && (
        <div className="text-xs text-gray-600">Today: Started {summary.tasks_started} · p95 {summary.p95_ms ?? "-"} ms</div>
      )}
    </section>
  );
}


