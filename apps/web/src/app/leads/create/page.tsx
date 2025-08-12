'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { apiFetch } from '@/lib/api';

type CreateLeadBody = { name: string; email?: string; notes?: string };

export default function CreateLeadPage() {
  const router = useRouter();
  const [form, setForm] = useState<CreateLeadBody>({ name: '', email: '', notes: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRun, setAutoRun] = useState(true);
  const [scheduleTask, setScheduleTask] = useState(true);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const created = await apiFetch<{ id: number }>(`/leads/`, {
        method: 'POST',
        body: JSON.stringify({
          name: form.name,
          email: form.email || undefined,
          notes: form.notes || undefined,
        }),
      });

      const leadId = created.id;

      if (autoRun) {
        // Kick off agent summarize + email generation
        await apiFetch<{ run_id: number }>(`/agent/run`, {
          method: 'POST',
          body: JSON.stringify({ lead_id: leadId, context: form.notes || '' }),
        }).catch(() => void 0);
      }

      if (scheduleTask) {
        await apiFetch<{ id: number }>(`/tasks/`, {
          method: 'POST',
          body: JSON.stringify({ title: `Send follow-up email to ${form.name}` }),
        }).catch(() => void 0);
      }

      router.replace(`/leads/${leadId}`);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to create lead';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="p-6 max-w-xl">
      <h1 className="text-2xl font-semibold mb-4">Create Lead</h1>
      {error && <p className="text-red-600 mb-3">{error}</p>}
      <form onSubmit={onSubmit} className="space-y-3">
        <input
          className="border rounded px-3 py-2 w-full"
          placeholder="Name"
          value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          required
        />
        <input
          className="border rounded px-3 py-2 w-full"
          placeholder="Email (optional)"
          type="email"
          value={form.email}
          onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
        />
        <textarea
          className="border rounded px-3 py-2 w-full"
          placeholder="Notes (optional)"
          value={form.notes}
          onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
        />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={autoRun} onChange={e => setAutoRun(e.target.checked)} />
          Auto-summarize + draft email via Agent
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={scheduleTask}
            onChange={e => setScheduleTask(e.target.checked)}
          />
          Schedule follow-up task
        </label>
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </main>
  );
}
