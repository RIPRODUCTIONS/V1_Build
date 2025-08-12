'use client';

import { useState } from 'react';

import { useDeleteRun } from '@/hooks/useDeleteRun';
import { useRuns } from '@/hooks/useRuns';
import { useUpdateRun } from '@/hooks/useUpdateRun';

import CreateRunClientForm from './CreateRunClientForm';

export default function RunsClient() {
  const [page, setPage] = useState(1);
  const result = useRuns({ page, pageSize: 10 });
  const data = result.data;
  const isLoading = result.isLoading;
  const error = result.error;
  const items = data?.data ?? [];
  const isPaged = data?.kind === 'page';
  const total = isPaged ? (data as { total: number }).total : items.length;
  return (
    <>
      <CreateRunClientForm />
      {isLoading && <p>Loading runs…</p>}
      {error && <p>Failed to load runs.</p>}
      <ul className="space-y-2 mt-4">
        {(items as Array<{ id: string; title: string; status: string }>)?.map(run => (
          <RunItem key={run.id} id={run.id} title={run.title} status={run.status} />
        ))}
      </ul>
      {isPaged && (
        <div className="mt-4 flex items-center gap-2">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)} aria-label="Prev page">
            Prev
          </button>
          <span>Page {page}</span>
          <button
            disabled={(items.length ?? 0) < 10}
            onClick={() => setPage(p => p + 1)}
            aria-label="Next page"
          >
            Next
          </button>
          <span className="ml-2 text-sm text-neutral-500">{total} total</span>
        </div>
      )}
    </>
  );
}

function RunItem({ id, title, status }: { id: string; title: string; status: string }) {
  const upd = useUpdateRun(id);
  const del = useDeleteRun(id);
  return (
    <li className="rounded border p-3 flex items-center gap-3">
      <div className="flex-1">
        <div className="font-mono text-sm">{id}</div>
        <div className="text-sm">Status: {status}</div>
        <div className="text-sm">Title: {title}</div>
      </div>
      <button
        className="border rounded px-2 py-1"
        onClick={() => upd.mutate({ title: title + ' ✏️' })}
      >
        Rename
      </button>
      <button
        className="border rounded px-2 py-1"
        onClick={() => upd.mutate({ status: 'running' })}
      >
        Run ▶
      </button>
      <button
        className="border rounded px-2 py-1"
        onClick={() => del.mutate()}
        aria-label={`delete-${id}`}
      >
        Delete
      </button>
    </li>
  );
}
