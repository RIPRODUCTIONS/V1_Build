"use client";
import { useEffect, useMemo, useState } from "react";

type Template = {
  id: string;
  name: string;
  description?: string;
  category?: string;
  estimated_time_minutes?: number;
  price_per_run_usd?: number;
};

export default function MarketplacePage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [buyAmount, setBuyAmount] = useState<string>("20");
  const [params, setParams] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [usage, setUsage] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const tpl = await fetch(`/api/marketplace/templates`).then((x) => x.json());
        setTemplates(tpl.templates || []);
      } catch {}
      try {
        const c = await fetch(`/api/marketplace/credits`).then((x) => x.json());
        setBalance(Number(c.balance_usd || 0));
      } catch {}
      try {
        const u = await fetch(`/api/marketplace/usage?limit=20`).then((x) => x.json());
        setUsage(u.items || []);
      } catch {}
    };
    load();

    const url = new URL(window.location.href);
    const sessionId = url.searchParams.get("session_id");
    const success = url.searchParams.get("success");
    if (success && sessionId) {
      (async () => {
        try {
          const res = await fetch(`/api/marketplace/buy_credits/confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId }),
          }).then((x) => x.json());
          setMessage(`Credits added successfully! New balance: $${Number(res.balance_usd || 0).toFixed(2)}`);
          await load();
        } catch {}
      })();
    }
  }, []);

  const grouped = useMemo(() => {
    const byCat: Record<string, Template[]> = {};
    for (const t of templates) {
      const cat = t.category || "misc";
      byCat[cat] = byCat[cat] || [];
      byCat[cat].push(t);
    }
    return byCat;
  }, [templates]);

  const buyCredits = async () => {
    setLoading(true);
    setMessage("");
    try {
      const checkout = await fetch(`/api/marketplace/buy_credits/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_usd: Number(buyAmount || 0) }),
      });
      if (checkout.ok) {
        const data = await checkout.json();
        if (data.url) {
          window.location.href = data.url;
          return;
        }
      }
      const res = await fetch(`/api/marketplace/buy_credits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_usd: Number(buyAmount || 0) }),
      }).then((x) => x.json());
      setMessage(`Credits purchased. Balance: $${res.balance_usd}`);
    } catch (e: any) {
      setMessage(`Failed to buy credits: ${e?.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  const paramsFor = (id: string) => {
    try {
      const raw = params[id] || "{}";
      return JSON.parse(raw);
    } catch {
      return {};
    }
  };

  const runTemplate = async (t: Template) => {
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch(`/api/marketplace/run/${t.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(paramsFor(t.id)),
      }).then((x) => x.json());
      if (res?.billing?.ok) {
        setMessage(`Queued ${t.name}. ${res.task_count} task(s). Charged $${res.total_price_usd}. New balance: $${res.billing.balance_usd}`);
      } else {
        setMessage(`Failed to queue: ${res?.detail?.error || res?.detail || 'unknown error'}`);
      }
    } catch (e: any) {
      setMessage(`Error: ${e?.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Automation Marketplace</h1>
        <div className="text-sm">
          Credits Balance: <span className="font-semibold">$ {balance.toFixed(2)}</span>
        </div>
      </div>

      <div className="border rounded p-4 bg-white">
        <h2 className="text-lg font-semibold mb-2">Buy Credits</h2>
        <div className="flex items-center gap-2">
          <label htmlFor="buy-amount" className="sr-only">Buy amount</label>
          <input id="buy-amount" aria-label="Buy amount" placeholder="20" className="border rounded px-2 py-1 w-28" type="number" min={0} step={1} value={buyAmount} onChange={(e) => setBuyAmount(e.target.value)} />
          <button onClick={buyCredits} disabled={loading} className="bg-blue-600 text-white px-3 py-1 rounded">Buy</button>
        </div>
        <div className="text-xs text-gray-600 mt-1">$20, $50, $100+ packages. Larger packages include bonus credits.</div>
        <div className="text-xs text-gray-600 mt-1">New here? Start with free $5 credits via Onboarding.</div>
        <div className="mt-2">
          <button
            onClick={async () => {
              try {
                const r = await fetch(`/api/onboarding/start`, { method: "POST" }).then((x) => x.json());
                setMessage(`$${r.free_credits_granted} free credits granted! Try LinkedIn Lead Extractor or Price Spy.`);
              } catch {}
            }}
            className="bg-green-600 text-white px-3 py-1 rounded"
          >
            Claim $5 Free Credits
          </button>
        </div>
      </div>

      {message && <div className="p-3 rounded bg-yellow-50 border border-yellow-200 text-sm">{message}</div>}

      {Object.entries(grouped).map(([cat, list]) => (
        <div key={cat}>
          <h2 className="text-xl font-semibold mb-2 capitalize">{cat.split("_").join(" ")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map((t) => (
              <div key={t.id} className="border rounded p-4 bg-white space-y-2">
                <div className="font-medium">{t.name}</div>
                {t.description && <div className="text-sm text-gray-700">{t.description}</div>}
                <div className="text-xs text-gray-600">Est. {t.estimated_time_minutes ?? "-"} min · Price: $ {t.price_per_run_usd?.toFixed(2) ?? "-"}</div>
                <div>
                  <label className="block text-xs font-medium mb-1">Parameters (JSON)</label>
                  <textarea
                    className="border rounded w-full p-2 text-xs"
                    rows={4}
                    placeholder={"{\n  \"target_websites\": [\"https://example.com\"]\n}"}
                    value={params[t.id] || ""}
                    onChange={(e) => setParams((p) => ({ ...p, [t.id]: e.target.value }))}
                  />
                </div>
                <button onClick={() => runTemplate(t)} disabled={loading} className="bg-green-600 text-white px-3 py-1 rounded">Try for $ {t.price_per_run_usd?.toFixed(2) ?? "-"}</button>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="border rounded p-4 bg-white">
        <h2 className="text-lg font-semibold mb-2">Receipts</h2>
        {!usage.length && <div className="text-sm text-gray-600">No recent usage.</div>}
        {!!usage.length && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2 pr-4">Time</th>
                  <th className="py-2 pr-4">Template</th>
                  <th className="py-2 pr-4">Cost</th>
                  <th className="py-2 pr-4">Tasks</th>
                </tr>
              </thead>
              <tbody>
                {usage.map((r) => (
                  <tr key={r.id} className="border-b hover:bg-gray-50">
                    <td className="py-1 pr-4">{new Date(r.executed_at).toLocaleString()}</td>
                    <td className="py-1 pr-4">{r.template_id}</td>
                    <td className="py-1 pr-4">$ {Number(r.cost_usd).toFixed(2)}</td>
                    <td className="py-1 pr-4">{r.summary?.task_count ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}


