'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { apiFetch, TaskOut } from '@/lib/api';

export default function TasksQueuePage() {
  const [q, setQ] = useState('');
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [sort, setSort] = useState('created_desc');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['tasks', { q, status, sort }],
    queryFn: async (): Promise<TaskOut[]> => {
      const params = new URLSearchParams();
      if (q) params.set('q', q);
      if (status) params.set('status_filter', status);
      if (sort) params.set('sort', sort);
      return apiFetch<TaskOut[]>(`/tasks?${params.toString()}`);
    },
  });

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Tasks</h1>
      <div className="flex gap-3 items-center">
        <input
          className="border rounded px-3 py-2"
          placeholder="Search tasks"
          value={q}
          onChange={e => setQ(e.target.value)}
        />
        <select
          className="border rounded px-3 py-2"
          value={status ?? ''}
          onChange={e => setStatus(e.target.value || undefined)}
        >
          <option value="">All</option>
          <option value="todo">Todo</option>
          <option value="doing">Doing</option>
          <option value="done">Done</option>
        </select>
        <select
          className="border rounded px-3 py-2"
          value={sort}
          onChange={e => setSort(e.target.value)}
        >
          <option value="created_desc">Newest</option>
          <option value="title_asc">Title A→Z</option>
          <option value="title_desc">Title Z→A</option>
        </select>
      </div>

      {isLoading && <p>Loading…</p>}
      {isError && <p className="text-red-600">Failed to load tasks</p>}
      {data && (
        <ul className="space-y-2">
          {data.map(t => (
            <li key={t.id} className="p-3 rounded border bg-white">
              <div className="font-medium">{t.title}</div>
              <div className="text-sm text-gray-500">{t.status}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
