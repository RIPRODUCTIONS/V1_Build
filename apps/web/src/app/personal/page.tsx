"use client";
import { useEffect, useState } from "react";
import { buildAuthHeaders, sseUrl } from "@/lib/security";

export default function PersonalDashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [onboarding, setOnboarding] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [running, setRunning] = useState<Record<string, boolean>>({});
  const [lastResult, setLastResult] = useState<Record<string, any>>({});
  const [recentRuns, setRecentRuns] = useState<Array<{ id: number; template_id: string; task_id: string; status: string; created_at?: string }>>([]);
  const [oauthStatus, setOauthStatus] = useState<{ twitter?: boolean; linkedin?: boolean }>({});
  const [postText, setPostText] = useState("Hello world");
  const [postPlatforms, setPostPlatforms] = useState<string>("twitter,linkedin");
  const [emailQuery, setEmailQuery] = useState<string>("newer_than:1d");
  const [emailMax, setEmailMax] = useState<number>(50);
  const [researchTopic, setResearchTopic] = useState<string>("AI automation trends");
  const [shopQuery, setShopQuery] = useState<string>("laptop under $1000");
  const [shopMax, setShopMax] = useState<number>(20);

  useEffect(() => {
    (async () => {
      try {
        const s = await fetch(`/api/onboarding/status`, { headers: buildAuthHeaders() }).then((x) => x.json());
        setOnboarding(s);
      } catch {}
      try {
        const m = await fetch(`/api/operator/metrics/summary`, { headers: buildAuthHeaders() }).then((x) => x.json());
        setSummary(m);
      } catch {}
      try {
        const c = await fetch(`/api/personal/config`, { headers: buildAuthHeaders() }).then((x) => x.json());
        setConfig(c);
      } catch {}
      try {
        const s = await fetch(`/api/personal/social/oauth/status`, { headers: buildAuthHeaders() }).then((x) => x.json());
        setOauthStatus(s);
      } catch {}
      try {
        const r = await fetch(`/api/personal/runs`, { headers: buildAuthHeaders() }).then((x) => x.json());
        setRecentRuns(r.items || []);
      } catch {}
    })();
  }, []);
  useEffect(() => {
    const t = setInterval(async () => {
      try {
        const r = await fetch(`/api/personal/runs`, { headers: buildAuthHeaders() }).then((x) => x.json());
        setRecentRuns(r.items || []);
      } catch {}
    }, 5000);
    return () => clearInterval(t);
  }, []);

  const followRun = (taskId: string, templateId?: string) => {
    try {
      const es = new EventSource(sseUrl(`/api/personal/stream/${taskId}`));
      es.onmessage = (evt) => {
        const data = JSON.parse(evt.data);
        const key = templateId || taskId;
        setLastResult((prev) => ({ ...prev, [key]: data }));
        if (data?.status === "completed" || data?.status === "error") {
          es.close();
        }
      };
      es.onerror = () => es.close();
    } catch (e) {
      // no-op
    }
  };


  const runPersonalAutomation = async (templateId: string, parameters: any = {}) => {
    try {
      setRunning((r) => ({ ...r, [templateId]: true }));
      // Immediately surface a placeholder result so E2E and users see progress
      setLastResult((prev) => ({ ...prev, [templateId]: { status: "queued", state: "PENDING" } }));
      const r = await fetch(`/api/personal/run/${templateId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...buildAuthHeaders() },
        body: JSON.stringify(parameters),
      }).then((x) => x.json());
      // Best-effort: record immediate ack
      setLastResult((prev) => ({ ...prev, [templateId]: r }));
      const taskId = r?.task_id;
      if (taskId && typeof window !== "undefined") {
        try {
          const es = new EventSource(sseUrl(`/api/personal/stream/${taskId}`));
          es.onmessage = (evt) => {
            const data = JSON.parse(evt.data);
            setLastResult((prev) => ({ ...prev, [templateId]: data }));
            if (data?.status === "completed" || data?.status === "error") {
              es.close();
            }
          };
          es.onerror = () => {
            es.close();
          };
        } catch (e) {
          // Fallback to polling on SSE failure
          for (let i = 0; i < 20; i++) {
            await new Promise((res) => setTimeout(res, 1500));
            const s = await fetch(`/api/personal/result/${taskId}`, { headers: buildAuthHeaders() }).then((x) => x.json());
            if (s?.status === "completed" || s?.status === "error") {
              setLastResult((prev) => ({ ...prev, [templateId]: s }));
              break;
            }
          }
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRunning((r) => ({ ...r, [templateId]: false }));
    }
  };

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
          {config && (
            <div className="text-xs text-gray-600 mt-2">
              Social enabled: Twitter {config.twitter_enabled ? 'on' : 'off'} · LinkedIn {config.linkedin_enabled ? 'on' : 'off'} · Real posting {config.post_real_enabled ? 'on' : 'off'}
            </div>
          )}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Connect Accounts</div>
          <div className="text-sm text-gray-700">Twitter: {oauthStatus.twitter ? 'connected' : 'not connected'}</div>
          {config?.oauth?.twitter && (
            <div className="flex items-center gap-3 mt-1">
              <a className="underline text-blue-600 text-sm" href="/api/personal/social/oauth/twitter/start">Connect Twitter</a>
              {oauthStatus.twitter && (
                <button
                  className="text-sm text-red-600 underline"
                  onClick={async () => {
                     await fetch(`/api/personal/social/oauth/twitter`, { method: 'DELETE', headers: buildAuthHeaders() });
                     const s = await fetch(`/api/personal/social/oauth/status`, { headers: buildAuthHeaders() }).then((x) => x.json());
                    setOauthStatus(s);
                  }}
                >Disconnect</button>
              )}
            </div>
          )}
          <div className="text-sm text-gray-700 mt-2">LinkedIn: {oauthStatus.linkedin ? 'connected' : 'not connected'}</div>
          {config?.oauth?.linkedin && (
            <div className="flex items-center gap-3 mt-1">
              <a className="underline text-blue-600 text-sm" href="/api/personal/social/oauth/linkedin/start">Connect LinkedIn</a>
              {oauthStatus.linkedin && (
                <button
                  className="text-sm text-red-600 underline"
                  onClick={async () => {
                     await fetch(`/api/personal/social/oauth/linkedin`, { method: 'DELETE', headers: buildAuthHeaders() });
                     const s = await fetch(`/api/personal/social/oauth/status`, { headers: buildAuthHeaders() }).then((x) => x.json());
                    setOauthStatus(s);
                  }}
                >Disconnect</button>
              )}
            </div>
          )}
        </div>
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Recent Personal Runs</div>
          {!recentRuns.length && <div className="text-sm text-gray-600">No runs yet.</div>}
          {!!recentRuns.length && (
            <ul className="space-y-2">
              {recentRuns.map((r) => (
                <li key={r.id} className="text-sm flex items-center justify-between">
                  <div>
                    <div className="font-mono text-xs">{r.template_id}</div>
                    <div className={`text-xs ${r.status === 'completed' ? 'text-green-600' : r.status === 'error' ? 'text-red-600' : 'text-gray-600'}`}>{r.status}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      className="underline text-blue-600 text-xs"
                      onClick={() => followRun(r.task_id, r.template_id)}
                      title="Stream live updates"
                    >View live</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="border rounded p-4 bg-white col-span-1 md:col-span-2">
          <div className="font-medium mb-2">Quick Social Post</div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">Post Text</label>
            <textarea className="w-full border rounded p-2 text-sm" rows={3} value={postText} onChange={(e) => setPostText(e.target.value)} placeholder="Write your post..." />
            <label className="block text-sm font-medium">Platforms (comma-separated)</label>
            <input className="w-full border rounded p-2 text-sm" value={postPlatforms} onChange={(e) => setPostPlatforms(e.target.value)} placeholder="twitter,linkedin" />
            <div>
              <button
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
                onClick={() =>
                  runPersonalAutomation("social_media_manager", {
                    text: postText,
                    platforms: postPlatforms.split(",").map((s) => s.trim()).filter(Boolean),
                    post_now: false,
                  })
                }
              >
                Draft
              </button>
              <button
                className="bg-green-600 text-white px-3 py-1 rounded text-sm ml-2"
                onClick={() =>
                  runPersonalAutomation("social_media_manager", {
                    text: postText,
                    platforms: postPlatforms.split(",").map((s) => s.trim()).filter(Boolean),
                    post_now: true,
                  })
                }
              >
                Post (if enabled)
              </button>
            </div>
          </div>
          {lastResult["social_media_manager"] && (
            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult["social_media_manager"], null, 2)}</pre>
          )}
        </div>
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Research Assistant</div>
          <label className="block text-sm font-medium">Topic</label>
          <input
            className="w-full border rounded p-2 text-sm"
            value={researchTopic}
            onChange={(e) => setResearchTopic(e.target.value)}
            placeholder="AI automation trends"
            data-testid="research-topic"
          />
          <div className="mt-2">
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
              onClick={() => runPersonalAutomation("research_assistant", { topic: researchTopic })}
              disabled={!!running["research_assistant"]}
              data-testid="research-assistant-run"
            >Run</button>
          </div>
          <pre data-testid="research-results" className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult["research_assistant"] || { status: running["research_assistant"] ? "queued" : "idle" }, null, 2)}</pre>
          {lastResult["research_assistant"]?.result?.research_data && Array.isArray(lastResult["research_assistant"].result.research_data) && (
            <div className="mt-2 overflow-x-auto">
              <table className="min-w-full text-xs border">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-2 py-1 text-left border">Title</th>
                    <th className="px-2 py-1 text-left border">Authors</th>
                    <th className="px-2 py-1 text-left border">Year</th>
                    <th className="px-2 py-1 text-left border">Citations</th>
                  </tr>
                </thead>
                <tbody>
                  {lastResult["research_assistant"].result.research_data.slice(0, 10).map((r: any, i: number) => (
                    <tr key={i} className="odd:bg-white even:bg-gray-50">
                      <td className="px-2 py-1 border truncate max-w-[260px]" title={r.title || ""}>{r.title || "—"}</td>
                      <td className="px-2 py-1 border truncate max-w-[200px]" title={(r.authors || []).join?.(", ")}>{Array.isArray(r.authors) ? r.authors.join(", ") : (r.authors || "—")}</td>
                      <td className="px-2 py-1 border">{r.year || "—"}</td>
                      <td className="px-2 py-1 border">{r.citations ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Shopping Assistant</div>
          <label className="block text-sm font-medium">Product Query</label>
          <input
            className="w-full border rounded p-2 text-sm"
            value={shopQuery}
            onChange={(e) => setShopQuery(e.target.value)}
            placeholder="laptop under $1000"
          />
          <label className="block text-sm font-medium mt-2">Max Results</label>
          <input
            type="number"
            className="w-full border rounded p-2 text-sm"
            value={shopMax}
            onChange={(e) => setShopMax(Number(e.target.value || 0))}
            placeholder="20"
          />
          <div className="mt-2">
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
              onClick={() => runPersonalAutomation("shopping_assistant", { product_query: shopQuery, max_results: shopMax })}
              disabled={!!running["shopping_assistant"]}
            >Run</button>
          </div>
          {lastResult["shopping_assistant"] && (
            <>
              <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult["shopping_assistant"], null, 2)}</pre>
              {lastResult["shopping_assistant"].result?.products && Array.isArray(lastResult["shopping_assistant"].result.products) && (
                <div className="mt-2 overflow-x-auto">
                  <table className="min-w-full text-xs border">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-2 py-1 text-left border">Name</th>
                        <th className="px-2 py-1 text-left border">Price</th>
                        <th className="px-2 py-1 text-left border">Rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lastResult["shopping_assistant"].result.products.slice(0, 10).map((p: any, i: number) => (
                        <tr key={i} className="odd:bg-white even:bg-gray-50">
                          <td className="px-2 py-1 border truncate max-w-[260px]" title={p.name || ""}>{p.name || "—"}</td>
                          <td className="px-2 py-1 border">{typeof p.price === "number" ? `$${p.price.toFixed(2)}` : (p.price || "—")}</td>
                          <td className="px-2 py-1 border">{p.rating ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Quick Email Sweep</div>
          <label className="block text-sm font-medium">Query</label>
          <div className="flex gap-2">
            <input className="w-full border rounded p-2 text-sm" value={emailQuery} onChange={(e) => setEmailQuery(e.target.value)} placeholder="newer_than:1d" />
            <select
              className="border rounded p-2 text-sm"
              onChange={(e) => setEmailQuery(e.target.value)}
              value={emailQuery}
              title="Presets"
            >
              <option value="newer_than:1d">Last day</option>
              <option value="newer_than:7d">Last week</option>
              <option value="from:billing OR subject:invoice newer_than:30d">Bills & invoices (30d)</option>
              <option value="label:news newer_than:14d">Newsletters (14d)</option>
            </select>
          </div>
          <label className="block text-sm font-medium mt-2">Max Results</label>
          <input type="number" className="w-full border rounded p-2 text-sm" value={emailMax} onChange={(e) => setEmailMax(Number(e.target.value || 0))} placeholder="50" />
          <div className="mt-2">
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
              onClick={() => runPersonalAutomation("personal_email_manager", { query: emailQuery, max_results: emailMax })}
              disabled={!!running["personal_email_manager"]}
            >Run</button>
          </div>
          {lastResult["personal_email_manager"] && (
            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult["personal_email_manager"], null, 2)}</pre>
          )}
        </div>
        <div className="border rounded p-4 bg-white">
          <div className="font-medium mb-2">Finance Update</div>
          <div className="text-sm text-gray-700">Fetch and summarize latest finance data</div>
          <div className="mt-2">
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
              onClick={() => runPersonalAutomation("personal_finance_tracker", {})}
              disabled={!!running["personal_finance_tracker"]}
            >Run</button>
          </div>
          <div className="mt-3">
            <div className="text-sm font-medium">Import CSV</div>
            <label className="block text-sm font-medium">Upload Transactions CSV</label>
            <input
              type="file"
              accept=".csv"
              className="text-sm"
              title="Choose a CSV file to import transactions"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                const body = new FormData();
                body.append("file", f);
                 const res = await fetch(`/api/personal/finance/import_csv`, { method: "POST", body });
                const data = await res.json();
                setLastResult((prev) => ({ ...prev, finance_csv: data }));
              }}
            />
          </div>
          {lastResult["personal_finance_tracker"] && (
            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult["personal_finance_tracker"], null, 2)}</pre>
          )}
          {lastResult["finance_csv"] && (
            <>
              <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult["finance_csv"], null, 2)}</pre>
              {lastResult["finance_csv"].per_category && (
                <div className="mt-2 overflow-x-auto">
                  <table className="min-w-full text-xs border">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-2 py-1 text-left border">Category</th>
                        <th className="px-2 py-1 text-left border">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(lastResult["finance_csv"].per_category).map(([cat, total]: any, i: number) => (
                        <tr key={i} className="odd:bg-white even:bg-gray-50">
                          <td className="px-2 py-1 border">{cat}</td>
                          <td className="px-2 py-1 border">{typeof total === "number" ? `$${total.toFixed(2)}` : total}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
        {widgets.map((w) => (
          <div key={w.automation} className="border rounded p-4 bg-white">
            <div className="font-medium">{w.title}</div>
            <div className="text-sm text-gray-700">{w.data}</div>
            <div className="mt-2">
              <a className="underline text-sm" href={`/templates/${w.automation}`}>Open</a>
            </div>
            <div className="mt-2">
              <button
                onClick={() => runPersonalAutomation(w.automation, w.automation === 'research_assistant' ? { topic: 'AI automation trends' } : {})}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
                disabled={!!running[w.automation]}
              >
                {running[w.automation] ? 'Running…' : 'Run Now'}
              </button>
            </div>
            {lastResult[w.automation] && (
              <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(lastResult[w.automation], null, 2)}</pre>
            )}
          </div>
        ))}
      </div>
      {summary && (
        <div className="text-xs text-gray-600">Today: Started {summary.tasks_started} · p95 {summary.p95_ms ?? "-"} ms</div>
      )}
    </section>
  );
}


