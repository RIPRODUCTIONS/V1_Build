'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import ConfirmDialog from '@/components/ConfirmDialog';
import { useToast } from '@/components/ToastProvider';
import { apiFetch } from '@/lib/api';
import { components } from '@/lib/api-types';

type LeadOut = components['schemas']['LeadOut'];
type LeadUpdate = components['schemas']['LeadUpdate'];
type AgentRunRequest = components['schemas']['AgentRunRequest'];
type ArtifactOut = components['schemas']['ArtifactOut'] & {
  file_path?: string | null;
  status?: string | null;
};

export default function LeadDetail({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { show } = useToast();

  const {
    data: lead,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['lead', id],
    queryFn: async (): Promise<LeadOut | null> => {
      // Prefer a direct endpoint if present; fallback to listing and filtering
      try {
        return await apiFetch<LeadOut>(`/leads/${id}`);
      } catch {
        const list = await apiFetch<LeadOut[]>(`/leads`);
        return list.find(l => l.id === id) ?? null;
      }
    },
  });

  const [form, setForm] = useState<LeadUpdate>({
    name: undefined,
    email: undefined,
    notes: undefined,
  });
  useEffect(() => {
    if (lead)
      setForm({ name: lead.name, email: lead.email ?? undefined, notes: lead.notes ?? undefined });
  }, [lead]);

  const updateMutation = useMutation({
    mutationFn: async (payload: LeadUpdate) =>
      apiFetch<LeadOut>(`/leads/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lead', id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => apiFetch<void>(`/leads/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      router.replace('/dashboard');
    },
  });

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [pollArtifacts, setPollArtifacts] = useState(false);
  type TimeoutRef = ReturnType<typeof setTimeout>;
  const pollTimerRef = useRef<TimeoutRef | null>(null);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);

  const {
    data: artifacts,
    isFetching: artifactsFetching,
    refetch: refetchArtifacts,
    error: artifactsError,
  } = useQuery({
    queryKey: ['artifacts', runId],
    queryFn: async (): Promise<ArtifactOut[]> => {
      return apiFetch<ArtifactOut[]>(`/agent/artifacts/${runId}`);
    },
    enabled: Boolean(runId),
    refetchInterval: pollArtifacts ? 2000 : false,
    staleTime: 1000,
  });

  async function onSave() {
    updateMutation.mutate(form);
  }

  async function onRunAgent() {
    setAgentLoading(true);
    setAgentError(null);
    try {
      const res = await apiFetch<{ run_id: number }>(`/agent/run`, {
        method: 'POST',
        body: JSON.stringify({ lead_id: id, context: form.notes ?? '' } satisfies AgentRunRequest),
      });
      setRunId(res.run_id);
      setPollArtifacts(true);
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
      pollTimerRef.current = setTimeout(() => setPollArtifacts(false), 20000);
      show('Agent run completed', 'success');
      setAgentStatus('Agent run completed');
      setTimeout(() => setAgentStatus(null), 4000);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setAgentError(message);
      show('Agent run failed', 'error');
    } finally {
      setAgentLoading(false);
    }
  }

  async function onDelete() {
    deleteMutation.mutate();
  }

  if (isLoading) return <main className="p-6">Loading…</main>;
  if (isError || !lead)
    return (
      <main className="p-6">
        {(error as unknown as { message?: string })?.message || 'Failed to load lead'}
      </main>
    );

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Edit Lead</h1>
      {updateMutation.isError && (
        <p className="text-red-600">
          {(updateMutation.error as unknown as { message?: string })?.message ||
            'Failed to update lead'}
        </p>
      )}
      <div className="grid gap-3 max-w-lg">
        <input
          className="border rounded px-3 py-2"
          value={form.name ?? ''}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          placeholder="Name"
        />
        <input
          className="border rounded px-3 py-2"
          value={form.email ?? ''}
          onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
          placeholder="Email"
        />
        <textarea
          className="border rounded px-3 py-2"
          value={form.notes ?? ''}
          onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          placeholder="Notes"
        />
        <div className="flex gap-3">
          <button
            onClick={onSave}
            disabled={updateMutation.isPending}
            className="px-4 py-2 rounded bg-blue-600 text-white"
          >
            {updateMutation.isPending ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={() => setConfirmOpen(true)}
            className="px-4 py-2 rounded bg-red-600 text-white"
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </button>
          <button
            onClick={onRunAgent}
            disabled={agentLoading}
            className="px-4 py-2 rounded bg-green-600 text-white"
          >
            {agentLoading ? 'Running...' : 'Run Agent'}
          </button>
        </div>
      </div>
      {agentError && <p className="text-red-600">{agentError}</p>}
      {agentStatus && (
        <div className="p-2 rounded bg-green-50 text-green-700 border border-green-200">
          {agentStatus}
        </div>
      )}
      {agentLoading && (
        <div className="flex items-center gap-2 text-gray-700">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-transparent" />
          <span>Agent running…</span>
        </div>
      )}
      {runId && (
        <section className="space-y-2">
          <h2 className="text-xl font-medium">Artifacts</h2>
          <div className="flex items-center gap-3">
            <button
              onClick={() => void refetchArtifacts()}
              className="px-3 py-2 rounded border bg-white hover:bg-gray-50"
              disabled={artifactsFetching}
            >
              {artifactsFetching ? 'Refreshing…' : 'Refresh'}
            </button>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={pollArtifacts}
                onChange={e => setPollArtifacts(e.target.checked)}
              />
              Auto-refresh (2s) for 20s
            </label>
          </div>
          {artifactsError && (
            <p className="text-red-600">
              {(artifactsError as unknown as { message?: string })?.message ||
                'Failed to load artifacts'}
            </p>
          )}
          {artifacts && artifacts.length > 0 ? (
            <ul className="space-y-2">
              {artifacts.map(a => (
                <li key={a.id} className="p-3 rounded border bg-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm uppercase text-gray-500">{a.kind}</div>
                      <pre className="whitespace-pre-wrap text-sm">{a.content}</pre>
                    </div>
                    {a.file_path?.startsWith('s3://') && (
                      <a
                        href={`#`}
                        onClick={async e => {
                          e.preventDefault();
                          try {
                            const res = await apiFetch<{ url: string }>(
                              `/agent/artifacts/${a.id}/download`,
                            );
                            window.open(res.url, '_blank');
                          } catch {
                            show('Failed to get download URL', 'error');
                          }
                        }}
                        className="text-blue-600 hover:underline ml-4"
                      >
                        Download
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-600 text-sm">No artifacts yet.</p>
          )}
        </section>
      )}
      <ConfirmDialog
        open={confirmOpen}
        title="Delete Lead"
        message="Are you sure you want to delete this lead? This action cannot be undone."
        onCancel={() => setConfirmOpen(false)}
        onConfirm={onDelete}
      />
    </main>
  );
}
