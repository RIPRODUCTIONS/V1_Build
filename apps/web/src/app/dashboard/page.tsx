"use client";
import Link from "next/link";
import { useState, useMemo } from "react";
import { apiFetch } from "@/lib/api";
import { usePagedList } from "@/hooks/usePagedList";
import { useToast } from "@/components/ToastProvider";

type Lead = { id: string; name: string; email: string; created_at: string };
type Task = { id: string; title: string; status: string; created_at: string };

export default function Dashboard() {
  const { show } = useToast();
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
    </section>
  );
}
