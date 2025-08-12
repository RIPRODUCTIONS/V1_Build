'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import type { RunStatus } from '@/lib/automation';
import { listRuns, runLink, RunSummary } from '@/lib/automation';

type Props = { defaultIntent?: string };

const STATUS_COLORS: Record<string, string> = {
  succeeded: 'text-emerald-600 border-emerald-300',
  failed: 'text-rose-600 border-rose-300',
  running: 'text-sky-600 border-sky-300',
  queued: 'text-amber-600 border-amber-300',
};

const LS_KEY = 'recentRuns.filters.v1';

export default function RecentRunsPanel({ defaultIntent }: Props) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const sp = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const abortRef = useRef<AbortController | null>(null);

  const [filters, setFilters] = useState<{
    intent?: string;
    status?: string;
    from?: string;
    to?: string;
  }>(() => {
    try {
      return JSON.parse(localStorage.getItem(LS_KEY) || '{}');
    } catch {
      return {};
    }
  });

  useEffect(() => {
    localStorage.setItem(LS_KEY, JSON.stringify(filters));
  }, [filters]);

  const intent = filters.intent ?? defaultIntent;

  async function fetchPage(reset = false) {
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    setLoading(true);
    setError(null);
    try {
      const page = await listRuns(
        {
          intent,
          status: filters.status as RunStatus | undefined,
          from: filters.from,
          to: filters.to,
          limit: 25,
          cursor: reset ? undefined : (cursor ?? undefined),
        },
        abortRef.current.signal,
      );
      setRuns(prev => (reset ? page : [...prev, ...page]));
      if (page.length) {
        const last = page[page.length - 1];
        setCursor(`${last.created_at}|${last.id}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg ?? 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  }

  // Auto-refresh every 10s (restart when filters change)
  useEffect(() => {
    fetchPage(true);
    const id = setInterval(() => fetchPage(true), 10000);
    return () => {
      clearInterval(id);
      abortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intent, filters.status, filters.from, filters.to]);

  // Deep-link: highlight runId from URL
  const selectedId = sp.get('runId');

  function openRun(id: string) {
    router.push(runLink(id, pathname), { scroll: false });
    setExpandedId(prev => (prev === id ? null : id));
  }

  return (
    <section className="mt-8 border rounded-xl p-4 bg-white/60">
      <header className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">Recent Runs</h3>
        <div className="flex gap-2">
          <select
            value={filters.status ?? ''}
            onChange={e => setFilters(f => ({ ...f, status: e.target.value || undefined }))}
            className="border rounded-md px-2 py-1"
            aria-label="Filter by status"
          >
            <option value="">All status</option>
            {['queued', 'running', 'succeeded', 'failed'].map(s => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <input
            placeholder="From (ISO)"
            value={filters.from ?? ''}
            onChange={e => setFilters(f => ({ ...f, from: e.target.value || undefined }))}
            className="border rounded-md px-2 py-1 w-40"
            aria-label="From date"
          />
          <input
            placeholder="To (ISO)"
            value={filters.to ?? ''}
            onChange={e => setFilters(f => ({ ...f, to: e.target.value || undefined }))}
            className="border rounded-md px-2 py-1 w-40"
            aria-label="To date"
          />
        </div>
      </header>

      {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
      <ul className="mt-3 divide-y">
        {runs.map(r => {
          const color = STATUS_COLORS[r.status] ?? 'text-slate-600 border-slate-300';
          const selected = r.id === selectedId;
          return (
            <li key={r.id} className={`py-3 ${selected ? 'bg-slate-50' : ''}`}>
              <button
                onClick={() => openRun(r.id)}
                className="w-full text-left"
                aria-expanded={expandedId === r.id ? 'true' : 'false'}
                aria-controls={`run-${r.id}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs border rounded px-2 py-0.5 ${color}`}>
                      {r.status}
                    </span>
                    <span className="font-medium">{r.intent}</span>
                    <span className="text-xs text-slate-500">
                      {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-slate-500 text-sm">
                    {expandedId === r.id ? 'Hide' : 'Details'}
                  </span>
                </div>
              </button>
              {expandedId === r.id && (
                <div id={`run-${r.id}`} className="mt-2 rounded-md border p-3 bg-white">
                  <pre className="text-xs overflow-auto max-h-64">
                    {JSON.stringify(r.detail ?? {}, null, 2)}
                  </pre>
                </div>
              )}
            </li>
          );
        })}
      </ul>

      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={() => fetchPage(false)}
          disabled={loading}
          className="px-3 py-1 border rounded-md"
        >
          {loading ? 'Loading…' : 'Load more'}
        </button>
        <span className="text-xs text-slate-500" aria-live="polite">
          Showing {runs.length} runs
        </span>
      </div>
    </section>
  );
}
