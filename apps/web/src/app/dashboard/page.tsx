"use client";
import Link from "next/link";
import React, { useState, useMemo } from "react";
import { apiFetch } from "@/lib/api";
import { usePagedList } from "@/hooks/usePagedList";
import { useToast } from "@/components/ToastProvider";

type Lead = { id: string; name: string; email: string; created_at: string };
type Task = { id: string; title: string; status: string; created_at: string };

export default function Dashboard() {
  const { show } = useToast();
  const [roi, setRoi] = useState<{ hourly_rate: number; roi: { id: string; name: string; estimated_cost_savings_usd: number }[] } | null>(null);
  // Filters
  const [leadQuery, setLeadQuery] = useState("");
  const [leadStatus, setLeadStatus] = useState<string | undefined>(undefined);
  const [leadSort, setLeadSort] = useState("created_desc");

  const [taskQuery, setTaskQuery] = useState("");
  const [taskStatus, setTaskStatus] = useState<string | undefined>(undefined);
  const [taskSort, setTaskSort] = useState("created_desc");

  // Query builders
  const leadParams = useMemo(
    () => ({
      q: leadQuery || undefined,
      status_filter: leadStatus || undefined,
      sort: leadSort,
      limit: 20,
    }),
    [leadQuery, leadStatus, leadSort]
  );

  const taskParams = useMemo(
    () => ({
      q: taskQuery || undefined,
      status_filter: taskStatus || undefined,
      sort: taskSort,
      limit: 20,
    }),
    [taskQuery, taskStatus, taskSort]
  );

  // usePagedList wires IntersectionObserver pagination
  const {
    items: leads,
    loadingMore: loadingMoreLeads,
    error: leadError,
    sentinelRef: leadSentinelRef,
    reset: resetLeads,
  } = usePagedList<Lead>({
    key: ["leads", leadParams],
    fetchPage: async ({ offset, limit }) => {
      const search = new URLSearchParams({
        ...(leadParams.q ? { q: leadParams.q } : {}),
        ...(leadParams.status_filter ? { status_filter: leadParams.status_filter } : {}),
        sort: leadParams.sort ?? "created_desc",
        limit: String(limit),
        offset: String(offset),
      });
      return apiFetch<Lead[]>(`/leads?${search.toString()}`);
    },
  });

  const {
    items: tasks,
    loadingMore: loadingMoreTasks,
    error: taskError,
    sentinelRef: taskSentinelRef,
    reset: resetTasks,
  } = usePagedList<Task>({
    key: ["tasks", taskParams],
    fetchPage: async ({ offset, limit }) => {
      const search = new URLSearchParams({
        ...(taskParams.q ? { q: taskParams.q } : {}),
        ...(taskParams.status_filter ? { status_filter: taskParams.status_filter } : {}),
        sort: taskParams.sort ?? "created_desc",
        limit: String(limit),
        offset: String(offset),
      });
      return apiFetch<Task[]>(`/tasks?${search.toString()}`);
    },
  });

  // Filter handlers reset pagination and show toast
  const onLeadFilterChange = () => { resetLeads(); show("Filters applied", "success"); };
  const onTaskFilterChange = () => { resetTasks(); show("Filters applied", "success"); };

  return (
    <section className="space-y-6 p-6">
      <div className="p-3 rounded border bg-white">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-medium">Automation ROI</h2>
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const base = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
                const r = await fetch(`${base}/admin/templates/roi`, { headers: { 'X-CI-Token': (typeof window!=='undefined' ? localStorage.getItem('ci_token')||'' : '') } });
                if (!r.ok) throw new Error('roi');
                const data = await r.json();
                setRoi(data);
                show('ROI refreshed', 'success');
              } catch {
                show('ROI fetch failed', 'error');
              }
            }}
          >Refresh</button>
        </div>
        {roi && (
          <div className="mt-2 text-sm">
            Hourly rate: $ {roi.hourly_rate} /hr · Total savings: $ {roi.roi.reduce((a, x)=>a+(x.estimated_cost_savings_usd||0),0).toFixed(2)}
          </div>
        )}
      </div>
      <div>
        <h2 className="text-xl font-medium mb-2">Leads</h2>

        <div className="flex items-center gap-2 mb-3">
          <input
            aria-label="Leads search"
            className="border px-2 py-1 rounded"
            placeholder="Search leads…"
            value={leadQuery}
            onChange={(e) => { setLeadQuery(e.target.value); onLeadFilterChange(); }}
          />
          <label htmlFor="lead-status" className="sr-only">Status</label>
          <select
            id="lead-status"
            aria-label="Status"
            className="border px-2 py-1 rounded"
            value={leadStatus ?? ""}
            onChange={(e) => { setLeadStatus(e.target.value || undefined); onLeadFilterChange(); }}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="won">Won</option>
            <option value="lost">Lost</option>
          </select>

          <label htmlFor="lead-sort" className="sr-only">Sort</label>
          <select
            id="lead-sort"
            aria-label="Sort"
            className="border px-2 py-1 rounded"
            value={leadSort}
            onChange={(e) => { setLeadSort(e.target.value); onLeadFilterChange(); }}
          >
            <option value="created_desc">Newest</option>
            <option value="created_asc">Oldest</option>
            <option value="name_asc">Name A–Z</option>
            <option value="name_desc">Name Z–A</option>
          </select>
        </div>

        <ul className="space-y-2">
          {leads.map((l) => (
            <li key={l.id} className="p-3 rounded border bg-white">
              <div className="font-medium">{l.name}</div>
              <div className="text-sm text-gray-600">{l.email}</div>
              <Link className="text-blue-600 text-sm" href={`/leads/${l.id}`}>Edit</Link>
            </li>
          ))}
        </ul>

        {leadError && <div className="text-red-600 mt-2">Failed to load leads.</div>}
        {!leadError && leads.length === 0 && !loadingMoreLeads && (
          <div className="text-gray-600 mt-2">No leads found.</div>
        )}
        <div ref={leadSentinelRef} className="h-6" />
        {loadingMoreLeads && (
          <div role="status" className="mt-2 animate-pulse text-gray-600">Loading more leads…</div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Tasks</h2>

        <div className="flex items-center gap-2 mb-3">
          <input
            aria-label="Tasks search"
            className="border px-2 py-1 rounded"
            placeholder="Search tasks…"
            value={taskQuery}
            onChange={(e) => { setTaskQuery(e.target.value); onTaskFilterChange(); }}
          />
          <label htmlFor="task-status" className="sr-only">Status</label>
          <select
            id="task-status"
            aria-label="Status"
            className="border px-2 py-1 rounded"
            value={taskStatus ?? ""}
            onChange={(e) => { setTaskStatus(e.target.value || undefined); onTaskFilterChange(); }}
          >
            <option value="">All statuses</option>
            <option value="todo">Todo</option>
            <option value="doing">Doing</option>
            <option value="done">Done</option>
          </select>

          <label htmlFor="task-sort" className="sr-only">Sort</label>
          <select
            id="task-sort"
            aria-label="Sort"
            className="border px-2 py-1 rounded"
            value={taskSort}
            onChange={(e) => { setTaskSort(e.target.value); onTaskFilterChange(); }}
          >
            <option value="created_desc">Newest</option>
            <option value="created_asc">Oldest</option>
            <option value="title_asc">Title A–Z</option>
            <option value="title_desc">Title Z–A</option>
          </select>
        </div>

        <ul className="space-y-2">
          {tasks.map((t) => (
            <li key={t.id} className="p-3 rounded border bg-white">
              <div className="font-medium">{t.title}</div>
              <div className="text-sm text-gray-600">{t.status}</div>
              <Link className="text-blue-600 text-sm" href={`/tasks/${t.id}`}>Edit</Link>
            </li>
          ))}
        </ul>

        {taskError && <div className="text-red-600 mt-2">Failed to load tasks.</div>}
        {!taskError && tasks.length === 0 && !loadingMoreTasks && (
          <div className="text-gray-600 mt-2">No tasks found.</div>
        )}
        <div ref={taskSentinelRef} className="h-6" />
        {loadingMoreTasks && (
          <div role="status" className="mt-2 animate-pulse text-gray-600">Loading more tasks…</div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Finance</h2>
        <div className="flex items-center gap-2 mb-3">
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/finance/pay_bill", {
                  method: "POST",
                  body: JSON.stringify({
                    vendor: "Acme Cloud",
                    amount: 123.45,
                    memo: "Test payment",
                  }),
                });
                show(`Finance run queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue finance run", "error");
              }
            }}
          >
            Run: Pay Bill (demo)
          </button>
          <Link className="text-blue-600 text-sm" href="/automation">View runs</Link>
        </div>
      </div>

      <RecentRuns />
      <RecentTemplateUsage />

      <div>
        <h2 className="text-xl font-medium mb-2">Ideation</h2>
        <div className="flex items-center gap-2 mb-3">
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/ideation/generate", {
                  method: "POST",
                  body: JSON.stringify({ topic: "automation business engine", count: 5 }),
                });
                show(`Ideation run queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue ideation run", "error");
              }
            }}
          >
            Generate Ideas (demo)
          </button>
          <Link className="text-blue-600 text-sm" href="/automation">View runs</Link>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Relationship</h2>
        <div className="flex items-center gap-2 mb-3">
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/relationship/openers", {
                  method: "POST",
                  body: JSON.stringify({
                    interests: ["hiking", "coffee"],
                    profile_bio: "love weekend trips",
                    tone: "playful",
                    count: 5,
                  }),
                });
                show(`Openers run queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue openers run", "error");
              }
            }}
          >
            Generate Openers (demo)
          </button>
          <Link className="text-blue-600 text-sm" href="/automation">View runs</Link>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Business</h2>
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/business/marketing/launch", {
                  method: "POST",
                  body: JSON.stringify({ campaign_name: "Q4 Launch", channels: ["email", "social"] }),
                });
                show(`Marketing launch queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue marketing launch", "error");
              }
            }}
          >
            Launch Marketing (demo)
          </button>
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/business/sales/outreach", {
                  method: "POST",
                  body: JSON.stringify({ leads: ["lead@example.com"], template: "Hi {{name}}, quick intro…" }),
                });
                show(`Sales outreach queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue sales outreach", "error");
              }
            }}
          >
            Sales Outreach (demo)
          </button>
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/business/ops/brief", {
                  method: "POST",
                });
                show(`Ops brief queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue ops brief", "error");
              }
            }}
          >
            Ops Brief (demo)
          </button>
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/business/simulate_cycle", {
                  method: "POST",
                  body: JSON.stringify({ topic: "autonomous business engine", count: 5 }),
                });
                show(`Cycle run queued: ${res.run_id}`, "success");
              } catch {
                show("Failed to enqueue cycle run", "error");
              }
            }}
          >
            Simulate Business Cycle (demo)
          </button>
          <Link className="text-blue-600 text-sm" href="/automation">View runs</Link>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Communication</h2>
        <div className="flex items-center gap-2 mb-3">
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ reply: string }>("/comm/auto_reply", {
                  method: "POST",
                  body: JSON.stringify({ channel: "email", body: "Can we schedule a meeting next week?" }),
                });
                show(res.reply, "success");
              } catch {
                show("Auto-reply failed", "error");
              }
            }}
          >
            Test Auto-Reply (demo)
          </button>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Documents</h2>
        <div className="flex items-center gap-2 mb-3">
          <button
            className="border px-3 py-1 rounded"
            onClick={async () => {
              try {
                const res = await apiFetch<{ run_id: string; status: string }>("/documents/ingest_scan", {
                  method: "POST",
                  body: JSON.stringify({ files: ["/tmp/sample1.png", "/tmp/sample2.pdf"] }),
                });
                show(`Docs ingest queued: ${res.run_id}`, "success");
              } catch {
                show("Docs ingest failed", "error");
              }
            }}
          >
            Ingest & Scan (demo)
          </button>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-medium mb-2">Life Automation</h2>
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          {[
            { path: "/life/health/wellness", label: "Wellness Daily" },
            { path: "/life/nutrition/plan", label: "Nutrition Plan" },
            { path: "/life/home/evening", label: "Home Evening" },
            { path: "/life/transport/commute", label: "Commute" },
            { path: "/life/learning/upskill", label: "Upskill" },
            { path: "/life/finance/investments", label: "Finance Investments" },
            { path: "/life/finance/bills", label: "Finance Bills" },
            { path: "/life/security/sweep", label: "Security Sweep" },
            { path: "/life/travel/plan", label: "Travel Plan" },
            { path: "/life/calendar/organize", label: "Calendar Organize" },
            { path: "/life/shopping/optimize", label: "Shopping Optimize" },
          ].map((a) => (
            <button
              key={a.path}
              className="border px-3 py-1 rounded"
              onClick={async () => {
                try {
                  const res = await apiFetch<{ run_id: string; status: string }>(a.path, {
                    method: "POST",
                    body: JSON.stringify({}),
                  });
                  show(`${a.label} queued: ${res.run_id}`, "success");
                } catch {
                  show(`${a.label} failed`, "error");
                }
              }}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function RecentRuns() {
  const [items, setItems] = useState<{ run_id: string; status: string; meta?: any; detail?: any }[]>([]);
  const { show } = useToast();
  const load = React.useCallback(async () => {
    try {
      const res = await apiFetch<{ items: any[] }>("/automation/recent");
      setItems(res.items ?? []);
    } catch {
      show("Failed to load recent runs", "error");
    }
  }, [show]);
  // simple poll
  React.useEffect(() => {
    load();
    const t = setInterval(load, 3500);
    return () => clearInterval(t);
  }, [load]);
  if (!items.length) return null;
  return (
    <div>
      <h2 className="text-xl font-medium mb-2">Recent Runs</h2>
      <ul className="space-y-2">
        {items.slice(0, 10).map((it) => (
          <li key={it.run_id} className="p-3 rounded border bg-white">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm">{it.run_id}</span>
              <span className="text-sm">{it.status}</span>
            </div>
            <div className="text-xs text-gray-600">
              {it?.meta?.intent} {it?.detail?.executed ? `— ${it.detail.executed.join(" → ")}` : ""}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RecentTemplateUsage() {
  const [items, setItems] = useState<{ template_id: string; queued_tasks: number; success: boolean; created_at: string }[]>([]);
  const { show } = useToast();
  const load = React.useCallback(async () => {
    try {
      const res = await apiFetch<{ items: any[] }>(`/templates/usage?limit=10`);
      setItems(res.items ?? []);
    } catch {
      show("Failed to load template usage", "error");
    }
  }, [show]);
  React.useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);
  if (!items.length) return null;
  return (
    <div>
      <h2 className="text-xl font-medium mb-2">Recent Template Usage</h2>
      <ul className="space-y-2">
        {items.map((it, idx) => (
          <li key={`${it.template_id}-${idx}-${it.created_at}`} className="p-3 rounded border bg-white">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm">{it.template_id}</span>
              <span className="text-sm">{new Date(it.created_at).toLocaleString()}</span>
            </div>
            <div className="text-xs text-gray-600">Queued: {it.queued_tasks} · {it.success ? "ok" : "failed"}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
