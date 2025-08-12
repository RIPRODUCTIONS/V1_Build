'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { apiFetch, LeadOut } from '@/lib/api';

export default function LeadsListPage() {
  const _router = useRouter();
  const [q, setQ] = useState('');
  const [sort, setSort] = useState('created_desc');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['leads', { q, sort }],
    queryFn: async (): Promise<LeadOut[]> => {
      const params = new URLSearchParams();
      if (q) params.set('q', q);
      if (sort) params.set('sort', sort);
      return apiFetch<LeadOut[]>(`/leads?${params.toString()}`);
    },
  });

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <Link
          href="/leads/create"
          className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
        >
          Create Lead
        </Link>
      </div>
      <div className="flex gap-3 items-center">
        <input
          className="border rounded px-3 py-2"
          placeholder="Search leads"
          value={q}
          onChange={e => setQ(e.target.value)}
        />
        <select
          className="border rounded px-3 py-2"
          value={sort}
          onChange={e => setSort(e.target.value)}
        >
          <option value="created_desc">Newest</option>
          <option value="name_asc">Name A→Z</option>
        </select>
      </div>

      {isLoading && <p>Loading…</p>}
      {isError && <p className="text-red-600">Failed to load leads</p>}
      {data && (
        <ul className="space-y-2">
          {data.map(l => (
            <li
              key={l.id}
              className="p-3 rounded border bg-white flex items-center justify-between"
            >
              <div>
                <div className="font-medium">{l.name}</div>
                <div className="text-sm text-gray-500">{l.email}</div>
              </div>
              <Link className="text-blue-600 hover:underline" href={`/leads/${l.id}`}>
                View
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
